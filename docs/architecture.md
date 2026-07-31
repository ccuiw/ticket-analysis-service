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
│  - 通过构造函数注入 Provider                   │
└────┬──────────┬──────────┬───────────────────┘
     │          │          │
┌────▼──┐ ┌────▼──┐ ┌─────▼──────────────┐
│Prompt │ │  LLM  │ │ Parsing / Validation│
│Layer  │ │ Layer │ │ Layer               │
│       │ │       │ │                     │
│loader │ │Base   │ │parse_raw_output()   │
│builder│ │Mock   │ │validate_structure() │
│       │ │OpenAI │ │validate_business()  │
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
│   ├── LLMTimeoutError
│   ├── LLMRequestError
│   └── LLMEmptyResponseError
├── OutputParseError
├── OutputValidationError
└── RepairFailedError (reserved)
```

### 提示词版本

- V1：Zero-shot，纯指令 + 字段说明 + 输出格式
- V2：Few-shot，在 V1 基础上增加 3 个高质量示例
- 两个版本返回相同的数据结构
- 提示词文件存放在 `prompts/` 目录，运行时可配置路径

### 当前范围外

- JSON 自动修复（markdown fence、尾随逗号等）
- 自动重试
- 备用模型
- 多供应商
- Docker Compose
