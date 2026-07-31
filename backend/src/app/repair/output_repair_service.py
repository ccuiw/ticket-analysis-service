"""
输出修复服务。

当 LLM 返回的 JSON 无法解析或校验失败时，
使用专用修复提示词请求模型重新生成合法 JSON。
最多修复一次。
"""

import json
import logging
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.prompts.loader import load_prompt
from app.domain.exceptions import (
    OutputRepairError,
    OutputRepairExhaustedError,
)

logger = logging.getLogger(__name__)


class OutputRepairService:
    """输出修复服务。

    加载 json_repair.txt 提示词，构造修复请求，
    调用 Provider 获取修复后的输出。

    注意：本服务不执行 JSON 解析或校验——这些
    由调用方（TicketAnalysisService）负责。
    """

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider
        self._repair_prompt: str | None = None

    def _load_repair_prompt(self) -> str:
        """延迟加载修复提示词。"""
        if self._repair_prompt is None:
            self._repair_prompt = load_prompt("json_repair")
        return self._repair_prompt

    async def repair(
        self,
        original_ticket: str,
        original_output: str,
        error_detail: str,
    ) -> str:
        """尝试修复模型输出。

        Args:
            original_ticket: 原始工单文本。
            original_output: 模型返回的原始输出（可能包含非法 JSON）。
            error_detail: 解析或校验错误的详细信息。

        Returns:
            修复后的原始文本（应该是合法 JSON）。

        Raises:
            OutputRepairExhaustedError: 修复失败。
        """
        repair_prompt = self._load_repair_prompt()

        # 构造修复请求消息
        system_content = repair_prompt
        user_content = (
            f"<original_ticket>\n{original_ticket}\n</original_ticket>\n\n"
            f"<original_output>\n{original_output}\n</original_output>\n\n"
            f"<error>\n{error_detail}\n</error>"
        )

        messages = [
            LLMMessage(role="system", content=system_content),
            LLMMessage(role="user", content=user_content),
        ]

        logger.info("开始输出修复，原始输出长度=%d，错误=%s", len(original_output), error_detail[:100])

        try:
            response: LLMResponse = await self._provider.analyze(messages)
        except Exception as exc:
            raise OutputRepairExhaustedError(
                f"输出修复调用失败：{exc}"
            ) from exc

        if not response.content or not response.content.strip():
            raise OutputRepairExhaustedError("修复模型返回了空输出")

        logger.info("输出修复完成，修复后长度=%d", len(response.content))
        return response.content
