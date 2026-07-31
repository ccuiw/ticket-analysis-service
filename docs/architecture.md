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
- Docker Compose
- 提示词版本批量评估
