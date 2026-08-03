"""评估入口。

用法：
    # Mock 模式
    python -m app.evaluation.run --provider mock --versions v1 v2

    # 真实 Provider 模式
    python -m app.evaluation.run --provider openai_compatible --versions v1 v2 --dataset ../data/test_cases.jsonl
"""

import os
import sys
import uuid
import asyncio
import logging
from pathlib import Path
from app.evaluation.cli import parse_args
from app.evaluation.dataset import load_dataset, compute_dataset_hash
from app.evaluation.runner import run_version
from app.evaluation.metrics import compute_metrics
from app.evaluation.models import PromptVersionReport, EvaluationRunMetadata
from app.evaluation.report_writer import write_reports

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    is_mock = args.provider == "mock"
    repair_enabled = not args.disable_repair

    # 校验数据集
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        # 相对于当前工作目录
        dataset_path = dataset_path.resolve()

    logger.info("加载数据集：%s", dataset_path)
    cases = load_dataset(dataset_path)
    dataset_hash = compute_dataset_hash(dataset_path)
    logger.info("已加载 %d 条测试案例（哈希：%s）", len(cases), dataset_hash)

    # 创建 Provider
    if is_mock:
        from app.llm.mock_provider import MockLLMProvider
        provider = MockLLMProvider()
        model_name = "mock"
    else:
        from app.llm.provider_factory import create_provider
        provider = create_provider()
        model_name = provider.model_name

    # 输出运行信息
    logger.info("Provider: %s", args.provider)
    logger.info("模型: %s", model_name)
    logger.info("案例数: %d", len(cases))
    logger.info("版本数: %d (%s)", len(args.versions), ", ".join(args.versions))
    max_calls_per_case = 2 + (1 if repair_enabled else 0)  # network retries + repair
    total_max_calls = len(cases) * len(args.versions) * max_calls_per_case
    logger.info("每案例最大调用次数: %d", max_calls_per_case)
    logger.info("预计最大总调用次数: %d", total_max_calls)

    if not is_mock:
        logger.warning("⚠️  即将执行真实 LLM 调用，将消耗 API 额度！")
        logger.info("按 Ctrl+C 取消...")

    # 运行评估
    async def _run():
        reports = []
        for version in args.versions:
            logger.info("开始评估 Prompt %s...", version)
            case_results = await run_version(
                cases=cases,
                prompt_version=version,
                provider=provider,
                repair_enabled=repair_enabled,
            )
            metrics = compute_metrics(case_results, cases)
            # Aggregate duration and provider calls
            metrics.total_duration_seconds = sum(
                cr.duration_seconds for cr in case_results
            )
            metrics.total_provider_calls = sum(
                cr.provider_calls for cr in case_results
            )
            report = PromptVersionReport(
                prompt_version=version,
                metrics=metrics,
                case_results=case_results,
            )
            reports.append(report)
            logger.info(
                "Prompt %s: structured=%.1f e2e=%.1f",
                version,
                metrics.structured_success_rate * 100,
                metrics.end_to_end_success_rate * 100,
            )
        return reports

    reports = asyncio.run(_run())

    # 生成报告
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = output_dir.resolve()

    metadata = EvaluationRunMetadata(
        run_id=uuid.uuid4().hex[:12],
        provider=args.provider,
        model=model_name,
        prompt_versions=args.versions,
        dataset_path=str(dataset_path),
        dataset_hash=dataset_hash,
        repair_enabled=repair_enabled,
        is_mock=is_mock,
    )
    paths = write_reports(reports, metadata, output_dir)
    logger.info("报告已生成：")
    for name, path in paths.items():
        logger.info("  %s: %s", name, path)


if __name__ == "__main__":
    main()
