# 第四周 AI 部门练习项目总结

## 1. 项目介绍

### 项目背景

第四周 AI 部门实践任务。项目名称为 `ticket-analysis-service`，目标是从简单调用 LLM API 进阶到构建稳定、可维护、可评估的 LLM 应用系统。

### 项目目标

实现一个基于大语言模型（LLM）的工单智能分析系统。用户在前端输入工单文本，后端调用 LLM 进行结构化分析，返回固定的 JSON 结果。

### 核心能力

- 工单文本自动分类（支付、登录、退款、订单等）
- 结构化信息提取（订单号、优先级、置信度等）
- 标签自动生成
- JSON 固定格式输出
- Pydantic Schema 校验
- JSON 格式错误自动修复
- 多 Prompt 版本比较（Zero-shot vs Few-shot）
- 自动化评估体系
- Docker 容器化部署

## 2. 技术架构

```
┌──────────────────────────────────────────────┐
│              Frontend (React + Vite)           │
│          HTTP POST /api/v1/tickets/analyze     │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│           API Layer (FastAPI + Pydantic)       │
│         请求校验 → 异常 → HTTP 响应映射         │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│      Application Layer (TicketAnalysisService) │
│     Prompt → LLM → Parse → Validate → Repair   │
└────┬──────────┬──────────┬───────────────────┘
     │          │          │
┌────▼──┐ ┌────▼──┐ ┌─────▼──────────────┐
│Prompt │ │  LLM  │ │ Parsing / Validate  │
│Layer  │ │ Layer │ │   / Repair / Eval   │
│V1/V2  │ │Mock   │ │JSON Parse           │
│Builder│ │OpenAI │ │Schema Validate      │
│Repair │ │+Retry │ │Output Repair        │
└───────┘ └───────┘ └─────────────────────┘
```

### 层级职责

| 层 | 职责 | 依赖 |
|---|---|---|
| API Layer | 接收请求、校验输入、映射异常到 HTTP | FastAPI, Pydantic |
| Application Layer | 编排完整分析流程 | 各层抽象接口 |
| Prompt Layer | 版本化提示词加载和构造 | 文件系统 |
| LLM Layer | 供应商抽象，Mock 和真实 Provider | httpx（仅真实 Provider） |
| Parsing Layer | 严格 JSON 解析 | json 标准库 |
| Validation Layer | Pydantic 结构校验 + 业务校验 | Pydantic |
| Repair Layer | 单次输出修复 + 受控网络重试 | LLM Provider |
| Evaluation Layer | 批量测试 + 指标计算 + 报告生成 | TicketAnalysisService |
| Domain Layer | 异常层次结构 | 无外部依赖 |

## 3. 完成功能

### Prompt Engineering

- **V1 Zero-shot**: System Prompt 中描述任务、字段定义、输出格式和规则
- **V2 Few-shot**: 在 V1 基础上增加 3 个高质量示例，覆盖明确分类、缺失订单号、信息不足场景
- Prompt 版本化管理和文件加载（不在 Python 代码中硬编码）
- `<ticket>` 标签隔离用户工单数据
- `json_repair.txt` 修复提示词

### Structured Output

- 严格 JSON 输出约束（Pydantic `AnalysisResult`）
- 8 个字段：`category`, `priority`, `summary`, `tags`, `order_id`, `confidence`, `need_human_review`, `uncertain_fields`
- `confidence` 范围约束 0.0-1.0
- 字段类型自动校验

### Reliability Engineering

- **RetryPolicy**: 网络级重试策略（指数退避，最大尝试次数可控）
- 可重试错误：Timeout、Connection Error、429 Rate Limit、500/502/503/504
- 不可重试错误：401/403 Authentication、Configuration Error、4xx
- **OutputRepairService**: JSON 解析/校验失败时单次 LLM 修复
- 最坏调用次数上限：4 次（初始 + 重试 + 修复 + 修复重试）
- 12 种领域异常类型，按类型映射为 HTTP 状态码

### Evaluation Framework

- 20 条固定测试数据（7 种类型：明确问题、边界、多问题、信息不足、口语化、无关信息、防编造）
- 11 项评估指标
- V1/V2 分版本执行
- JSON + CSV + Markdown 三种报告格式
- 6 章节 Markdown 报告（Experiment Overview、Prompt Comparison、Failure Analysis、Prompt Difference Analysis、Limitations、Recommendations）

### Thinking Mode

- 统一 `LLM_THINKING_MODE=disabled` 配置
- 所有请求（分析、重试、修复、评估）使用同一配置
- 配置校验 + 测试覆盖

### Docker Deployment

- Backend: Python 3.12-slim + Uvicorn
- Frontend: Node 22 Alpine build → Nginx
- Docker Compose 编排
- Reports 目录持久化挂载
- Backend healthcheck
- `.env` 排除（通过 `.dockerignore`）

## 4. 开发过程中遇到的问题

### 问题 1：Docker Hub 网络连接失败

**描述**: 执行 `docker compose build` 时，拉取 `node:22-alpine` 镜像失败。

**错误信息**: `failed to fetch oauth token: dial tcp ... auth.docker.io: connectex: A connection attempt failed`

**原因**: VPN 智能模式无法代理 Docker Desktop 后台请求。Docker 的网络请求走系统代理，与浏览器网络环境不同。

