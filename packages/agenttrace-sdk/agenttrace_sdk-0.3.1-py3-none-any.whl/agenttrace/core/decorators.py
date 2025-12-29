from functools import wraps
import time
from .tracer import Tracer

def step(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = Tracer.get_instance()
            tracer.record_event("step_start", {"name": name})
            try:
                result = func(*args, **kwargs)
                tracer.record_event("step_end", {"name": name})
                return result
            except Exception as e:
                tracer.record_event("step_failed", {"name": name, "error": str(e)})
                raise
        return wrapper
    return decorator


def tool(func):
    """Decorator for tracking tool calls with latency measurement."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracer = Tracer.get_instance()
        tool_name = func.__name__
        start_time = time.perf_counter()
        
        # Record the invocation
        tracer.record_event("tool_invocation", {
            "tool": tool_name, 
            "args": str(args), 
            "kwargs": str(kwargs)
        })
        
        # What-If Event Injection: Atomic check + consume + record
        injected, result = tracer.try_consume_injected_result(tool_name)
        if injected:
            return result
        
        # Normal execution with latency tracking
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            tracer.record_event("tool_end", {
                "tool": tool_name, 
                "result": str(result),
                "latency_ms": round(latency_ms, 2)
            })
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            tracer.record_event("tool_failed", {
                "tool": tool_name, 
                "error": str(e),
                "latency_ms": round(latency_ms, 2)
            })
            raise
    return wrapper


# Token pricing per 1M tokens (USD) - configurable
LLM_PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "default": {"input": 1.0, "output": 3.0}
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a given model and token counts."""
    pricing = LLM_PRICING.get(model, LLM_PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def llm_tool(model: str = "default"):
    """Decorator for LLM calls with token and cost tracking.
    
    Usage:
        @llm_tool(model="gpt-4o")
        def call_llm(prompt: str) -> dict:
            response = openai.chat(prompt)
            return {
                "content": response.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
    
    The decorated function should return a dict with:
    - content: The LLM response
    - input_tokens: Number of input tokens
    - output_tokens: Number of output tokens
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = Tracer.get_instance()
            tool_name = func.__name__
            start_time = time.perf_counter()
            
            # Record invocation
            tracer.record_event("llm_invocation", {
                "tool": tool_name,
                "model": model,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            
            # What-If injection check
            injected, result = tracer.try_consume_injected_result(tool_name)
            if injected:
                return result
            
            # Execute LLM call
            try:
                result = func(*args, **kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # FIX 3.4: Warn if result is not in expected format
                if not isinstance(result, dict):
                    print(f"[AgentTrace] Warning: @llm_tool expects dict return, got {type(result).__name__}")
                    tracer.record_event("llm_end", {
                        "tool": tool_name,
                        "model": model,
                        "result": str(result),
                        "latency_ms": round(latency_ms, 2),
                        "warning": "Non-dict return, cost tracking disabled"
                    })
                    return result
                
                # Extract token counts from result
                input_tokens = result.get("input_tokens", 0)
                output_tokens = result.get("output_tokens", 0)
                
                if input_tokens == 0 and output_tokens == 0:
                    print(f"[AgentTrace] Warning: @llm_tool missing token counts, cost tracking disabled")
                
                total_tokens = input_tokens + output_tokens
                cost_usd = calculate_cost(model, input_tokens, output_tokens)
                
                tracer.record_event("llm_end", {
                    "tool": tool_name,
                    "model": model,
                    "result": str(result.get("content", result) if isinstance(result, dict) else result),
                    "latency_ms": round(latency_ms, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": cost_usd
                })
                
                return result
            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                tracer.record_event("llm_failed", {
                    "tool": tool_name,
                    "model": model,
                    "error": str(e),
                    "latency_ms": round(latency_ms, 2)
                })
                raise
        return wrapper
    return decorator


def trace(func):
    """Decorator for tracking function execution with latency."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracer = Tracer.get_instance()
        name = func.__name__
        start_time = time.perf_counter()
        
        tracer.record_event("function_start", {
            "name": name, 
            "args": str(args), 
            "kwargs": str(kwargs)
        })
        
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            tracer.record_event("function_end", {
                "name": name, 
                "result": str(result),
                "latency_ms": round(latency_ms, 2)
            })
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            tracer.record_event("function_failed", {
                "name": name, 
                "error": str(e),
                "latency_ms": round(latency_ms, 2)
            })
            raise
    return wrapper
