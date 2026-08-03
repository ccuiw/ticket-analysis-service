"""评估报告生成器。"""

import json
import csv
import io
from pathlib import Path
from app.evaluation.models import (
    PromptVersionReport,
    EvaluationRunMetadata,
    EvaluationMetrics,
)


def write_reports(
    reports: list[PromptVersionReport],
    metadata: EvaluationRunMetadata,
    output_dir: str | Path,
) -> dict[str, Path]:
    """生成 JSON、CSV 和 Markdown 报告。"""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    summary_path = output / "latest_summary.json"
    cases_path = output / "latest_cases.csv"
    report_path = output / "latest_report.md"

    # JSON summary
    _write_json_summary(reports, metadata, summary_path)

    # CSV cases
    _write_cases_csv(reports, cases_path)

    # Markdown report
    report_md = _build_markdown_report(reports, metadata)
    report_path.write_text(report_md, encoding="utf-8")

    return {"summary": summary_path, "cases": cases_path, "report": report_path}


def _write_json_summary(
    reports: list[PromptVersionReport],
    metadata: EvaluationRunMetadata,
    path: Path,
) -> None:
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
            "average_duration_seconds": m.average_duration_seconds,
            "average_tokens_per_case": m.average_tokens_per_case,
            "total_tokens_used": m.total_tokens_used,
            "end_to_end_success_rate": m.end_to_end_success_rate,
            "errors_by_type": m.errors_by_type,
        })
    path.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_cases_csv(reports: list[PromptVersionReport], path: Path) -> None:
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
    lines: list[str] = []
    lines.extend(_section_experiment_overview(metadata))
    lines.extend(_section_prompt_comparison(reports))
    lines.extend(_section_failure_analysis(reports))
    lines.extend(_section_prompt_difference_analysis(reports, metadata))
    lines.extend(_section_limitations(metadata))
    lines.extend(_section_recommendations(metadata))
    return "\n".join(lines) + "\n"


# ── Section 1: Experiment Overview ──

def _section_experiment_overview(metadata: EvaluationRunMetadata) -> list[str]:
    lines = [
        "# 提示词评估报告",
        "",
        "## 1. Experiment Overview",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Dataset size | {len(metadata.prompt_versions)} versions |",
        f"| Prompt versions | {', '.join(metadata.prompt_versions)} |",
        f"| Provider | {metadata.provider} |",
        f"| Model | {metadata.model} |",
        f"| Evaluation time | {metadata.timestamp} |",
        f"| Dataset hash | {metadata.dataset_hash} |",
        f"| Repair enabled | {metadata.repair_enabled} |",
        f"| Max attempts | {metadata.max_attempts} |",
        f"| Run ID | {metadata.run_id} |",
    ]
    if metadata.is_mock:
        lines.extend([
            "",
            "> ⚠️ **Mock Evaluation Results**",
            "> ",
            "> This evaluation used the Mock Provider. Results validate the evaluation",
            "> pipeline but **do NOT represent real prompt quality**.",
            "> ",
            "> V1 and V2 produce identical results with Mock because the provider uses",
            "> keyword matching, not prompt semantics.",
            "> ",
            "> Run with `--provider openai_compatible` to get real quality data.",
        ])
    return lines


# ── Section 2: Prompt Comparison ──

