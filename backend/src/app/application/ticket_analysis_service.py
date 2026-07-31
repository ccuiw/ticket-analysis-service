"""
工单分析应用服务。

编排完整的 LLM 分析流程：
1. 加载提示词并构造消息；
2. 调用 LLM Provider（含网络重试）；
3. 解析原始输出；
4. 校验结构；
5. 输出格式异常时尝试单次修复；
6. 执行业务规则校验。

不包含供应商特定的 HTTP 逻辑。
"""

import logging
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.models.responses import AnalysisResult
from app.prompts.builder import build_messages
from app.parsing.parser import parse_raw_output
from app.validation.structural import validate_structure
from app.validation.business import validate_business_rules
from app.repair.retry_policy import RetryPolicy
from app.repair.output_repair_service import OutputRepairService
from app.domain.exceptions import (
    AnalysisError,
    OutputParseError,
    OutputValidationError,
    OutputRepairExhaustedError,
)

logger = logging.getLogger(__name__)


class TicketAnalysisService:
    """工单分析服务。

    协调 Prompt → LLM（含重试）→ Parse → Validate（含修复）全流程。
    通过构造函数注入 Provider、RetryPolicy 和 OutputRepairService。
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        retry_policy: RetryPolicy | None = None,
        repair_service: OutputRepairService | None = None,
        repair_enabled: bool = True,
    ) -> None:
        self._provider = provider
        self._retry_policy = retry_policy or RetryPolicy()
        self._repair_service = repair_service
        self._repair_enabled = repair_enabled

    @property
    def provider_name(self) -> str:
        return self._provider.model_name

    async def analyze(
        self, ticket_text: str, prompt_version: str
    ) -> AnalysisResult:
        """分析工单文本。

        Args:
            ticket_text: 工单文本。
            prompt_version: 提示词版本（"v1" 或 "v2"）。

        Returns:
            校验通过的 AnalysisResult。

        Raises:
            AnalysisError: 输入无效。
            LLMError 子类: LLM 调用失败（含重试耗尽）。
            OutputParseError: JSON 解析失败且修复未启用/失败。
            OutputValidationError: 结构校验失败且修复未启用/失败。
            OutputRepairExhaustedError: 修复后仍失败。
        """
        if not ticket_text or not ticket_text.strip():
            raise AnalysisError("ticket_text 不能为空")

        # 1. 构造消息
        messages = build_messages(ticket_text, prompt_version)
        logger.info(
            "开始分析，provider=%s，prompt_version=%s，文本长度=%d",
            self._provider.model_name,
            prompt_version,
            len(ticket_text),
        )

        # 2. 调用 LLM（含网络重试）
        raw_output = await self._call_llm_with_retry(
            messages, context=f"analysis/{prompt_version}"
        )

        # 3-4. 解析 + 校验（含输出修复）
        result = await self._parse_and_validate(
            raw_output, ticket_text
        )

        # 5. 业务校验
        result = validate_business_rules(result)

        logger.info(
            "分析完成，category=%s，priority=%s，confidence=%.2f",
            result.category,
            result.priority,
            result.confidence,
        )

        return result

    async def _call_llm_with_retry(
        self, messages: list[LLMMessage], context: str
    ) -> str:
        """调用 LLM，在可重试错误时自动重试。"""
        async def _call() -> str:
            response: LLMResponse = await self._provider.analyze(messages)
            logger.debug(
                "%s 返回，model=%s，长度=%d",
                context,
                response.model,
                len(response.content),
            )
            return response.content

        return await self._retry_policy.execute_with_retry(
            _call, operation_name=f"LLM call ({context})"
        )

    async def _parse_and_validate(
        self, raw_output: str, ticket_text: str
    ) -> AnalysisResult:
        """解析原始输出并校验，失败时尝试修复（最多一次）。

        注意：need_human_review=true 或 category 信息不足时，
        不作为错误触发修复——这些是正常的业务结果。
        """
        # 首次尝试
        parse_error = None
        validation_error = None

        try:
            data = parse_raw_output(raw_output)
        except OutputParseError as exc:
            parse_error = exc
            data = None

        if data is not None:
            try:
                return validate_structure(data)
            except (OutputValidationError, Exception) as exc:
                validation_error = exc

        # 如果修复未启用，直接抛出
        if not self._repair_enabled or self._repair_service is None:
            if parse_error:
                raise parse_error
            if validation_error:
                raise validation_error
            raise AnalysisError("分析结果解析失败")

        # 构造错误描述
        error_detail = ""
        if parse_error:
            error_detail = f"JSON 解析失败：{parse_error}"
        elif validation_error:
            error_detail = f"结构校验失败：{validation_error}"

        logger.warning("输出异常，尝试修复：%s", error_detail[:100])

        # 单次修复
        try:
            repaired_raw = await self._repair_service.repair(
                original_ticket=ticket_text,
                original_output=raw_output,
                error_detail=error_detail,
            )
        except OutputRepairExhaustedError:
            # 修复服务本身失败
            if parse_error:
                raise parse_error
            raise OutputRepairExhaustedError(
                f"输出修复失败：{error_detail}"
            )

        # 修复后重新解析
        try:
            repaired_data = parse_raw_output(repaired_raw)
        except OutputParseError as exc:
            raise OutputRepairExhaustedError(
                f"修复后仍无法解析 JSON：{exc}"
            ) from exc

        # 修复后重新校验
        try:
            return validate_structure(repaired_data)
        except (OutputValidationError, Exception) as exc:
            raise OutputRepairExhaustedError(
                f"修复后结构校验仍失败：{exc}"
            ) from exc
