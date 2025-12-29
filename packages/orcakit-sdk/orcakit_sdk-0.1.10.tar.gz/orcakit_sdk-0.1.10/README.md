# OrcaKit SDK

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**OrcaKit SDK** 是基于 [LangGraph](https://github.com/langchain-ai/langgraph) 构建的 AI Agent 开发框架，提供了一套完整的工具和适配器，用于快速构建、部署和运行生产级 AI Agent 应用。

## ✨ 特性

- 🚀 **快速开发**：基于 LangGraph 的声明式 Agent 开发，简化复杂工作流
- 🔌 **多通道支持**：内置 LangGraph、OpenAI 兼容、A2A 协议、MCP Server、企业微信等多种通道
- 🛠️ **MCP 集成**：完整支持 Model Context Protocol，轻松接入外部工具和数据源
- 🔄 **MCP Server 通道**：将 Agent 暴露为 MCP Server，供其他 Agent 调用
- 💾 **持久化支持**：内置 MemorySaver 和 PostgreSQL checkpoint 存储
- 📊 **可观测性**：集成 Langfuse，提供完整的 Agent 运行追踪和分析
- 🔄 **流式输出**：支持流式响应，提升用户体验
- 🎯 **类型安全**：完整的类型注解，提供更好的 IDE 支持
- 📚 **Scalar API 文档**：内置美观的 API 文档界面

## 📦 安装

### 使用 pip

```bash
pip install orcakit-sdk
```

### 使用 uv（推荐）

```bash
uv pip install orcakit-sdk
```

### 开发模式安装

```bash
git clone https://github.com/yourusername/orcakit-sdk.git
cd orcakit-sdk
pip install -e ".[dev]"
```

## 🚀 快速开始

### 1. 创建一个简单的 Agent

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from orcakit_sdk.runner.agent_executor import LangGraphAgentExecutor
from orcakit_sdk.runner.runner import SimpleRunner

# 定义状态
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# 创建 LLM 节点
def chatbot(state: State) -> State:
    llm = ChatOpenAI(model="gpt-4")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.set_entry_point("chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

# 创建执行器
executor = LangGraphAgentExecutor(graph=graph)

# 创建运行器并启动（自动注册所有通道）
runner = SimpleRunner(port=8888)
runner.run(executor)
```

### 2. 调用 Agent

启动后，服务器会自动注册以下通道：

```bash
# LangGraph 通道 - 同步调用
curl -X POST http://localhost:8888/langgraph/call \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, how are you?"}'

# LangGraph 通道 - 流式调用
curl -X POST http://localhost:8888/langgraph/stream \
  -H "Content-Type: application/json" \
  -d '{"content": "Tell me a story"}' \
  --no-buffer

# OpenAI 兼容通道
curl -X POST http://localhost:8888/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "agent", "messages": [{"role": "user", "content": "Hello"}]}'

# 查看 API 文档
open http://localhost:8888/docs
```

## 📚 核心组件

### LangGraphAgentExecutor

`LangGraphAgentExecutor` 是 Agent 的执行引擎，负责管理 LangGraph 的执行、状态持久化和观测。

```python
from orcakit_sdk.runner.agent_executor import LangGraphAgentExecutor

executor = LangGraphAgentExecutor(
    graph=graph,
    name="my-agent",  # Agent 名称
)
```

**主要方法：**
- `call()` - 同步调用 Agent
- `stream()` - 流式调用，返回完整事件
- `stream_content()` - 流式调用，只返回文本内容

### SimpleRunner

`SimpleRunner` 是一个开箱即用的运行器，自动注册所有可用通道。

```python
from orcakit_sdk.runner.runner import SimpleRunner

runner = SimpleRunner(
    host="0.0.0.0",      # 服务器地址
    port=8888,           # 服务器端口
    log_level="info",    # 日志级别
    dev=False,           # 开发模式（支持热重载）
)

# 运行 Agent
runner.run(executor)
```

**自动注册的通道：**
- `/langgraph` - LangGraph 原生协议
- `/openai` - OpenAI 兼容 API
- `/wework` - 企业微信机器人
- `/mcp-server` - MCP Server 协议
- `/a2a-protocol` - A2A 协议

**多 Agent 支持：**

`run()` 方法支持多次调用，通过不同的 `url_prefix` 注册多个 Agent：

```python
from orcakit_sdk.runner.runner import SimpleRunner
from orcakit_sdk.runner.agent_executor import LangGraphAgentExecutor

# 创建多个 Agent
agent1 = LangGraphAgentExecutor(graph=graph1, name="agent1")
agent2 = LangGraphAgentExecutor(graph=graph2, name="agent2")

# 创建运行器
runner = SimpleRunner(port=8888)

# 注册多个 Agent 到不同的 URL 前缀
runner.run(agent1, url_prefix="/agent1", start=False)  # 不启动服务器
runner.run(agent2, url_prefix="/agent2", start=True)   # 启动服务器

# 访问方式：
# Agent1: http://localhost:8888/agent1/langgraph/call
# Agent2: http://localhost:8888/agent2/langgraph/call
```

> **注意**：每次调用 `run()` 时，`url_prefix` 必须不同，否则会导致路由冲突。最后一次调用设置 `start=True` 来启动服务器。

### MCP 适配器

集成 Model Context Protocol，轻松接入外部工具：

```python
from orcakit_sdk import get_mcp_tools

# 定义 MCP 服务器配置
mcp_servers = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/data"],
    }
}

