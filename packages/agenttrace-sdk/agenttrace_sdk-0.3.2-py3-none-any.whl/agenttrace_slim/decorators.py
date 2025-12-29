"""
Decorators for automatic function tracing.
"""

import functools
import time
from typing import Callable, Optional
from .client import get_tracer, AgentTrace


def trace(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    tracer: Optional[AgentTrace] = None
):
    """
    Decorator to trace function calls.
    
    Usage:
        @trace
        def my_function(x, y):
            return x + y
        
        # Or with custom name
        @trace(name="custom_name")
        def my_function(x, y):
            return x + y
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t = tracer or get_tracer()
            fn_name = name or fn.__name__
            
            start_time = time.time()
            t.tool_start(fn_name, {"args": str(args)[:500], "kwargs": str(kwargs)[:500]})
            
            try:
                result = fn(*args, **kwargs)
                duration = time.time() - start_time
                t.tool_end(fn_name, result)
                return result
            except Exception as e:
                duration = time.time() - start_time
                t.tool_end(fn_name, None, error=str(e))
                raise
        
        return wrapper
    
    # Handle both @trace and @trace() syntax
    if func is not None:
        return decorator(func)
    return decorator


def trace_async(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    tracer: Optional[AgentTrace] = None
):
    """
    Decorator to trace async function calls.
    
    Usage:
        @trace_async
        async def my_async_function():
            await some_io()
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            t = tracer or get_tracer()
            fn_name = name or fn.__name__
            
            start_time = time.time()
            t.tool_start(fn_name, {"args": str(args)[:500], "kwargs": str(kwargs)[:500]})
            
            try:
                result = await fn(*args, **kwargs)
                duration = time.time() - start_time
                t.tool_end(fn_name, result)
                return result
            except Exception as e:
                duration = time.time() - start_time
                t.tool_end(fn_name, None, error=str(e))
                raise
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator
