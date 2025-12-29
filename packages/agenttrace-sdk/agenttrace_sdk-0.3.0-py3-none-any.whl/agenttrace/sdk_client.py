# agenttrace/sdk_client.py
"""
AgentTrace SDK Client - Simple API-key based cloud sync.

Users only need to set AGENTTRACE_API_KEY to use cloud features.
All trace data including scripts will be automatically synced.
"""

import os
import json
import requests
from typing import Optional, Dict, Any

# Default API endpoint (can be overridden)
DEFAULT_API_URL = "https://moat-kappa.vercel.app/api"


class AgentTraceClient:
    """
    Client for syncing traces to AgentTrace cloud.
    
    Usage:
        client = AgentTraceClient()  # Uses AGENTTRACE_API_KEY env var
        trace_id = client.start_trace("my_script.py")
        client.send_event(trace_id, "tool_end", {"tool": "search", "result": "..."})
        client.end_trace(trace_id, script_content="...")
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AGENTTRACE_API_KEY")
        self.api_url = api_url or os.environ.get("AGENTTRACE_API_URL", DEFAULT_API_URL)
        
        if not self.api_key:
            raise ValueError(
                "AgentTrace API key not found. "
                "Set AGENTTRACE_API_KEY environment variable or pass api_key parameter."
            )
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to API."""
        url = f"{self.api_url}{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[AgentTrace] API error: {e}")
            raise
    
    def start_trace(self, script_name: str, metadata: Optional[Dict] = None) -> str:
        """Start a new trace session.
        
        Returns:
            trace_id: UUID of the created trace
        """
        result = self._request("POST", "/sdk/trace/start", {
            "script_name": script_name,
            "metadata": metadata or {}
        })
        return result["trace_id"]
    
    def send_event(self, trace_id: str, event_type: str, payload: Dict) -> bool:
        """Send an event to the trace.
        
        Args:
            trace_id: UUID of the trace
            event_type: Type of event (e.g., "tool_end", "llm_response")
            payload: Event data
            
        Returns:
            success: Whether the event was recorded
        """
        try:
            result = self._request("POST", "/sdk/trace/event", {
                "trace_id": trace_id,
                "type": event_type,
                "payload": payload
            })
            return result.get("success", False)
        except Exception:
            return False
    
    def end_trace(
        self, 
        trace_id: str, 
        status: str = "completed",
        script_content: Optional[str] = None
    ) -> Dict:
        """End a trace session and finalize upload.
        
        IMPORTANT: Include script_content for Replay to work!
        
        Args:
            trace_id: UUID of the trace
            status: Final status ("completed" or "failed")
            script_content: Content of the Python script (required for Replay)
            
        Returns:
            result: API response with total_events count
        """
        return self._request("POST", "/sdk/trace/end", {
            "trace_id": trace_id,
            "status": status,
            "script_content": script_content
        })


# Convenience function for simple usage
def init(api_key: Optional[str] = None) -> AgentTraceClient:
    """Initialize AgentTrace client with API key.
    
    Example:
        import agenttrace
        client = agenttrace.init()  # Uses AGENTTRACE_API_KEY env var
    """
    return AgentTraceClient(api_key=api_key)
