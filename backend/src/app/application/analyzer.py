"""
已废弃的 analyze_ticket 函数。

此模块保留仅用于向后兼容。新代码应使用
app.application.ticket_analysis_service.TicketAnalysisService。

Mock 逻辑已迁移至 app.llm.mock_provider.MockLLMProvider。
"""

import warnings
from app.models.responses import AnalysisResult
from app.llm.mock_provider import MockLLMProvider


def analyze_ticket(ticket_text: str, prompt_version: str) -> AnalysisResult:
    """已废弃。请使用 TicketAnalysisService。"""
    warnings.warn(
        "analyze_ticket 已废弃，请使用 TicketAnalysisService",
        DeprecationWarning,
        stacklevel=2,
    )
    # 同步包装器：仅用于测试兼容
    import asyncio
    from app.prompts.builder import build_messages
    from app.parsing.parser import parse_raw_output
    from app.validation.structural import validate_structure

    provider = MockLLMProvider()

    async def _run():
        messages = build_messages(ticket_text, prompt_version)
        response = await provider.analyze(messages)
        data = parse_raw_output(response.content)
        return validate_structure(data)

    return asyncio.run(_run())