# 获取工具
tools = await get_mcp_tools(mcp_servers)

# 在 LangGraph 中使用
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
```

## 🔧 通道说明

### LangGraph Channel

原生 LangGraph 协议，支持完整的状态管理和检查点功能。

**端点：**
- `POST /langgraph/call` - 同步调用
- `POST /langgraph/stream` - 流式调用

### OpenAI Channel

完全兼容 OpenAI Chat Completions API，可直接替换 OpenAI SDK 使用。

**端点：**
- `POST /openai/v1/chat/completions` - 聊天完成（支持流式）
- `GET /openai/v1/models` - 模型列表

### MCP Server Channel

将 Agent 暴露为 MCP Server，供其他 Agent 或 MCP 客户端调用。

**端点：**
- `POST /mcp-server/sse` - SSE 连接端点
- `POST /mcp-server/messages` - 消息处理端点

**环境变量：**
- `AGENT_NAME` - 工具名称
- `AGENT_DESCRIPTION` - 工具描述

### A2A Channel

支持 Agent-to-Agent (A2A) 协议，用于 Agent 之间的互操作。

**端点：**
- 完整的 A2A 协议端点（任务创建、查询、流式订阅等）

**环境变量：**
- `A2A_BASE_URL` - A2A 服务基础 URL

### 企业微信 Channel

支持企业微信机器人集成。

**端点：**
- `GET /wework/callback` - 验证回调
- `POST /wework/callback` - 消息回调

**环境变量：**
- `WEWORK_TOKEN` - 企业微信 Token
- `WEWORK_ENCODING_AES_KEY` - 企业微信 EncodingAESKey
- `WEWORK_CORP_ID` - 企业 ID
- `WEWORK_AGENT_ID` - 应用 ID
- `WEWORK_SECRET` - 应用 Secret

## 🔍 可观测性

### Langfuse 集成

`LangGraphAgentExecutor` 自动集成 Langfuse 追踪，只需配置环境变量：

```bash
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

追踪信息包括：
- 用户 ID (`user` 参数)
- 会话 ID (`thread_id` 参数)
- 自定义标签 (`tags` 参数)

## 💾 状态持久化

### MemorySaver (默认)

默认使用内存存储，适合开发和测试：

```python
executor = LangGraphAgentExecutor(graph=graph)
```

### PostgreSQL

配置 `POSTGRES_URI` 环境变量启用 PostgreSQL 持久化：

```bash
export POSTGRES_URI="postgresql://user:pass@localhost:5432/dbname"
```

需要安装额外依赖：

```bash
pip install langgraph-checkpoint-postgres psycopg[pool]
```

## 🔥 开发模式

支持热重载的开发模式：

```python
runner = SimpleRunner(port=8888, dev=True)
runner.run(
    executor,
    graph_module="my_agent.graph",  # 模块路径
    graph_attr="graph",              # 图对象属性名
)
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行集成测试
pytest tests/integration_tests/

# 运行单元测试
pytest tests/unit_tests/

# 带覆盖率
pytest tests/ --cov=orcakit_sdk
```

## 🛠️ 开发

### 代码规范

项目使用 `ruff` 进行代码检查和格式化：

```bash
# 检查代码
ruff check .

# 自动修复
ruff check --fix .

# 格式化代码
ruff format .
```

### 类型检查

```bash
mypy src/
```

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🤝 贡献

欢迎贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📞 联系方式

- 作者：Jubao Liang
- 邮箱：jubaoliang@gmail.com

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的 Agent 编排框架
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用开发框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Langfuse](https://langfuse.com/) - LLM 应用可观测平台
- [Scalar](https://scalar.com/) - 美观的 API 文档

---

**OrcaKit SDK** - 让 AI Agent 开发更简单 🐋
