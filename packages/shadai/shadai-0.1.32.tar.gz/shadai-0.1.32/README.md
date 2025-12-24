# Shadai Client - Official Python SDK

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Beautiful, Pythonic client for Shadai AI services.** Query your knowledge base, orchestrate custom tools with intelligent agents, and more with an intuitive, production-ready API.

## 🆕 What's New in v0.1.29

- **🧠 Memory enabled by default** - All tools now use conversation memory by default for better context continuity
- **💬 Chat history management** - New methods to retrieve and clear session history with pagination
- **📖 Enhanced documentation** - Updated examples and API reference with new features

## ✨ Features

- 🚀 **Easy to use** - Clean, intuitive API design with one-step async patterns
- ⚡ **Async streaming** - Real-time streaming responses for all tools
- 🛠️ **Multiple tools** - Query, summarize, search, engine, and intelligent agent
- 🤖 **Intelligent agent** - Automatic plan → execute → synthesize workflow
- 🧠 **Conversation memory** - Built-in memory enabled by default for context continuity
- 💬 **Chat history management** - Get and clear session history with pagination
- 🔒 **Type-safe** - Full type hints and Pydantic models for better IDE support
- 📦 **Minimal dependencies** - Only requires `aiohttp` and `pydantic`
- 🎯 **Production-ready** - Comprehensive error handling

## 📦 Installation

```bash
pip install shadai-client
```

Or install from source:

```bash
cd client
pip install -e .
```

## 🚀 Quick Start

```python
import asyncio
from shadai import Shadai

async def main():
    # Create session and query
    async with Shadai(name="my-session") as shadai:
        # Ingest documents
        await shadai.ingest(folder_path="./documents")

        # Query knowledge base
        async for chunk in shadai.query("What is machine learning?"):
            print(chunk, end="", flush=True)

asyncio.run(main())
```

## 📚 Usage Examples

### Knowledge Base Query

Query your uploaded documents using RAG (Retrieval-Augmented Generation):

```python
async with Shadai(name="research") as shadai:
    # Ingest documents
    await shadai.ingest(folder_path="./documents")

    # Ask questions about your documents
    async for chunk in shadai.query("What are the key findings?"):
        print(chunk, end="", flush=True)

    # Memory is enabled by default for context continuity
    async for chunk in shadai.query("Tell me more about that"):
        print(chunk, end="", flush=True)

    # Disable memory if needed
    async for chunk in shadai.query("Independent question", use_memory=False):
        print(chunk, end="", flush=True)
```

### Document Summarization

Generate comprehensive summaries of all documents in a session:

```python
async with Shadai(name="research") as shadai:
    await shadai.ingest(folder_path="./documents")

    async for chunk in shadai.summarize():
        print(chunk, end="", flush=True)
```

### Web Search

Search the internet for current information:

```python
async with Shadai(name="news") as shadai:
    async for chunk in shadai.web_search("Latest AI developments 2024"):
        print(chunk, end="", flush=True)
```

### Chat History Management

Retrieve and manage conversation history for sessions:

```python
async with Shadai(name="chat") as shadai:
    # Get chat history with pagination
    history = await shadai.get_session_history(
        page=1,
        page_size=5  # Default: 5, Max: 10
    )

    print(f"Total messages: {history['count']}")
    for message in history["results"]:
        print(f"{message['role']}: {message['content']}")

    # Clear all chat history
    result = await shadai.clear_session_history()
    print(result["message"])  # "Session history cleared successfully"
```

### Unified Engine

Orchestrate multiple tools for comprehensive answers:

```python
async with Shadai(name="analysis") as shadai:
    await shadai.ingest(folder_path="./documents")

    async for chunk in shadai.engine(
        prompt="Compare my docs with current trends",
        use_knowledge_base=True,
        use_web_search=True
    ):
        print(chunk, end="", flush=True)
```

### Intelligent Agent

Orchestrate plan → execute → synthesize workflow with custom tools.
**The planner automatically infers tool arguments from your prompt!**

```python
from shadai import Shadai, tool

# Define tools using @tool decorator
@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search database for user information.

    Args:
        query: Search query string
        limit: Maximum number of results
    """
    # Your implementation
    return "Search results..."

@tool
def generate_report(data: str, format: str = "text") -> str:
    """Generate a formatted report.

    Args:
        data: Data to include in report
        format: Report format (text, pdf, etc.)
    """
    # Your implementation
    return "Generated report..."

# Agent automatically infers arguments from your prompt!
async with Shadai(name="agent") as shadai:
    async for chunk in shadai.agent(
        prompt="Find the top 5 users and create a PDF report",
        tools=[search_database, generate_report]
    ):
        print(chunk, end="", flush=True)
```

The agent automatically:
1. **Plans** which tools to use based on your prompt
2. **Infers** the appropriate arguments for each tool from your prompt
3. **Executes** the selected tools locally with inferred arguments
4. **Synthesizes** all outputs into a unified, coherent answer

## 🔧 Configuration

### Environment Variables

```bash
export SHADAI_API_KEY="your-api-key"
export SHADAI_BASE_URL="http://localhost"  # Optional
```

### Client Initialization

