"""
AgentTrace Slim Client
Minimal SDK that sends events to AgentTrace backend - NO core logic exposed.
"""

import requests
import time
import threading
import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


class AgentTrace:
    """
    Thin AgentTrace client that sends events to the cloud backend.
    
    All processing, analysis, and intelligence happens server-side.
    This client only handles:
    - API authentication
    - Event batching and sending
    - Basic instrumentation hooks
    """
    
    DEFAULT_ENDPOINT = "https://app.agenttrace.io"
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 1.0
    ):
        """
        Initialize AgentTrace client.
        
        Args:
            api_key: Your AgentTrace API key (or set AGENTTRACE_API_KEY env var)
            endpoint: API endpoint (default: https://app.agenttrace.io)
            batch_size: Number of events to buffer before sending
            flush_interval: Seconds between automatic flushes
        """
        self.api_key = api_key or os.environ.get("AGENTTRACE_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Pass api_key= or set AGENTTRACE_API_KEY")
        
        self.endpoint = endpoint or os.environ.get("AGENTTRACE_ENDPOINT", self.DEFAULT_ENDPOINT)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # State
        self.trace_id: Optional[str] = None
        self.seq = 0
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        self._started = False
    
    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def start(self, script_name: str, metadata: Optional[Dict] = None) -> str:
        """
        Start a new trace session.
        
        Args:
            script_name: Name of the script being traced
            metadata: Optional metadata (project_id, tags, etc.)
        
        Returns:
            trace_id: The unique trace ID
        """
        if self._started:
            raise RuntimeError("Trace already started. Call end() first.")
        
        response = requests.post(
            f"{self.endpoint}/api/sdk/trace/start",
            headers=self._headers(),
            json={
                "script_name": script_name,
                "metadata": metadata or {}
            }
        )
        
        if not response.ok:
            raise RuntimeError(f"Failed to start trace: {response.text}")
        
        data = response.json()
        self.trace_id = data["trace_id"]
        self.seq = 0
        self._started = True
        self._buffer = []
        
        # Record trace_start event
        self.record("trace_start", {
            "script": script_name,
            "timestamp": time.time()
        })
        
        # Start flush timer
        self._start_flush_timer()
        
        return self.trace_id
    
    def record(self, event_type: str, payload: Optional[Dict] = None) -> int:
        """
        Record an event.
        
        Args:
            event_type: Type of event (thought, tool_call, file_write, etc.)
            payload: Event data
        
        Returns:
            seq: The sequence number of this event
        """
        if not self._started:
            raise RuntimeError("Trace not started. Call start() first.")
        
        with self._lock:
            self.seq += 1
            event = {
                "trace_id": self.trace_id,
                "seq": self.seq,
                "type": event_type,
                "payload": payload or {},
                "timestamp": time.time()
            }
            self._buffer.append(event)
            
            current_seq = self.seq
        
        # Flush if buffer is full
        if len(self._buffer) >= self.batch_size:
            self._flush()
        
        return current_seq
    
    def thought(self, content: str, reasoning: Optional[str] = None) -> int:
        """Record an agent thought/reasoning step."""
        return self.record("thought", {
            "content": content,
            "reasoning": reasoning
        })
    
    def tool_start(self, tool_name: str, args: Optional[Dict] = None) -> int:
        """Record tool invocation start."""
        return self.record("tool_invocation", {
            "name": tool_name,
            "args": args or {}
        })
    
    def tool_end(self, tool_name: str, result: Any, error: Optional[str] = None) -> int:
        """Record tool invocation end."""
        return self.record("tool_end", {
            "name": tool_name,
            "result": str(result)[:10000] if result else None,  # Truncate large results
            "error": error
        })
    
    def file_write(self, path: str, content: str, is_binary: bool = False) -> int:
        """Record a file write operation."""
        return self.record("file_write", {
            "path": path,
            "content": content[:50000] if not is_binary else "<binary>",
            "size": len(content),
            "is_binary": is_binary
        })
    
    def exception(self, error_type: str, message: str, traceback: Optional[str] = None) -> int:
        """Record an exception."""
        return self.record("python_exception", {
            "error_type": error_type,
            "message": message,
            "traceback": traceback
        })
    
    def _start_flush_timer(self):
        """Start background flush timer."""
        if self._flush_timer:
            self._flush_timer.cancel()
        self._flush_timer = threading.Timer(self.flush_interval, self._auto_flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()
    
    def _auto_flush(self):
        """Auto-flush callback."""
        if self._started and self._buffer:
            self._flush()
        if self._started:
            self._start_flush_timer()
    
    def _flush(self):
        """Send buffered events to server."""
        with self._lock:
            if not self._buffer:
                return
            events_to_send = self._buffer.copy()
            self._buffer = []
        
        # Send each event (could optimize with batch endpoint)
        for event in events_to_send:
            try:
                response = requests.post(
                    f"{self.endpoint}/api/sdk/trace/event",
                    headers=self._headers(),
                    json=event,
                    timeout=5
                )
                if not response.ok:
                    print(f"[AgentTrace] Event send failed: {response.text}")
            except Exception as e:
                print(f"[AgentTrace] Event send error: {e}")
    
    def end(self, status: str = "completed") -> Dict[str, Any]:
        """
        End the trace session.
        
        Args:
            status: Final status (completed, failed, cancelled)
        
        Returns:
            Summary of the trace
        """
        if not self._started:
            raise RuntimeError("Trace not started.")
        
        # Record trace_end event
        self.record("trace_end", {
            "status": status,
            "timestamp": time.time()
        })
        
        # Flush remaining events
        self._flush()
        
        # Stop timer
        if self._flush_timer:
            self._flush_timer.cancel()
        
        # Finalize on server
        response = requests.post(
            f"{self.endpoint}/api/sdk/trace/end",
            headers=self._headers(),
            json={
                "trace_id": self.trace_id,
                "status": status
            }
        )
        
        self._started = False
        
        if not response.ok:
            raise RuntimeError(f"Failed to end trace: {response.text}")
        
        return response.json()
    
    @contextmanager
    def session(self, script_name: str, metadata: Optional[Dict] = None):
        """
        Context manager for trace sessions.
        
        Usage:
            tracer = AgentTrace(api_key="...")
            with tracer.session("my_script.py") as trace_id:
                tracer.thought("Working...")
        """
        try:
            trace_id = self.start(script_name, metadata)
            yield trace_id
            self.end("completed")
        except Exception as e:
            self.exception(type(e).__name__, str(e))
            self.end("failed")
            raise


# Global instance for simple use
_global_tracer: Optional[AgentTrace] = None

def get_tracer() -> AgentTrace:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = AgentTrace()
    return _global_tracer

def init(api_key: Optional[str] = None, **kwargs):
    """Initialize the global tracer."""
    global _global_tracer
    _global_tracer = AgentTrace(api_key=api_key, **kwargs)
    return _global_tracer