def _section_prompt_comparison(reports: list[PromptVersionReport]) -> list[str]:
    lines = [
        "",
        "## 2. Prompt Comparison",
        "",
        "| Metric | V1 | V2 |",
        "| --- | --- | --- |",
    ]

    v1 = _find_report(reports, "v1")
    v2 = _find_report(reports, "v2")

    rows = [
        ("JSON Parse Rate", lambda m: f"{m.raw_parse_rate:.1%}"),
        ("Structured Success Rate", lambda m: f"{m.structured_success_rate:.1%}"),
        ("Category Accuracy", lambda m: f"{m.category_accuracy:.1%}" if m.category_accuracy is not None else "N/A"),
        ("Priority Accuracy", lambda m: f"{m.priority_accuracy:.1%}" if m.priority_accuracy is not None else "N/A"),
        ("Order ID Accuracy", lambda m: f"{m.order_id_accuracy:.1%}" if m.order_id_accuracy is not None else "N/A"),
        ("Human Review Accuracy", lambda m: f"{m.human_review_accuracy:.1%}" if m.human_review_accuracy is not None else "N/A"),
        ("Tag Recall", lambda m: f"{m.tag_recall:.1%}"),
        ("Fabrication Rate", lambda m: f"{m.fabrication_rate:.1%}"),
        ("Repair Trigger Rate", lambda m: f"{m.repair_trigger_rate:.1%}"),
        ("Avg Provider Calls", lambda m: f"{m.average_provider_calls:.1f}"),
        ("Avg Duration (s)", lambda m: f"{m.average_duration_seconds:.2f}"),
        ("End-to-End Success Rate", lambda m: f"{m.end_to_end_success_rate:.1%}"),
    ]

    for name, fmt in rows:
        v1_val = fmt(v1.metrics) if v1 else "N/A"
        v2_val = fmt(v2.metrics) if v2 else "N/A"
        lines.append(f"| {name} | {v1_val} | {v2_val} |")

    return lines


# ── Section 3: Failure Analysis ──

def _section_failure_analysis(reports: list[PromptVersionReport]) -> list[str]:
    lines = [
        "",
        "## 3. Failure Analysis",
        "",
    ]

    for r in reports:
        lines.append(f"### {r.prompt_version} Failures")
        lines.append("")

        # JSON parse failures
        parse_fails = [cr for cr in r.case_results if not cr.raw_parse_ok]
        if parse_fails:
            lines.append(f"**JSON Parse Failures ({len(parse_fails)}):**")
            for cr in parse_fails:
                lines.append(f"- {cr.case_id}: {cr.error_detail or 'unknown'}")
        else:
            lines.append("**JSON Parse Failures:** None")

        # Category errors
        cat_errors = [cr for cr in r.case_results if cr.final_result and cr.category_match is False]
        if cat_errors:
            lines.append(f"\n**Category Errors ({len(cat_errors)}):**")
            for cr in cat_errors:
                expected = cr.final_result.get("category") if cr.final_result else "?"
                lines.append(f"- {cr.case_id}: got `{expected}`")

        # Missing fields
        missing = [cr for cr in r.case_results if cr.final_result and cr.order_id_match is False]
        if missing:
            lines.append(f"\n**Order ID Errors ({len(missing)}):**")
            for cr in missing:
                lines.append(f"- {cr.case_id}")

        # Fabrication
        fabricated = [cr for cr in r.case_results if cr.fabricated]
        if fabricated:
            lines.append(f"\n**Fabrication Cases ({len(fabricated)}):**")
            for cr in fabricated:
                lines.append(f"- {cr.case_id}: fabricated fields {cr.fabricated_fields}")
        else:
            lines.append("\n**Fabrication Cases:** None")

        # Repair still failed
        repair_fails = [cr for cr in r.case_results if cr.repair_triggered and not cr.success]
        if repair_fails:
            lines.append(f"\n**Repair Still Failed ({len(repair_fails)}):**")
            for cr in repair_fails:
                lines.append(f"- {cr.case_id}")
        else:
            lines.append("\n**Repair Still Failed:** None")

        # Error type summary
        if r.metrics.errors_by_type:
            lines.append(f"\n**Error Type Distribution:**")
            for etype, count in sorted(r.metrics.errors_by_type.items()):
                lines.append(f"- {etype}: {count}")

        lines.append("")

    return lines


# ── Section 4: Prompt Difference Analysis ──

