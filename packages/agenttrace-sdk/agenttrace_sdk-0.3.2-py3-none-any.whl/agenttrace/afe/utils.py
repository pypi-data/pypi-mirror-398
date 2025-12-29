from typing import List, Dict, Any

def format_trace_context(trace_steps: List[Dict[str, Any]], max_steps: int = 10) -> str:
    """
    Formats trace steps into a concise string for LLM context.
    Includes the last `max_steps` steps.
    """
    if not trace_steps:
        return "No trace steps available."

    # Take the last N steps
    recent_steps = trace_steps[-max_steps:]
    
    formatted = []
    for i, step in enumerate(recent_steps):
        step_type = step.get("type", "unknown")
        name = step.get("name", "unnamed")
        status = step.get("status", "unknown")
        error = step.get("error", "")
        
        # Basic info
        entry = f"Step {i+1}: [{step_type}] {name} ({status})"
        
        # Add input/output snippet if available (truncated)
        if "input" in step:
            inp = str(step["input"])[:100]
            entry += f"\n  Input: {inp}..."
            
        if "output" in step:
            out = str(step["output"])[:100]
            entry += f"\n  Output: {out}..."
            
        if error:
            entry += f"\n  ERROR: {error}"
            
        # Add rich context for error events
        if "payload" in step and (step_type == "error" or "exception" in step_type.lower()):
            payload = step["payload"]
            if isinstance(payload, dict):
                if "locals" in payload:
                    entry += f"\n  LOCALS: {str(payload['locals'])[:500]}..."
                if "globals" in payload:
                    entry += f"\n  GLOBALS: {str(payload['globals'])[:500]}..."
            
        formatted.append(entry)
        
    return "\n\n".join(formatted)
