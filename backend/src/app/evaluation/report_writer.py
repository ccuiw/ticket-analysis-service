"""评估报告生成器。"""

import json
import csv
import io
from pathlib import Path
from datetime import datetime, timezone
from app.evaluation.models import (
    PromptVersionReport,
    EvaluationRunMetadata,
)


def write_reports(
    reports: list[PromptVersionReport],
    metadata: EvaluationRunMetadata,
    output_dir: str | Path,
) -> dict[str, Path]:
    """生成 JSON、CSV 和 Markdown 报告。

    Args:
        reports: 每个版本的评估报告。
        metadata: 运行元数据。
        output_dir: 输出目录。

    Returns:
        {"summary": path, "cases": path, "report": path}
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    summary_path = output / "latest_summary.json"
    cases_path = output / "latest_cases.csv"
    report_path = output / "latest_report.md"

    # JSON summary
    summary_data = {
        "metadata": {
            "run_id": metadata.run_id,
            "timestamp": metadata.timestamp,
            "provider": metadata.provider,
            "model": metadata.model,
            "prompt_versions": metadata.prompt_versions,
            "dataset_path": metadata.dataset_path,
            "dataset_hash": metadata.dataset_hash,
            "repair_enabled": metadata.repair_enabled,
            "max_attempts": metadata.max_attempts,
            "git_commit": metadata.git_commit,
            "is_mock": metadata.is_mock,
        },
        "reports": [],
    }
    for r in reports:
        m = r.metrics
        summary_data["reports"].append({
            "prompt_version": r.prompt_version,
            "total_cases": m.total_cases,
            "raw_parse_rate": m.raw_parse_rate,
            "structured_success_rate": m.structured_success_rate,
            "category_accuracy": m.category_accuracy,
            "priority_accuracy": m.priority_accuracy,
            "order_id_accuracy": m.order_id_accuracy,
            "human_review_accuracy": m.human_review_accuracy,
            "tag_recall": m.tag_recall,
            "fabrication_rate": m.fabrication_rate,
            "repair_trigger_rate": m.repair_trigger_rate,
            "average_provider_calls": m.average_provider_calls,
            "end_to_end_success_rate": m.end_to_end_success_rate,
            "errors_by_type": m.errors_by_type,
        })
    summary_path.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV cases
    _write_cases_csv(reports, cases_path)

    # Markdown report
    report_md = _build_markdown_report(reports, metadata)
    report_path.write_text(report_md, encoding="utf-8")

    return {
        "summary": summary_path,
        "cases": cases_path,
        "report": report_path,
    }


def _write_cases_csv(reports: list[PromptVersionReport], path: Path) -> None:
    """将每个案例的评估结果写入 CSV。"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "case_id", "prompt_version", "success", "raw_parse_ok",
        "repair_triggered", "provider_calls", "category_match",
        "priority_match", "order_id_match", "human_review_match",
        "tags_recall", "fabricated", "error_type", "error_detail",
        "duration_seconds",
    ])
    for r in reports:
        for cr in r.case_results:
            writer.writerow([
                cr.case_id, cr.prompt_version, cr.success, cr.raw_parse_ok,
                cr.repair_triggered, cr.provider_calls, cr.category_match,
                cr.priority_match, cr.order_id_match, cr.human_review_match,
                cr.tags_recall, cr.fabricated, cr.error_type or "",
                (cr.error_detail or "")[:200], cr.duration_seconds,
            ])
    path.write_text(output.getvalue(), encoding="utf-8")


