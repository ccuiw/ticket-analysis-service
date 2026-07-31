"""POST /api/v1/tickets/analyze 端点测试。"""

from fastapi.testclient import TestClient


class TestAnalyzeEndpoint:
    def test_valid_request_returns_200(self, client: TestClient, valid_request_body: dict):
        response = client.post("/api/v1/tickets/analyze", json=valid_request_body)
        assert response.status_code == 200
        data = response.json()
        # 验证所有字段存在
        assert "category" in data
        assert "priority" in data
        assert "summary" in data
        assert "tags" in data
        assert "order_id" in data
        assert "confidence" in data
        assert "need_human_review" in data
        assert "uncertain_fields" in data

    def test_response_is_valid_json(self, client: TestClient, valid_request_body: dict):
        response = client.post("/api/v1/tickets/analyze", json=valid_request_body)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_confidence_within_range(self, client: TestClient, valid_request_body: dict):
        response = client.post("/api/v1/tickets/analyze", json=valid_request_body)
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_payment_keyword_returns_payment_category(self, client: TestClient):
        body = {"ticket_text": "付款后会员没到账", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "支付问题"
        assert data["priority"] == "高"

    def test_member_keyword_returns_account_category(self, client: TestClient):
        body = {"ticket_text": "会员等级显示错误", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "账号问题"

    def test_login_keyword_returns_login_category(self, client: TestClient):
        body = {"ticket_text": "我忘记了密码，无法登录系统", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "登录问题"

    def test_refund_keyword_returns_refund_category(self, client: TestClient):
        body = {"ticket_text": "我要申请退款", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "退款问题"
        assert data["need_human_review"] is True

    def test_empty_ticket_text_returns_422(self, client: TestClient):
        body = {"ticket_text": "", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 422

    def test_missing_ticket_text_returns_422(self, client: TestClient):
        body = {"prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 422

    def test_invalid_prompt_version_returns_422(self, client: TestClient):
        body = {"ticket_text": "需要帮助", "prompt_version": "v3"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 422

    def test_prompt_version_v2_is_accepted(self, client: TestClient):
        body = {"ticket_text": "需要帮助", "prompt_version": "v2"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200

    def test_unknown_keyword_returns_default_result(self, client: TestClient):
        body = {"ticket_text": "请问你们的营业时间是几点", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "一般咨询"
        assert "category" in data["uncertain_fields"]