def _section_prompt_difference_analysis(
    reports: list[PromptVersionReport],
    metadata: EvaluationRunMetadata,
) -> list[str]:
    lines = [
        "## 4. Prompt Difference Analysis",
        "",
        "### V1: Instruction-driven generation (Zero-shot)",
        "",
        "V1 relies solely on system instructions describing the task, field definitions,",
        "rules, and output format. The model must infer the expected behavior from the",
        "instruction text alone, with no worked examples.",
        "",
        "### V2: Example-guided generation (Few-shot)",
        "",
        "V2 extends V1 with 3 curated examples covering:",
        "- Clear classification with order ID present",
        "- Missing order ID (uncertain_fields handling)",
        "- Insufficient information (low confidence, human review required)",
        "",
        "### Observed Differences",
        "",
    ]

    if metadata.is_mock:
        lines.extend([
            "**Mock mode:** V1 and V2 produce identical results because the Mock Provider",
            "uses keyword matching, which ignores the prompt version entirely.",
            "",
            "Run with `--provider openai_compatible` to observe real differences.",
        ])
    else:
        v1 = _find_report(reports, "v1")
        v2 = _find_report(reports, "v2")
        if v1 and v2:
            # Compare key metrics
            lines.append("| Area | V1 | V2 | Analysis |")
            lines.append("| --- | --- | --- | --- |")
            lines.append(_diff_row("Category Accuracy", v1.metrics.category_accuracy, v2.metrics.category_accuracy))
            lines.append(_diff_row("JSON Parse Rate", v1.metrics.raw_parse_rate, v2.metrics.raw_parse_rate))
            lines.append(_diff_row("Fabrication Rate", v1.metrics.fabrication_rate, v2.metrics.fabrication_rate))
            lines.append("")
            lines.extend([
                "> **Note:** Analysis is based on observed data. Where sample size is small (20 cases),",
                "> differences may not be statistically significant. Do not over-generalize.",
            ])

    return lines


def _diff_row(name: str, v1_val: float | None, v2_val: float | None) -> str:
    v1_s = f"{v1_val:.1%}" if v1_val is not None else "N/A"
    v2_s = f"{v2_val:.1%}" if v2_val is not None else "N/A"
    if v1_val is not None and v2_val is not None:
        if v2_val > v1_val:
            analysis = "V2 better"
        elif v2_val < v1_val:
            analysis = "V1 better"
        else:
            analysis = "Equal"
    else:
        analysis = "N/A"
    return f"| {name} | {v1_s} | {v2_s} | {analysis} |"


# ── Section 5: Limitations ──

def _section_limitations(metadata: EvaluationRunMetadata) -> list[str]:
    lines = [
        "## 5. Limitations",
        "",
        "- 20 test cases provide limited coverage of real-world ticket diversity",
        "- Tag recall uses simplified substring matching, may miss synonyms",
        "- Category accuracy depends on subjective expected values",
        "- Single run per case; results may vary between runs",
    ]
    if metadata.is_mock:
        lines.append("- Mock results do not represent real prompt quality")
    return lines


# ── Section 6: Recommendations ──

def _section_recommendations(metadata: EvaluationRunMetadata) -> list[str]:
    lines = [
        "## 6. Recommendations",
        "",
    ]
    if metadata.is_mock:
        lines.extend([
            "- Run with `--provider openai_compatible` to obtain real prompt quality data",
            "- Compare results across multiple models if available",
        ])
    else:
        lines.extend([
            "- Consider running multiple repetitions to reduce sampling variance",
            "- Add more boundary and edge cases to the test dataset",
            "- If V2 shows better category accuracy, few-shot examples are likely helping disambiguation",
            "- If V1 and V2 show similar performance, the instruction alone may be sufficient",
        ])
    lines.extend([
        "- Expand test dataset to 50+ cases for statistical significance",
        "- Add multi-label evaluation for cases with multiple valid categories",
    ])
    return lines


def _find_report(
    reports: list[PromptVersionReport], version: str
) -> PromptVersionReport | None:
    return next((r for r in reports if r.prompt_version == version), None)
