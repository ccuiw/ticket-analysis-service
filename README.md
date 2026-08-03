# Ticket Analysis Service

工单文本分析服务 —— 用户提交工单文本，后端调用大模型进行结构化分析，返回固定 JSON。

## 技术栈

- **后端:** Python 3.12+, FastAPI, Pydantic, httpx
- **前端:** React 18, TypeScript, Vite, CSS Modules
- **测试:** pytest (后端), TypeScript + ESLint (前端)
- **基础设施:** Git, GitHub, Docker Compose

## 架构

```
Frontend (React + Vite)
    │  HTTP POST /api/v1/tickets/analyze
    ▼
FastAPI Backend
    │
    ▼
TicketAnalysisService
    ├── Prompt Layer       (loader, builder, repair prompt)
    ├── LLM Layer          (Mock / OpenAI Compatible + Retry)
    ├── Parsing Layer      (JSON parse)
    ├── Validation Layer   (structural + business)
    ├── Repair Layer       (output repair, retry policy)
    └── Evaluation Layer   (metrics, reports)
            │
            ▼
    LLM Provider (DeepSeek / OpenAI Compatible API)
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 22+
- npm 9+
- Docker Desktop（可选）

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

参考 `backend/.env.example`，复制为 `backend/.env` 并填写：

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
LLM_THINKING_MODE=disabled
LLM_TIMEOUT_SECONDS=60
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

## 提示词工程

### V1：Zero-shot Prompt

- 基础任务描述
- JSON 输出约束
- 字段说明
- 禁止编造规则
- 缺失值处理策略

策略：Instruction-driven generation

### V2：Few-shot Prompt

- 在 V1 基础上增加 3 个高质量示例
- 覆盖明确分类（含订单号）
- 覆盖缺失订单号（uncertain_fields 处理）
- 覆盖信息不足（低置信度 + 人工审核）
- 边界情况说明
- 防止模型编造

策略：Example-guided generation

两个版本返回相同的数据结构，用于比较 Zero-shot 与 Few-shot 的效果差异。

## 评估结果

### Mock 评估（验证评估管道）

> ⚠️ Mock evaluation only verifies the evaluation pipeline. It does **not** represent real LLM performance.

| 指标 | V1 | V2 |
| --- | --- | --- |
| JSON Parse Rate | 100.0% | 100.0% |
| Structured Success Rate | 100.0% | 100.0% |
| Category Accuracy | 45.0% | 45.0% |
| Fabrication Rate | 0.0% | 0.0% |
| Repair Trigger Rate | 0.0% | 0.0% |
| End-to-End Success Rate | 15.0% | 15.0% |

V1 与 V2 的 Mock 结果相同，因为 Mock Provider 基于关键词匹配，不受提示词语义影响。

### 真实 LLM 评估

运行以下命令进行真实评估（将消耗 API 额度）：

```bash
cd backend
python -m app.evaluation.run --provider openai_compatible --versions v1 v2 --dataset ../data/test_cases.jsonl
```

## Docker 部署

### 前置条件

- Docker Desktop
- Docker Compose

### 构建

```bash
docker compose build
```

### 启动

```bash
docker compose up -d
```

### 检查状态

```bash
docker compose ps
```

### 查看日志

```bash
# 后端日志
docker compose logs backend

# 前端日志
docker compose logs frontend
```

### 停止

```bash
# 暂停容器（保留状态）
docker compose stop

# 关闭并删除容器
docker compose down
```

### 容器访问

| 服务 | 地址 |
| --- | --- |
| Backend API | <http://localhost:8000> |
| API Docs | <http://localhost:8000/docs> |
| Frontend | <http://localhost:5173> |

## 目录结构

```text
.
├── backend/             # FastAPI 后端
│   ├── src/app/         # 应用源码
│   │   ├── api/         # API 路由层
│   │   ├── application/ # 应用服务层
│   │   ├── domain/      # 领域模型和异常
│   │   ├── llm/         # LLM Provider 层
│   │   ├── prompts/     # 提示词加载
│   │   ├── parsing/     # JSON 解析
│   │   ├── validation/  # 结构/业务校验
│   │   ├── repair/      # 重试/修复
│   │   └── evaluation/  # 评估模块
│   ├── Dockerfile
│   └── tests/           # 测试
├── frontend/            # React + TypeScript 前端
│   ├── src/
│   │   ├── api/         # API 调用模块
│   │   ├── types/       # TypeScript 类型定义
│   │   └── components/  # UI 组件
│   └── Dockerfile
├── prompts/             # 提示词模板
├── schemas/             # JSON Schema
├── data/                # 测试数据 (20 cases)
├── docs/                # 文档
│   └── architecture.md  # 架构文档
├── reports/             # 评估报告
└── docker-compose.yml
```

## 当前状态

- [x] 项目初始化：FastAPI + React 骨架
- [x] LLM Provider 抽象：Mock + OpenAI-compatible (DeepSeek)
- [x] 真实提示词模板：Zero-shot (V1) + Few-shot (V2)
- [x] 结构化分析管道：Prompt → LLM → Parse → Validate
- [x] 统一非思考模式：`LLM_THINKING_MODE=disabled`
- [x] 网络重试：可重试错误自动重试（超时、连接、429、5xx）
- [x] 输出修复：JSON 解析/校验失败时单次 LLM 修复
- [x] Zero-shot / Few-shot 提示词版本比较（评估框架 + 20 条测试数据）
- [x] 评估报告生成（JSON、CSV、Markdown + 6 章节分析报告）
- [x] Docker Compose 部署（backend + frontend 容器化）
- [ ] 真实 LLM 评估优化
- [ ] 多 Provider 支持
- [ ] 生产环境监控

## 许可

内部项目。
