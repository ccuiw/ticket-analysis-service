"""评估运行器——对单个 Prompt 版本执行全部案例。"""

import time
import logging
from app.llm.base import BaseLLMProvider
from app.application.ticket_analysis_service import TicketAnalysisService
from app.repair.retry_policy import RetryPolicy
from app.repair.output_repair_service import OutputRepairService
from app.evaluation.models import TestCase, EvaluationCaseResult
from app.evaluation.metrics import evaluate_case
from app.domain.exceptions import DomainError

logger = logging.getLogger(__name__)


async def run_version(
    cases: list[TestCase],
    prompt_version: str,
    provider: BaseLLMProvider,
    repair_enabled: bool = True,
) -> list[EvaluationCaseResult]:
    """对一个 Prompt 版本运行全部测试案例。

    Args:
        cases: 测试案例列表。
        prompt_version: 提示词版本。
        provider: LLM Provider 实例。
        repair_enabled: 是否启用输出修复。

    Returns:
        EvaluationCaseResult 列表（与 cases 同顺序）。
    """
    retry_policy = RetryPolicy(max_attempts=2, base_delay_seconds=0, backoff_multiplier=0)
    repair_service = OutputRepairService(provider) if repair_enabled else None

    service = TicketAnalysisService(
        provider=provider,
        retry_policy=retry_policy,
        repair_service=repair_service,
        repair_enabled=repair_enabled,
    )

    results: list[EvaluationCaseResult] = []

    for case in cases:
        logger.info("Case %s [%s]", case.id, prompt_version)
        start = time.perf_counter()

        result_data: dict | None = None
        raw_parse_ok = False
        repair_triggered = False
        provider_calls = 0
        error_type: str | None = None
        error_detail: str | None = None

        try:
            # 使用 TicketAnalysisService 执行分析
            analysis = await service.analyze(case.input, prompt_version)
            result_data = analysis.model_dump()
            raw_parse_ok = True
            # 注意：Mock provider 的内部调用次数无法直接获取
            # 使用 1 作为首次调用计数的默认值
            provider_calls = 1
        except DomainError as exc:
            error_type = type(exc).__name__
            error_detail = str(exc)[:500]
        except Exception as exc:
            error_type = type(exc).__name__
            error_detail = str(exc)[:500]

        duration = time.perf_counter() - start

        cr = evaluate_case(
            case=case,
            prompt_version=prompt_version,
            result=result_data,
            raw_parse_ok=raw_parse_ok,
            repair_triggered=repair_triggered,
            provider_calls=provider_calls,
            error_type=error_type,
            error_detail=error_detail,
            duration_seconds=duration,
        )
        results.append(cr)

        status = "OK" if cr.success else f"FAIL ({error_type})"
        logger.info("Case %s [%s]: %s (%.2fs)", case.id, prompt_version, status, duration)

    return results
