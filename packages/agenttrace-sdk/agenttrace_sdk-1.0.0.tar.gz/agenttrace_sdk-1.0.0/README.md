# AgentTrace SDK

**AI Agent Observability & Debugging** - Record, replay, and debug your AI agents.

[![PyPI version](https://badge.fury.io/py/agenttrace.svg)](https://pypi.org/project/agenttrace/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🚀 Quick Start

```bash
pip install agenttrace-sdk
```

```python
from agenttrace import AgentTrace

# Initialize with your API key
tracer = AgentTrace(api_key="at_your_api_key_here")

# Start a trace session
tracer.start("my_agent.py")

# Record agent activities
tracer.thought("Analyzing the user's request...")
tracer.tool_start("web_search", {"query": "latest AI news"})
tracer.tool_end("web_search", {"results": [...]})

# End the session
tracer.end()
```

## 📋 Features

- **📍 Event Recording** - Capture thoughts, tool calls, file writes, and exceptions
- **🔄 Replay Execution** - Re-run your agent with deterministic results
- **🌿 Branch & Fork** - Create alternate timelines from any point
- **🔍 Compare Runs** - Side-by-side diff of different executions
- **🛠️ AutoFix Engine** - AI-powered error detection and fixes

## 🔧 API Reference

### Initialize Client

```python
from agenttrace import AgentTrace

tracer = AgentTrace(
    api_key="at_xxx...",                    # Your API key (required)
    endpoint="https://app.agenttrace.io",   # API endpoint (optional)
    batch_size=10,                          # Events before auto-flush
    flush_interval=1.0                      # Seconds between flushes
)
```

### Record Events

```python
# Record a thought/reasoning step
tracer.thought("Planning the next action...")

# Record tool invocation
tracer.tool_start("calculator", {"expression": "2+2"})
tracer.tool_end("calculator", result=4)

# Record file operations
tracer.file_write("/path/to/file.txt", "content here")

# Record exceptions
tracer.exception("ValueError", "Invalid input", traceback_str)
```

### Context Manager

```python
with tracer.session("my_script.py") as trace_id:
    tracer.thought("Starting...")
    # Your agent code here
    # Automatically ends with status "completed" or "failed"
```

### Decorator

```python
from agenttrace import trace

@trace
def my_function(x, y):
    return x + y  # Automatically traced!
```

## 🔑 Get Your API Key

1. Sign up at [agenttrace.io](https://agenttrace.io)
2. Go to Settings → API Keys
3. Create a new key
4. Copy and use in your code

```python
# Or set via environment variable
export AGENTTRACE_API_KEY="at_your_key_here"

# Then just:
tracer = AgentTrace()  # Auto-reads from env
```

## 📊 View Your Traces

After recording, view your traces at:
- **Dashboard**: `https://app.agenttrace.io/dashboard/traces`
- **Individual Trace**: `https://app.agenttrace.io/trace/{trace_id}`

## 🌐 Self-Hosted

For self-hosted deployments:

```python
tracer = AgentTrace(
    api_key="at_xxx...",
    endpoint="https://your-domain.com"  # Your self-hosted instance
)
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Website**: [agenttrace.io](https://agenttrace.io)
- **Documentation**: [docs.agenttrace.io](https://docs.agenttrace.io)
- **Support**: agenttraceismoat@gmail.com
