"""
AgentTrace Slim SDK
A minimal, secure SDK for AgentTrace that keeps core logic on the server.

Usage:
    from agenttrace_slim import AgentTrace
    
    tracer = AgentTrace(api_key="at_xxxx...")
    tracer.start("my_script.py")
    tracer.thought("Planning the task...")
    tracer.record("tool_call", {"name": "search", "args": ["query"]})
    tracer.end()
"""

__version__ = "1.0.0"

from .client import AgentTrace
from .decorators import trace

__all__ = ["AgentTrace", "trace", "__version__"]
