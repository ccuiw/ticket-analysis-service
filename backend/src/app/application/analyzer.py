"""
工单分析应用服务。

当前为模拟实现，根据输入关键词返回固定分析结果。
后续将替换为完整的 LLM → parse → validate 管道。
"""

from app.models.responses import AnalysisResult
from app.domain.exceptions import AnalysisError

# ---- 临时模拟实现，后续由应用服务和 LLM Client 替换 ----


def _build_mock_result(ticket_text: str, prompt_version: str) -> AnalysisResult:
    """根据输入关键词构建模拟分析结果。"""
    text_lower = ticket_text.lower()

    # 根据关键词决定返回哪类模拟结果
    if "付款" in ticket_text or "付费" in ticket_text:
        return AnalysisResult(
            category="支付问题",
            priority="高",
            summary="用户完成付款后，会员权益尚未生效。",
            tags=["支付", "会员", "权益未生效"],
            order_id=None,
            confidence=0.95,
            need_human_review=False,
            uncertain_fields=[],
        )
    elif "会员" in ticket_text:
        return AnalysisResult(
            category="账号问题",
            priority="中",
            summary="用户反馈会员相关问题，需要进一步确认具体表现。",
            tags=["会员", "账号"],
            order_id=None,
            confidence=0.88,
            need_human_review=False,
            uncertain_fields=["order_id"],
        )
    elif "登录" in ticket_text or "密码" in ticket_text:
        return AnalysisResult(
            category="登录问题",
            priority="高",
            summary="用户无法正常登录系统，可能是密码错误或账号锁定导致。",
            tags=["登录", "密码"],
            order_id=None,
            confidence=0.92,
            need_human_review=False,
            uncertain_fields=["order_id"],
        )
    elif "退款" in ticket_text or "退货" in ticket_text:
        return AnalysisResult(
            category="退款问题",
            priority="高",
            summary="用户申请退款或退货，需要客服介入处理。",
            tags=["退款", "售后"],
            order_id=None,
            confidence=0.90,
            need_human_review=True,
            uncertain_fields=["order_id"],
        )
    else:
        return AnalysisResult(
            category="一般咨询",
            priority="低",
            summary="用户提交了工单，需要进一步确认具体问题类型。",
            tags=["咨询"],
            order_id=None,
            confidence=0.75,
            need_human_review=False,
            uncertain_fields=["category", "order_id"],
        )


# --------------------------------------------------------


def analyze_ticket(ticket_text: str, prompt_version: str) -> AnalysisResult:
    """
    分析工单文本。

    当前为模拟实现。后续版本将：
    1. 通过 prompt loader 加载对应版本的提示词
    2. 通过 LLM provider 调用大模型
    3. 通过 parser 解析原始输出
    4. 通过 structural validation 校验结构
    5. 通过 business validation 校验业务规则
    6. 校验失败时触发 repair 流程
    """
    if not ticket_text or not ticket_text.strip():
        raise AnalysisError("ticket_text 不能为空")
    if prompt_version not in ("v1", "v2"):
        raise AnalysisError(f"不支持的提示词版本：{prompt_version}")

    return _build_mock_result(ticket_text, prompt_version)