```python
# Named session (persistent)
async with Shadai(name="my-project") as shadai:
    await shadai.ingest(folder_path="./docs")

# Temporal session (auto-deleted)
async with Shadai(temporal=True) as shadai:
    async for chunk in shadai.query("Quick question"):
        print(chunk, end="")

# Custom configuration
async with Shadai(
    name="custom",
    api_key="your-api-key",
    base_url="https://api.shadai.com",
    timeout=60  # seconds
) as shadai:
    pass
```

## 🛠️ Available Tools

| Tool | Description | Streaming |
|------|-------------|-----------|
| `query()` | Query knowledge base with RAG | ✅ |
| `summarize()` | Summarize all session documents | ✅ |
| `web_search()` | Search web for current information | ✅ |
| `engine()` | Unified multi-tool orchestration | ✅ |
| `agent()` | Intelligent agent (plan → execute → synthesize) | ✅ |
| `get_session_history()` | Retrieve chat history with pagination | ❌ |
| `clear_session_history()` | Clear all messages in a session | ❌ |

## 📖 API Reference

### Shadai

Main entry point for the client.

```python
Shadai(
    name: str = None,
    temporal: bool = False,
    api_key: str = None,
    base_url: str = "http://localhost",
    timeout: int = 30
)
```

**Methods:**
- `ingest(folder_path)` → `Dict` - Ingest documents from folder
- `query(query, use_memory=True)` → `AsyncIterator[str]` - Query knowledge base
- `summarize(use_memory=True)` → `AsyncIterator[str]` - Summarize documents
- `web_search(prompt, use_web_search=True, use_memory=True)` → `AsyncIterator[str]` - Search web
- `engine(prompt, **options)` → `AsyncIterator[str]` - Unified engine
- `agent(prompt, tools)` → `AsyncIterator[str]` - Intelligent agent
- `get_session_history(page=1, page_size=5)` → `Dict[str, Any]` - Get chat history
- `clear_session_history()` → `Dict[str, str]` - Clear chat history

### query()

Query your knowledge base with streaming responses. Memory enabled by default.

```python
async with Shadai(name="docs") as shadai:
    async for chunk in shadai.query("What is AI?", use_memory=True):
        print(chunk, end="")
```

### summarize()

Summarize all documents in a session. Memory enabled by default.

```python
async with Shadai(name="docs") as shadai:
    async for chunk in shadai.summarize(use_memory=True):
        print(chunk, end="")
```

### web_search()

Search the web for current information. Memory enabled by default.

```python
async with Shadai(name="search") as shadai:
    async for chunk in shadai.web_search("Latest AI news"):
        print(chunk, end="")
```

### engine()

Unified engine with multiple tool capabilities. Memory enabled by default.

```python
async with Shadai(name="engine") as shadai:
    async for chunk in shadai.engine(
        prompt="Analyze my documents",
        use_knowledge_base=True,
        use_web_search=True
    ):
        print(chunk, end="")
```

### get_session_history()

Retrieve chat history with pagination support.

```python
async with Shadai(name="chat") as shadai:
    history = await shadai.get_session_history(page=1, page_size=5)

    # Response includes: count, next, previous, results
    for msg in history["results"]:
        print(f"{msg['role']}: {msg['content']}")
```

### clear_session_history()

Clear all messages in a session.

```python
async with Shadai(name="chat") as shadai:
    result = await shadai.clear_session_history()
    # Returns: {"message": "Session history cleared successfully"}
```

### agent()

Intelligent agent that orchestrates custom tools.

```python
from shadai import tool

@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return "result"

async with Shadai(name="agent") as shadai:
    async for chunk in shadai.agent(
        prompt="Execute task",
        tools=[my_tool]
    ):
        print(chunk, end="")
```

## 🚨 Error Handling

```python
from shadai import (
    Shadai,
    AuthenticationError,
    ConnectionError,
    ServerError
)

try:
    shadai = Shadai(api_key="invalid-key")
    await shadai.health()
except AuthenticationError:
    print("Invalid API key")
except ConnectionError:
    print("Cannot connect to server")
except ServerError as e:
    print(f"Server error: {e}")
```

## 📝 Examples

Check the `examples/` directory for complete examples:

- `query_example.py` - Knowledge base queries
- `summary_example.py` - Document summarization
- `websearch_example.py` - Web search
- `agent_example.py` - Intelligent agent workflow
- `agent_synthesis_example.py` - Advanced synthesis with multiple data sources
- `complete_workflow.py` - Full agent workflow with multiple examples

Run examples:

```bash
cd client/
python examples/query_example.py
python examples/summary_example.py
python examples/websearch_example.py
python examples/agent_example.py
python examples/agent_synthesis_example.py
python examples/complete_workflow.py
```

## 🔒 Security

- Always use environment variables for API keys
- Never commit API keys to version control
- Use HTTPS in production (`base_url="https://..."`)

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines.

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **Documentation**: https://docs.shadai.com
- **GitHub**: https://github.com/shadai/shadai-client
- **Issues**: https://github.com/shadai/shadai-client/issues

## 💡 Support

- 📧 Email: support@shadai.com
- 💬 Discord: https://discord.gg/shadai
- 📖 Docs: https://docs.shadai.com

---

Made with ❤️ by the Shadai Team
