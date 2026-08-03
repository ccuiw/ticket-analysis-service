"""评估数据模型。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TestCase:
    """单条测试用例。"""
    id: str
    input: str
    expected: dict
    case_type: str
    notes: str = ""


@dataclass
class EvaluationCaseResult:
    """单条案例的评估结果。"""
    case_id: str
    prompt_version: str
    success: bool
    raw_parse_ok: bool = False
    repair_triggered: bool = False
    provider_calls: int = 0
    final_result: dict | None = None
    category_match: bool | None = None
    priority_match: bool | None = None
    order_id_match: bool | None = None
    human_review_match: bool | None = None
    tags_recall: float | None = None
    fabricated: bool = False
    fabricated_fields: list[str] = field(default_factory=list)
    error_type: str | None = None
    error_detail: str | None = None
    duration_seconds: float = 0.0


@dataclass
class EvaluationMetrics:
    """单个 Prompt 版本的汇总指标。"""
    total_cases: int = 0
    raw_parse_success: int = 0
    final_structured_success: int = 0
    category_correct: int = 0
    category_evaluable: int = 0
    priority_correct: int = 0
    priority_evaluable: int = 0
    order_id_correct: int = 0
    order_id_evaluable: int = 0
    human_review_correct: int = 0
    human_review_evaluable: int = 0
    tags_total_expected: int = 0
    tags_total_recalled: int = 0
    cases_fabricated: int = 0
    cases_repair_triggered: int = 0
    total_provider_calls: int = 0
    total_duration_seconds: float = 0.0
    total_tokens_used: int = 0
    end_to_end_success: int = 0
    errors_by_type: dict = field(default_factory=dict)

    @property
    def raw_parse_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.raw_parse_success / self.total_cases

    @property
    def structured_success_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.final_structured_success / self.total_cases

    @property
    def category_accuracy(self) -> float | None:
        if self.category_evaluable == 0:
            return None
        return self.category_correct / self.category_evaluable

    @property
    def priority_accuracy(self) -> float | None:
        if self.priority_evaluable == 0:
            return None
        return self.priority_correct / self.priority_evaluable

    @property
    def order_id_accuracy(self) -> float | None:
        if self.order_id_evaluable == 0:
            return None
        return self.order_id_correct / self.order_id_evaluable

    @property
    def human_review_accuracy(self) -> float | None:
        if self.human_review_evaluable == 0:
            return None
        return self.human_review_correct / self.human_review_evaluable

    @property
    def tag_recall(self) -> float:
        if self.tags_total_expected == 0:
            return 1.0
        return self.tags_total_recalled / self.tags_total_expected

    @property
    def fabrication_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.cases_fabricated / self.total_cases

    @property
    def repair_trigger_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.cases_repair_triggered / self.total_cases

    @property
    def average_provider_calls(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.total_provider_calls / self.total_cases

    @property
    def end_to_end_success_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.end_to_end_success / self.total_cases

    @property
    def average_duration_seconds(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.total_duration_seconds / self.total_cases

    @property
    def average_tokens_per_case(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.total_tokens_used / self.total_cases


@dataclass
class PromptVersionReport:
    """单个 Prompt 版本的完整评估报告。"""
    prompt_version: str
    metrics: EvaluationMetrics
    case_results: list[EvaluationCaseResult] = field(default_factory=list)


@dataclass
class EvaluationRunMetadata:
    """评估运行的元数据。"""
    run_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provider: str = "mock"
    model: str = "mock"
    prompt_versions: list[str] = field(default_factory=list)
    dataset_path: str = ""
    dataset_hash: str = ""
    repair_enabled: bool = True
    max_attempts: int = 2
    git_commit: str = ""
    is_mock: bool = True