def _build_markdown_report(
    reports: list[PromptVersionReport],
    metadata: EvaluationRunMetadata,
) -> str:
    """生成 Markdown 格式的评估报告。"""
    lines = [
        "# 提示词评估报告",
        "",
        "## 运行信息",
        "",
        f"- **运行 ID**: {metadata.run_id}",
        f"- **时间**: {metadata.timestamp}",
        f"- **Provider**: {metadata.provider}",
        f"- **模型**: {metadata.model}",
        f"- **数据集**: {metadata.dataset_path}",
        f"- **数据集哈希**: {metadata.dataset_hash}",
        f"- **修复**: {'开启' if metadata.repair_enabled else '关闭'}",
        f"- **Mock 模式**: {'是（结果不代表提示词真实质量）' if metadata.is_mock else '否'}",
    ]

    if metadata.is_mock:
        lines.extend([
            "",
            "> ⚠️ **Mock 评估结果**：本次评估使用 Mock Provider，结果仅用于验证评估管道本身，",
            "> **不代表提示词的真实质量**。请使用 `--provider openai_compatible` 运行真实评估。",
        ])

    lines.extend(["", "## 指标对比", ""])
    lines.append("| 指标 | V1 | V2 | 差值 |")
    lines.append("| --- | --- | --- | --- |")

    v1_report = next((r for r in reports if r.prompt_version == "v1"), None)
    v2_report = next((r for r in reports if r.prompt_version == "v2"), None)

    metric_rows = [
        ("案例总数", lambda m: str(m.total_cases), False),
        ("JSON 首次解析率", lambda m: f"{m.raw_parse_rate:.1%}", True),
        ("结构化成功率", lambda m: f"{m.structured_success_rate:.1%}", True),
        ("分类准确率", lambda m: f"{m.category_accuracy:.1%}" if m.category_accuracy is not None else "N/A", True),
        ("优先级准确率", lambda m: f"{m.priority_accuracy:.1%}" if m.priority_accuracy is not None else "N/A", True),
        ("订单号准确率", lambda m: f"{m.order_id_accuracy:.1%}" if m.order_id_accuracy is not None else "N/A", True),
        ("人工审核准确率", lambda m: f"{m.human_review_accuracy:.1%}" if m.human_review_accuracy is not None else "N/A", True),
        ("标签召回率", lambda m: f"{m.tag_recall:.1%}", True),
        ("编造率", lambda m: f"{m.fabrication_rate:.1%}", True),
        ("修复触发率", lambda m: f"{m.repair_trigger_rate:.1%}", True),
        ("平均调用次数", lambda m: f"{m.average_provider_calls:.1f}", True),
        ("端到端成功率", lambda m: f"{m.end_to_end_success_rate:.1%}", True),
    ]

    for name, formatter, show_diff in metric_rows:
        v1_str = formatter(v1_report.metrics) if v1_report else "N/A"
        v2_str = formatter(v2_report.metrics) if v2_report else "N/A"
        if show_diff and v1_report and v2_report:
            diff = formatter(v2_report.metrics) + " vs " + formatter(v1_report.metrics)
        else:
            diff = "-"
        lines.append(f"| {name} | {v1_str} | {v2_str} | {diff} |")

    # 失败案例
    lines.extend(["", "## 失败案例", ""])
    for r in reports:
        failed = [cr for cr in r.case_results if not cr.success]
        if failed:
            lines.append(f"### {r.prompt_version}")
            for cr in failed:
                lines.append(f"- **{cr.case_id}**: {cr.error_type} — {cr.error_detail or '无详情'}")

    # 原因分析
    lines.extend(["", "## 原因分析", ""])
    lines.append("基于实际数据，分析两个版本效果差异的原因。")
    if metadata.is_mock:
        lines.append("Mock 模式下不进行原因分析。")

    # 局限
    lines.extend(["", "## 测试局限", ""])
    lines.append("- 20 条数据的覆盖面有限")
    if metadata.is_mock:
        lines.append("- Mock 结果不代表真实模型表现")
    lines.append("- tag 匹配使用简化规则，同义词可能不完全覆盖")

    # 建议
    lines.extend(["", "## 改进建议", ""])
    lines.append("- 使用真实 Provider 运行评估以获得可信结论")
    lines.append("- 增加更多边界案例")
    lines.append("- 考虑多次重复运行以减少采样偏差")

    return "\n".join(lines) + "\n"
