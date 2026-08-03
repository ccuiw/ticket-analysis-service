# Architecture

## 系统分层

```text
┌──────────────────────────────────────────────┐
│                  Frontend                     │
│         React + TypeScript + Vite             │
│              HTTP POST / JSON                 │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│              API Layer (FastAPI)              │
│  - 请求校验 (Pydantic)                        │
│  - 异常 → HTTP 响应映射                       │
│  - 不包含 LLM / Prompt / Parse 逻辑           │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│        Application Layer                      │
│  TicketAnalysisService                       │
│  - 编排 Prompt → LLM → Parse → Validate       │
│  - 集成 RetryPolicy（网络重试）                │
│  - 集成 OutputRepairService（输出修复）        │
│  - 通过构造函数注入 Provider                   │
└────┬──────────┬──────────┬───────────────────┘
     │          │          │
┌────▼──┐ ┌────▼──┐ ┌─────▼──────────────┐
│Prompt │ │  LLM  │ │ Parsing / Validation│
│Layer  │ │ Layer │ │   / Repair Layer    │
│       │ │       │ │                     │
│loader │ │Base   │ │parse_raw_output()   │
│builder│ │Mock   │ │validate_structure() │
│repair │ │OpenAI │ │validate_business()  │
│prompt │ │+Retry │ │OutputRepairService  │
│       │ │       │ │RetryPolicy          │
└───────┘ └───────┘ └─────────────────────┘
```

## 关键设计决策

### 依赖方向

```
API → Application → Domain
API → Application → LLM (abstract)
API → Application → Prompt
API → Application → Parsing
API → Application → Validation
```

Domain 层不依赖 FastAPI、Pydantic、httpx 或任何外部 SDK。

### Provider 抽象

- `BaseLLMProvider` 是纯 ABC，定义 `analyze(messages) -> LLMResponse`
- `MockLLMProvider`：基于关键词的模拟实现，无需网络
- `OpenAICompatibleLLMProvider`：通过 httpx 调用任意 OpenAI-compatible API
- `create_provider()` 工厂根据环境变量 `LLM_PROVIDER` 选择实例
- 默认 Provider 是 `mock`，保证无 API Key 时仍可运行

### 消息结构

使用 `LLMMessage` 和 `LLMResponse` 作为领域类型，不直接暴露供应商 SDK 类型。
用户工单数据通过 `<ticket>...</ticket>` 标签隔离在独立的 User 消息中。

### 异常层次

```
DomainError
├── AnalysisError
├── PromptNotFoundError
├── PromptRenderError
├── LLMError
│   ├── LLMConfigurationError
│   ├── LLMAuthenticationError
│   ├── LLMTimeoutError (可重试)
│   ├── LLMConnectionError (可重试)
│   ├── LLMRateLimitError (可重试)
│   ├── LLMServerError (可重试)
│   ├── LLMRequestError (不可重试)
│   └── LLMEmptyResponseError
├── OutputParseError (可触发修复)
├── OutputValidationError (可触发修复)
├── OutputRepairError
│   └── OutputRepairExhaustedError
├── RetryConfigurationError
└── RepairFailedError (已废弃)
```

### 提示词版本

- V1：Zero-shot，纯指令 + 字段说明 + 输出格式
- V2：Few-shot，在 V1 基础上增加 3 个高质量示例
- 两个版本返回相同的数据结构
- 提示词文件存放在 `prompts/` 目录，运行时可配置路径

### 重试与修复

- `RetryPolicy`：控制网络级重试。可重试：`LLMTimeoutError`、`LLMConnectionError`、`LLMRateLimitError`、`LLMServerError`
- `OutputRepairService`：JSON 解析/校验失败时，使用 `json_repair.txt` 提示词请求模型修复输出
- 修复最多执行一次，网络重试最多 `LLM_MAX_ATTEMPTS` 次
- 最坏情况调用次数：初始 1 + 网络重试 1 + 修复 1 + 修复重试 1 = **4 次**
- 可通过 `LLM_OUTPUT_REPAIR_ENABLED=false` 关闭修复

### 当前范围外

- 备用模型
- 多供应商
- 生产环境监控

## 评估架构

```
backend/src/app/evaluation/
├── models.py          # TestCase, EvaluationCaseResult, EvaluationMetrics
├── dataset.py         # Load/validate test_cases.jsonl
├── metrics.py         # 11 evaluation metrics
├── runner.py          # Run evaluation for one prompt version
├── report_writer.py   # Generate JSON, CSV, Markdown reports
├── run.py             # CLI entry: python -m app.evaluation.run
└── cli.py             # Argument parsing
```

### 评估指标

- JSON Parse Rate — 首次模型输出可被严格 JSON 解析的比例
- Structured Success Rate — 最终通过结构校验的比例
- Category Accuracy — 分类准确率
- Priority Accuracy — 优先级准确率
- Order ID Accuracy — 订单号准确率（含虚构检测）
- Human Review Accuracy — 人工审核准确率
- Tag Recall — 标签召回率
- Fabrication Rate — 编造率
- Repair Trigger Rate — 修复触发率
- Average Provider Calls — 平均调用次数
- End-to-End Success Rate — 端到端成功率

## Docker 架构

```
docker-compose.yml
├── backend (python:3.12-slim)
│   ├── uvicorn on 0.0.0.0:8000
│   ├── /app/src/          (backend source)
│   ├── /app/prompts/      (prompt templates, COPY)
│   ├── /app/schemas/      (JSON Schema, COPY)
│   ├── /app/data/         (test cases, COPY)
│   └── /app/reports/      (evaluation output, volume mount)
└── frontend (node:22-alpine → nginx:alpine)
    ├── multi-stage build (npm build → nginx)
    └── port 80 mapped to 5173
```

## 思考模式配置

所有 LLM 请求统一使用 `LLM_THINKING_MODE` 配置：

```python
# openai_compatible.py — 每次 /chat/completions 请求均包含
"thinking": {"type": "disabled"}  # 或 "enabled"
```

- 默认值：`disabled`（适合分类和结构化输出任务）
- 配置校验：仅接受 `enabled` 或 `disabled`
- 所有调用路径一致：分析、重试、修复、评估
- Provider 构造时确定，整个生命周期不变
