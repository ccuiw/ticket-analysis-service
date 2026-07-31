"""
Mock LLM Provider。

始终返回符合 AnalysisResult 结构的 JSON，不发起任何网络请求。
根据输入关键词切换返回不同模拟结果，用于开发和测试。
"""

import json
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """基于关键词匹配的模拟 LLM 供应商。

    不调用任何外部服务，始终返回有效 JSON。
    """

    def __init__(self) -> None:
        self._model = "mock"

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze(self, messages: list[LLMMessage]) -> LLMResponse:
        # 从 user 消息中提取工单文本
        ticket_text = ""
        for msg in messages:
            if msg.role == "user":
                ticket_text = msg.content
                break

        result = self._build_result(ticket_text)
        return LLMResponse(
            content=json.dumps(result, ensure_ascii=False),
            model=self._model,
        )

    def _build_result(self, ticket_text: str) -> dict:
        """根据输入关键词构建模拟分析结果。"""
        if "付款" in ticket_text or "付费" in ticket_text:
            return {
                "category": "支付问题",
                "priority": "高",
                "summary": "用户完成付款后，会员权益尚未生效。",
                "tags": ["支付", "会员", "权益未生效"],
                "order_id": None,
                "confidence": 0.95,
                "need_human_review": False,
                "uncertain_fields": [],
            }
        elif "会员" in ticket_text:
            return {
                "category": "账号问题",
                "priority": "中",
                "summary": "用户反馈会员相关问题，需要进一步确认具体表现。",
                "tags": ["会员", "账号"],
                "order_id": None,
                "confidence": 0.88,
                "need_human_review": False,
                "uncertain_fields": ["order_id"],
            }
        elif "登录" in ticket_text or "密码" in ticket_text:
            return {
                "category": "登录问题",
                "priority": "高",
                "summary": "用户无法正常登录系统，可能是密码错误或账号锁定导致。",
                "tags": ["登录", "密码"],
                "order_id": None,
                "confidence": 0.92,
                "need_human_review": False,
                "uncertain_fields": ["order_id"],
            }
        elif "退款" in ticket_text or "退货" in ticket_text:
            return {
                "category": "退款问题",
                "priority": "高",
                "summary": "用户申请退款或退货，需要客服介入处理。",
                "tags": ["退款", "售后"],
                "order_id": None,
                "confidence": 0.90,
                "need_human_review": True,
                "uncertain_fields": ["order_id"],
            }
        else:
            return {
                "category": "一般咨询",
                "priority": "低",
                "summary": "用户提交了工单，需要进一步确认具体问题类型。",
                "tags": ["咨询"],
                "order_id": None,
                "confidence": 0.75,
                "need_human_review": False,
                "uncertain_fields": ["category", "order_id"],
            }
