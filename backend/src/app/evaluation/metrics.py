"""评估指标计算。"""

from app.evaluation.models import (
    TestCase,
    EvaluationCaseResult,
    EvaluationMetrics,
)


def evaluate_case(
    case: TestCase,
    prompt_version: str,
    result: dict | None,
    raw_parse_ok: bool,
    repair_triggered: bool,
    provider_calls: int,
    error_type: str | None,
    error_detail: str | None,
    duration_seconds: float,
) -> EvaluationCaseResult:
    """对单条案例的评估结果进行逐字段判定。

    Args:
        case: 测试用例。
        prompt_version: 使用的提示词版本。
        result: 模型返回的结构化结果（可能为 None）。
        raw_parse_ok: 首次 JSON 解析是否成功。
        repair_triggered: 是否触发了输出修复。
        provider_calls: Provider 调用总次数。
        error_type: 错误类型（成功时为 None）。
        error_detail: 错误详情。
        duration_seconds: 执行耗时。

    Returns:
        EvaluationCaseResult。
    """
    cr = EvaluationCaseResult(
        case_id=case.id,
        prompt_version=prompt_version,
        success=result is not None,
        raw_parse_ok=raw_parse_ok,
        repair_triggered=repair_triggered,
        provider_calls=provider_calls,
        final_result=result,
        error_type=error_type,
        error_detail=error_detail,
        duration_seconds=duration_seconds,
    )

    if result is None:
        return cr

    expected = case.expected

    # Category accuracy
    if "category" in expected:
        cr.category_match = result.get("category") == expected["category"]

    # Priority accuracy
    if "priority" in expected:
        cr.priority_match = result.get("priority") == expected["priority"]

    # Order ID accuracy
    if "order_id" in expected:
        expected_oid = expected["order_id"]
        actual_oid = result.get("order_id")
        if expected_oid is None:
            cr.order_id_match = actual_oid is None
        else:
            cr.order_id_match = actual_oid == expected_oid

    # Human review accuracy
    if "need_human_review" in expected:
        cr.human_review_match = (
            result.get("need_human_review") == expected["need_human_review"]
        )

    # Tag recall
    must_tags = expected.get("must_include_tags", [])
    if must_tags:
        actual_tags = [t.lower() for t in result.get("tags", [])]
        recalled = sum(
            1 for t in must_tags
            if any(t.lower() in at or at in t.lower() for at in actual_tags)
        )
        cr.tags_recall = recalled / len(must_tags)
    else:
        cr.tags_recall = 1.0

    # Fabrication detection
    forbidden = expected.get("forbidden_fabricated_fields", [])
    for field in forbidden:
        if field == "order_id" and result.get("order_id") is not None:
            cr.fabricated = True
            cr.fabricated_fields.append("order_id")

    return cr


def compute_metrics(
    case_results: list[EvaluationCaseResult],
    cases: list[TestCase],
) -> EvaluationMetrics:
    """从案例结果列表计算汇总指标。

    Args:
        case_results: 所有案例的评估结果。
        cases: 原始测试用例列表。

    Returns:
        EvaluationMetrics。
    """
    m = EvaluationMetrics()
    m.total_cases = len(cases)

    case_map = {c.id: c for c in cases}

    for cr in case_results:
        case = case_map.get(cr.case_id)
        if case is None:
            continue

        if cr.raw_parse_ok:
            m.raw_parse_success += 1
        if cr.final_result is not None:
            m.final_structured_success += 1
        if cr.repair_triggered:
            m.cases_repair_triggered += 1
        m.total_provider_calls += cr.provider_calls

        if cr.fabricated:
            m.cases_fabricated += 1

        # Category
        if "category" in case.expected:
            m.category_evaluable += 1
            if cr.category_match:
                m.category_correct += 1

        # Priority
        if "priority" in case.expected:
            m.priority_evaluable += 1
            if cr.priority_match:
                m.priority_correct += 1

        # Order ID
        if "order_id" in case.expected:
            m.order_id_evaluable += 1
            if cr.order_id_match:
                m.order_id_correct += 1

        # Human review
        if "need_human_review" in case.expected:
            m.human_review_evaluable += 1
            if cr.human_review_match:
                m.human_review_correct += 1

        # Tags
        must_tags = case.expected.get("must_include_tags", [])
        m.tags_total_expected += len(must_tags)
        if cr.tags_recall is not None:
            m.tags_total_recalled += int(cr.tags_recall * len(must_tags))

        # Error type
        if cr.error_type:
            m.errors_by_type[cr.error_type] = m.errors_by_type.get(cr.error_type, 0) + 1

        # End-to-end: structured success + category correct + no fabrication + human review correct
        if (
            cr.final_result is not None
            and (cr.category_match is None or cr.category_match)
            and (cr.order_id_match is None or cr.order_id_match)
            and not cr.fabricated
            and (cr.human_review_match is None or cr.human_review_match)
        ):
            m.end_to_end_success += 1

    return m
