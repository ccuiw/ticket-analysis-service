"""
业务规则校验。

对已通过结构化校验的分析结果进行业务层面的检查。
当前为透传桩，后续将实现：
- priority 与 urgency 一致性检查
- category 与 tags 相关性检查
- 必填字段业务合理性检查
"""

from app.models.responses import AnalysisResult


def validate_business_rules(result: AnalysisResult) -> AnalysisResult:
    """对分析结果执行业务规则校验。

    当前版本为透传桩，始终原样返回。
    """
    return result
