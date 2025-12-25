# AgentBay SDK for Python

> Execute commands, operate files, and run code in cloud environments

## 📦 Installation

```bash
pip install wuying-agentbay-sdk
```

## 🚀 Prerequisites

Before using the SDK, you need to:

1. Register an Alibaba Cloud account: [https://aliyun.com](https://aliyun.com)
2. Get API credentials: [AgentBay Console](https://agentbay.console.aliyun.com/service-management)
3. Set environment variable: `export AGENTBAY_API_KEY=your_api_key`

## 🚀 Quick Start

### Synchronous API (Default)

```python
from agentbay import AgentBay

# Create session
agent_bay = AgentBay()
result = agent_bay.create()

if result.success:
    session = result.session

    # Execute command
    cmd_result = session.command.execute_command("ls -la")
    print(cmd_result.output)

    # File operations
    session.file_system.write_file("/tmp/test.txt", "Hello World")
    content = session.file_system.read_file("/tmp/test.txt")
    print(content.content)  # Hello World

    # Clean up
    agent_bay.delete(session)
```

### Asynchronous API

```python
import asyncio
from agentbay import AsyncAgentBay

async def main():
    # Create session
    agent_bay = AsyncAgentBay()
    result = await agent_bay.create()

    if result.success:
        session = result.session

        # Execute command
        cmd_result = await session.command.execute_command("ls -la")
        print(cmd_result.output)

        # File operations
        await session.file_system.write_file("/tmp/test.txt", "Hello World")
        content = await session.file_system.read_file("/tmp/test.txt")
        print(content.content)  # Hello World

        # Clean up
        await agent_bay.delete(session)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔄 Sync vs Async: Which to Choose?

AgentBay Python SDK provides both synchronous and asynchronous APIs. Choose based on your application needs:

| Feature | Sync API (`AgentBay`) | Async API (`AsyncAgentBay`) |
|---------|----------------------|----------------------------|
| **Import** | `from agentbay import AgentBay` | `from agentbay import AsyncAgentBay` |
| **Best for** | Scripts, simple tools, CLI apps | Web servers (FastAPI/Django), high-concurrency apps |
| **Blocking** | Yes, blocks thread until complete | No, allows other tasks to run |
| **Usage** | `client.create(...)` | `await client.create(...)` |
| **Concurrency** | Sequential execution | Concurrent execution with asyncio |
| **Learning Curve** | Simpler, easier to start | Requires understanding of async/await |

### When to Use Sync API

Use the synchronous API (`AgentBay`) when:

- **Simple scripts**: One-off automation tasks or data processing scripts
- **CLI tools**: Command-line applications with sequential operations
- **Learning**: Getting started with AgentBay SDK
- **Debugging**: Easier to debug with sequential execution flow

**Example Use Case**: A script that processes files sequentially

```python
from agentbay import AgentBay, CreateSessionParams

agent_bay = AgentBay()
session = agent_bay.create(CreateSessionParams(image_id="code_latest")).session

# Process files one by one
for file_path in ["/tmp/file1.txt", "/tmp/file2.txt", "/tmp/file3.txt"]:
    content = session.file_system.read_file(file_path)
    processed = content.content.upper()
    session.file_system.write_file(file_path + ".processed", processed)

agent_bay.delete(session)
```

### When to Use Async API

Use the asynchronous API (`AsyncAgentBay`) when:

- **Web applications**: FastAPI, Django, or other async web frameworks
- **High concurrency**: Managing multiple sessions or operations simultaneously
- **Performance critical**: Need to maximize throughput with I/O-bound operations
- **Real-time systems**: Applications requiring non-blocking operations

**Example Use Case**: A web server handling multiple concurrent requests

```python
import asyncio
from agentbay import AsyncAgentBay, CreateSessionParams

async def process_request(task_id: str, code: str):
    agent_bay = AsyncAgentBay()
    session = (await agent_bay.create(CreateSessionParams(image_id="code_latest"))).session

    result = await session.code.run_code(code, "python")

    await agent_bay.delete(session)
    return result

async def main():
    # Process multiple requests concurrently
    tasks = [
        process_request("task1", "print('Hello from task 1')"),
        process_request("task2", "print('Hello from task 2')"),
        process_request("task3", "print('Hello from task 3')"),
    ]

    results = await asyncio.gather(*tasks)
    for result in results:
        print(result.result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📖 Complete Documentation

### 🆕 New Users
- [📚 Quick Start Tutorial](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/quickstart/README.md) - Get started in 5 minutes
- [🎯 Core Concepts](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/quickstart/basic-concepts.md) - Understand cloud environments and sessions
- [🔄 Sync vs Async Guide](docs/guides/async-programming/sync-vs-async.md) - Detailed guide on choosing between sync and async APIs

### 🚀 Experienced Users
**Choose Your Cloud Environment:**
- 🌐 [Browser Use](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/browser-use/README.md) - Web scraping, browser testing, form automation
- 🖥️ [Computer Use](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/computer-use/README.md) - Windows desktop automation, UI testing
- 📱 [Mobile Use](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/mobile-use/README.md) - Android UI testing, mobile app automation
- 💻 [CodeSpace](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/codespace/README.md) - Code execution, development environments

**Additional Resources:**
- [📖 Feature Guides](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/README.md) - Complete feature introduction
- [🔧 Python API Reference](docs/api/README.md) - Detailed API documentation
- [💻 Python Examples](docs/examples/README.md) - Complete example code
- [📋 Logging Configuration](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/guides/common-features/configuration/logging.md) - Configure logging levels and output

## 🔧 Core Features Quick Reference

### Session Management

#### Synchronous
```python
from agentbay import AgentBay

agent_bay = AgentBay()

# Create session
result = agent_bay.create()
if result.success:
    session = result.session

# List sessions by labels with pagination
result = agent_bay.list(labels={"environment": "production"}, limit=10)
if result.success:
    session_ids = result.session_ids

# Delete session
delete_result = agent_bay.delete(session)
```

#### Asynchronous
```python
import asyncio
from agentbay import AsyncAgentBay

async def main():
    agent_bay = AsyncAgentBay()

    # Create session
    result = await agent_bay.create()
    if result.success:
        session = result.session

    # List sessions by labels with pagination
    result = await agent_bay.list(labels={"environment": "production"}, limit=10)
    if result.success:
        session_ids = result.session_ids

    # Delete session
    delete_result = await agent_bay.delete(session)

asyncio.run(main())
```

### File Operations

#### Synchronous
```python
# Read/write files
session.file_system.write_file("/path/file.txt", "content")
content = session.file_system.read_file("/path/file.txt")
print(content.content)

# List directory
files = session.file_system.list_directory("/path")
```

#### Asynchronous
```python
# Read/write files
await session.file_system.write_file("/path/file.txt", "content")
content = await session.file_system.read_file("/path/file.txt")
print(content.content)

# List directory
files = await session.file_system.list_directory("/path")
```

### Command Execution

#### Synchronous
```python
# Execute command
result = session.command.execute_command("python script.py")
print(result.output)
```

#### Asynchronous
```python
# Execute command
result = await session.command.execute_command("python script.py")
print(result.output)
```

### Code Execution

#### Synchronous
```python
from agentbay import AgentBay, CreateSessionParams

agent_bay = AgentBay()
session = agent_bay.create(CreateSessionParams(image_id="code_latest")).session

# Run Python code
result = session.code.run_code("print('Hello World')", "python")
if result.success:
    print(result.result)  # Hello World

agent_bay.delete(session)
```

#### Asynchronous
```python
import asyncio
from agentbay import AsyncAgentBay, CreateSessionParams

async def main():
    agent_bay = AsyncAgentBay()
    session = (await agent_bay.create(CreateSessionParams(image_id="code_latest"))).session

    # Run Python code
    result = await session.code.run_code("print('Hello World')", "python")
    if result.success:
        print(result.result)  # Hello World

    await agent_bay.delete(session)

asyncio.run(main())
```

### Data Persistence

#### Synchronous
```python
from agentbay import AgentBay, CreateSessionParams
from agentbay import ContextSync, SyncPolicy

agent_bay = AgentBay()

# Create context
context = agent_bay.context.get("my-project", create=True).context

# Create session with context
context_sync = ContextSync.new(context.id, "/tmp/data", SyncPolicy.default())
session = agent_bay.create(CreateSessionParams(context_syncs=[context_sync])).session

# Data in /tmp/data will be synchronized to the context
session.file_system.write_file("/tmp/data/config.json", '{"key": "value"}')

agent_bay.delete(session)
```

#### Asynchronous
```python
import asyncio
from agentbay import AsyncAgentBay, CreateSessionParams
from agentbay import ContextSync, SyncPolicy

async def main():
    agent_bay = AsyncAgentBay()

    # Create context
    context = (await agent_bay.context.get("my-project", create=True)).context

    # Create session with context
    context_sync = ContextSync.new(context.id, "/tmp/data", SyncPolicy.default())
    session = (await agent_bay.create(CreateSessionParams(context_syncs=[context_sync]))).session

    # Data in /tmp/data will be synchronized to the context
    await session.file_system.write_file("/tmp/data/config.json", '{"key": "value"}')

    await agent_bay.delete(session)

asyncio.run(main())
```

## 🆘 Get Help

- [GitHub Issues](https://github.com/aliyun/wuying-agentbay-sdk/issues)
- [Documentation](https://github.com/aliyun/wuying-agentbay-sdk/tree/main/docs/README.md)

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