**解决**:
1. 切换 VPN 为全局模式
2. 在 Docker Desktop Settings 中配置代理
3. 验证 `docker pull` 可用

**总结**: Docker 网络环境独立于浏览器和终端，需要单独配置代理。在中国大陆网络环境下部署容器化应用需要提前准备镜像加速或代理方案。

### 问题 2：Docker Python `src` 布局错误

**描述**: 后端 Docker 构建失败。

**错误信息**: `error in 'egg_base' option: 'src' does not exist or is not a directory`

**原因**: Dockerfile 中 `pip install -e ".[dev]"` 在 `COPY src/` 之前执行。项目使用 `pyproject.toml` 的 `src` 布局（`package-dir = {"" = "src"}`），`pip install` 时需要 `src/` 目录已存在。

**解决**: 调整 Dockerfile 中 COPY 顺序——先 `COPY backend/src/ ./src/`，再执行 `pip install`。

**总结**: 需要理解 Docker build layer 的执行顺序和 Python 包结构。Dockerfile 中的每一条指令是一个独立的构建层，文件必须在使用前复制到容器中。

### 问题 3：Node 版本兼容问题

**描述**: 前端 Docker 构建时出现 Node 版本警告。

**错误信息**: `EBADENGINE — package requires node 20 or >=22, current node: v18.20.8`

**原因**: `frontend/Dockerfile` 使用 `node:18-alpine`，但 `package.json` 中声明的依赖要求 Node 20+。

**解决**: 将前端 Dockerfile 的基础镜像从 `node:18-alpine` 升级到 `node:22-alpine`。

**总结**: 前端依赖的版本管理非常重要。需要在 Docker 镜像中保持与本地开发环境一致的 Node 版本。

### 问题 4：LLM 输出稳定性

**描述**: 直接调用 LLM API 时，模型输出不够稳定，存在以下问题：
- JSON 格式错误（缺失引号、多余逗号、Markdown 代码块包裹）
- 分类结果不一致
- 偶尔编造工单中不存在的信息（如虚构订单号）

**解决**: 不是在 Prompt 层面不断修补，而是在工程层面建立了多层保障：
1. **Schema 约束**: Pydantic 模型定义严格的数据契约
2. **Validation 层**: 结构和业务双重校验
3. **Retry 层**: 网络级故障自动恢复
4. **Repair 层**: 输出格式错误自动修复
5. **Evaluation 层**: 批量测试持续监控质量

**总结**: 生产级 LLM 应用需要外围工程保障。模型负责理解和生成，工程负责限制、检查和修复。

### 问题 5：CORS 跨域配置

**描述**: 前端 `http://localhost:5173` 调用后端 `http://127.0.0.1:8000` 时出现跨域错误。

**原因**: 浏览器将 `localhost` 和 `127.0.0.1` 视为不同源，且 CORS 配置仅允许 `localhost`。

**解决**: 将 CORS 配置改为显式列出两个来源：`http://localhost:5173` 和 `http://127.0.0.1:5173`。

## 5. 技术收获

### 从 API 调用到应用工程

简单的 `Prompt + API` 调用不足以构成生产系统。一个完整的 LLM 应用需要：

```
Prompt Engineering
    +
Architecture Design
    +
Validation Layer
    +
Error Recovery
    +
Evaluation Framework
    +
Containerized Deployment
```

### 对 LLM 应用开发的理解

- **模型负责**: 理解文本、生成结果
- **工程负责**: 限制输出格式、检查错误、保证稳定性、评估质量
- **提示词不是银弹**: 即使是最好的 Prompt 也无法 100% 保证输出格式正确
- **测试驱动 Prompt 优化**: 固定的测试数据和指标比人工判断更可靠
- **可观测性**: 日志、指标和报告是 LLM 应用的必要组成部分

### 技术栈收获

| 领域 | 收获 |
|---|---|
| FastAPI + Pydantic | 自动校验、自动文档、异步支持 |
| httpx | 直接调用 REST API 替代 SDK，减少依赖 |
| Prompt Engineering | System/User 分离、版本管理、数据隔离 |
| Docker | 多阶段构建、build context 管理、compose 编排 |
| pytest | 异步测试、mock 策略、参数化测试 |
| Git | 分支管理、Conventional Commits、PR 工作流 |

## 6. 项目不足

- 评估数据规模较小（仅 20 条人工设计案例）
- 尚未执行真实 LLM 评估（Mock 结果不能代表真实提示词质量）
- 缺少持久化存储（数据库）
- 缺少用户认证机制
- 缺少生产环境监控和告警
- 仅支持单一 Provider（OpenAI-compatible）
- 缺少 A/B 测试和在线评估能力

## 7. 后续计划

### 短期（1-2 周）

- 配置 DeepSeek API Key，执行真实 V1 vs V2 评估
- 根据评估结果优化 Prompt
- 扩展测试数据集至 50+ 条

### 中期（1 个月）

- 增加多 Provider 支持
- 引入数据库存储分析历史
- 增加简单的用户认证
- 部署到云服务器

### 长期

- 生产环境监控和告警
- 在线评估和 A/B 测试
- 模型微调
- CI/CD 自动化测试和部署
