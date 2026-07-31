# Ticket Analysis Service

工单文本分析服务 —— 用户提交工单文本，后端调用大模型进行结构化分析，返回固定 JSON。

## 技术栈

- **后端:** Python 3.12+, FastAPI, Pydantic, httpx
- **前端:** React 18, TypeScript, Vite, CSS Modules
- **测试:** pytest (后端), TypeScript + ESLint (前端)
- **基础设施:** Git, GitHub, Docker Compose（后续）

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- npm 9+

### 后端

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# 或: .venv\Scripts\activate   # Windows CMD
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问 <http://127.0.0.1:8000/docs> 查看自动生成的 API 文档。

**默认使用 Mock Provider**，无需配置任何 API Key 即可运行。

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 <http://localhost:5173> 使用分析界面。

### 运行测试

```bash
# 后端测试
cd backend
python -m pytest -v

# 前端类型检查和 lint
cd frontend
npx tsc --noEmit
npx eslint src/
```

## LLM Provider 配置

### Mock 模式（默认）

无需配置，默认使用基于关键词匹配的模拟分析器。适合开发和测试。

### OpenAI-compatible 模式

在 `.env` 文件中配置以下变量：

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_TIMEOUT_SECONDS=30
```

支持任意兼容 OpenAI Chat Completions API 的服务。

**警告：不要将包含真实 API Key 的 `.env` 文件提交到 Git。**

## API 概览

### `GET /health`

健康检查。

```json
{"status": "healthy"}
```

### `POST /api/v1/tickets/analyze`

工单分析。

**请求：**

```json
{
  "ticket_text": "我已经付款，但是会员还没有生效。",
  "prompt_version": "v1"
}
```

**响应：**

```json
{
  "category": "支付问题",
  "priority": "高",
  "summary": "用户完成付款后，会员权益尚未生效。",
  "tags": ["支付", "会员", "权益未生效"],
  "order_id": null,
  "confidence": 0.95,
  "need_human_review": false,
  "uncertain_fields": []
}
```

### 提示词版本

| 版本 | 策略 | 说明 |
| --- | --- | --- |
| `v1` | Zero-shot | 纯指令 + 字段说明 + 输出格式要求 |
| `v2` | Few-shot | 在 V1 基础上增加 3 个示例，覆盖明确分类、缺失订单号、信息不足场景 |

两个版本返回相同的数据结构。

## 目录结构

```text
.
├── backend/             # FastAPI 后端
│   ├── src/app/         # 应用源码
│   └── tests/           # 测试
├── frontend/            # React + TypeScript 前端
│   ├── src/
│   │   ├── api/         # API 调用模块
│   │   ├── types/       # TypeScript 类型定义
│   │   └── components/  # UI 组件
│   └── public/
├── prompts/             # 提示词模板
├── schemas/             # JSON Schema
├── data/                # 测试数据
├── docs/                # 文档
│   └── architecture.md  # 架构文档
└── reports/             # 评估报告
```

## 当前状态

- [x] 项目初始化：FastAPI + React 骨架
- [x] LLM Provider 抽象：Mock + OpenAI-compatible
- [x] 真实提示词模板：Zero-shot (V1) + Few-shot (V2)
- [x] 结构化分析管道：Prompt → LLM → Parse → Validate
- [x] 模拟分析接口：关键词感知 Mock Provider
- [x] 网络重试：可重试错误自动重试（超时、连接、429、5xx）
- [x] 输出修复：JSON 解析/校验失败时单次 LLM 修复
- [ ] Zero-shot / Few-shot 提示词版本比较
- [ ] 评估报告生成
- [ ] Docker Compose 部署

## 许可

内部项目。
