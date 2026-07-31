"""
工单分析应用服务。

编排完整的 LLM 分析流程：
1. 加载提示词并构造消息；
2. 调用 LLM Provider；
3. 解析原始输出；
4. 校验结构；
5. 执行业务规则校验。

不包含供应商特定的 HTTP 逻辑。
"""

import logging
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage
from app.models.responses import AnalysisResult
from app.prompts.builder import build_messages
from app.parsing.parser import parse_raw_output
from app.validation.structural import validate_structure
from app.validation.business import validate_business_rules
from app.domain.exceptions import AnalysisError

logger = logging.getLogger(__name__)


class TicketAnalysisService:
    """工单分析服务。

    协调 Prompt → LLM → Parse → Validate 全流程。
    通过构造函数注入 Provider，支持 Mock 和真实 LLM 的无缝切换。
    """

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider

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
            PromptNotFoundError: 提示词文件不存在。
            PromptRenderError: 提示词构造失败。
            LLMError 子类: LLM 调用失败。
            OutputParseError: JSON 解析失败。
            OutputValidationError: 结构校验失败。
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

        # 2. 调用 LLM
        response = await self._provider.analyze(messages)
        logger.info(
            "LLM 返回，model=%s，长度=%d",
            response.model,
            len(response.content),
        )

        # 3. 解析 JSON
        data = parse_raw_output(response.content)

        # 4. 结构校验
        result = validate_structure(data)

        # 5. 业务校验
        result = validate_business_rules(result)

        logger.info(
            "分析完成，category=%s，priority=%s，confidence=%.2f",
            result.category,
            result.priority,
            result.confidence,
        )

        return result
