import importlib
import sys
import os
import io
from unittest.mock import MagicMock
from agenttrace.core.tracer import Tracer, Mode

# Try to import openai
try:
    import openai
except ImportError:
    openai = None

# Try to import groq
try:
    import groq
except ImportError:
    groq = None

import random
import time as time_module
from datetime import datetime

# In-memory file system for REPLAY mode
_vfs_files = {}
_original_open = None
_original_os_path_exists = None
_original_os_path_isfile = None
_original_os_listdir = None

# Time travel state
_original_start_time = None
_original_datetime_now = None
_original_time_time = None

def reset_patch_state():
    """Reset all global patch state. Call between trace executions to prevent leakage."""
    global _original_start_time, _original_datetime_now, _original_time_time, _vfs_files
    _original_start_time = None
    _original_datetime_now = None
    _original_time_time = None
    _vfs_files = {}  # Also reset VFS cache


def patch_openai():
    if not openai:
        return

    # ---------------------------------------------------------
    # 1. Synchronous Patch
    # ---------------------------------------------------------
    original_create = openai.resources.chat.Completions.create

    def wrapped_create(*args, **kwargs):
        tracer = Tracer.get_instance()
        is_stream = kwargs.get("stream", False)
        
        if tracer.mode == Mode.RECORD:
            print(f"AgentTrace: Calling real OpenAI API (Sync, Stream={is_stream})...")
            
            # Call original safely
            with tracer.disable_instrumentation():
                response = original_create(*args, **kwargs)
            
            # Handle Streaming
            if is_stream:
                def _stream_wrapper(gen):
                    full_content = []
                    stream_timing = []
                    last_time = time_module.time()

                    try:
                        for chunk in gen:
                            current_time = time_module.time()
                            # Accumulate
                            if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                full_content.append(content)
                                stream_timing.append({
                                    "c": content,
                                    "d": int((current_time - last_time) * 1000) # delay in ms
                                })
                                last_time = current_time
                            yield chunk
                    finally:
                        # Record full message after stream ends
                        output_str = "".join(full_content)
                        print(f"DEBUG: Recording stream event. Tracer ID: {id(tracer)}")
                        res = tracer.record_event("openai_completion", {
                            "inputs": str(kwargs),
                            "output": {"choices": [{"message": {"content": output_str, "role": "assistant"}}]},
                            "is_stream": True,
                            "stream_timing": stream_timing
                        })
                        print(f"DEBUG: record_event result: {res}")
                
                return _stream_wrapper(response)

            # Handle Normal
            try:
                response_dict = response.model_dump()
            except AttributeError:
                response_dict = response
            
            tracer.record_event("openai_completion", {
                "inputs": str(kwargs),
                "output": response_dict,
                "is_stream": False
            })
            return response

        elif tracer.mode == Mode.REPLAY:
            print("AgentTrace: Intercepting OpenAI call (REPLAY)...")
            cached_payload = tracer.get_next_replay_event("openai_completion")
            
            if cached_payload:
                output = cached_payload["output"]
                is_stream_record = cached_payload.get("is_stream", False)
                
                # If original was stream, we must simulate a stream response
                if is_stream or is_stream_record:
                    from openai.types.chat import ChatCompletionChunk
                    from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
                    
                    content = output["choices"][0]["message"]["content"]
                    
                    def _fake_stream():
                        # Yield one big chunk for simplicity, or chunk it up
                        # Ideally we mimic the chunks, but one chunk is functionally fine for most consumers
                        yield ChatCompletionChunk(
                            id="replay-id",
                            object="chat.completion.chunk",
                            created=int(time_module.time()),
                            model="replay-model",
                            choices=[
                                Choice(
                                    index=0,
                                    delta=ChoiceDelta(content=content, role="assistant"),
                                    finish_reason="stop"
                                )
                            ]
                        )
                    return _fake_stream()

                from openai.types.chat import ChatCompletion
                return ChatCompletion(**output)
            else:
                raise RuntimeError("Replay divergence: Missing OpenAI response in log")
        else:
            return original_create(*args, **kwargs)

    openai.resources.chat.Completions.create = wrapped_create
    
    # ---------------------------------------------------------
    # 2. Asynchronous Patch
    # ---------------------------------------------------------
    if hasattr(openai.resources.chat, 'AsyncCompletions'):
        original_async_create = openai.resources.chat.AsyncCompletions.create

        async def wrapped_async_create(*args, **kwargs):
            tracer = Tracer.get_instance()
            is_stream = kwargs.get("stream", False)
            
            if tracer.mode == Mode.RECORD:
                print(f"AgentTrace: Calling real AsyncOpenAI API (Stream={is_stream})...")
                
                with tracer.disable_instrumentation():
                    response = await original_async_create(*args, **kwargs)
                
                if is_stream:
                    async def _async_stream_wrapper(gen):
                        full_content = []
                        try:
                            async for chunk in gen:
                                if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                                    full_content.append(chunk.choices[0].delta.content)
                                yield chunk
                        finally:
                            output_str = "".join(full_content)
                            tracer.record_event("openai_completion", {
                                "inputs": str(kwargs),
                                "output": {"choices": [{"message": {"content": output_str, "role": "assistant"}}]},
                                "is_stream": True,
                                "is_async": True
                            })
                    return _async_stream_wrapper(response)
                
                # Normal Async
                try:
                    response_dict = response.model_dump()
                except AttributeError:
                    response_dict = response
                    
                tracer.record_event("openai_completion", {
                    "inputs": str(kwargs),
                    "output": response_dict,
                    "is_stream": False,
                    "is_async": True
                })
                return response

            elif tracer.mode == Mode.REPLAY:
                print("AgentTrace: Intercepting AsyncOpenAI call (REPLAY)...")
                cached_payload = tracer.get_next_replay_event("openai_completion")
                
                if cached_payload:
                    output = cached_payload["output"]
                    is_stream_record = cached_payload.get("is_stream", False)
                    
                    if is_stream or is_stream_record:
                        from openai.types.chat import ChatCompletionChunk
                        from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
                        
                        content = output["choices"][0]["message"]["content"]
                        
                        async def _fake_async_stream():
                            yield ChatCompletionChunk(
                                id="replay-id",
                                object="chat.completion.chunk",
                                created=int(time_module.time()),
                                model="replay-model",
                                choices=[
                                    Choice(
                                        index=0,
                                        delta=ChoiceDelta(content=content, role="assistant"),
                                        finish_reason="stop"
                                    )
                                ]
                            )
                        return _fake_async_stream()

                    from openai.types.chat import ChatCompletion
                    return ChatCompletion(**output)
                else:
                    raise RuntimeError("Replay divergence: Missing AsyncOpenAI response in log")
            else:
                return await original_async_create(*args, **kwargs)

        openai.resources.chat.AsyncCompletions.create = wrapped_async_create

    print("AgentTrace: OpenAI (Sync+Async) Instrumented")

def patch_groq():
    if not groq:
        return

    original_create = groq.resources.chat.Completions.create

    def wrapped_create(*args, **kwargs):
        tracer = Tracer.get_instance()
        
        if tracer.mode == Mode.RECORD:
            print("AgentTrace: Calling real Groq API...")
            
            # Call original safely
            with tracer.disable_instrumentation():
                response = original_create(*args, **kwargs)
            
            try:
                response_dict = response.model_dump()
            except AttributeError:
                response_dict = response
            
            tracer.record_event("groq_completion", {
                "inputs": str(kwargs),
                "output": response_dict
            })
            return response

        elif tracer.mode == Mode.REPLAY:
            print("AgentTrace: Intercepting Groq call (REPLAY)...")
            cached_payload = tracer.get_next_replay_event("groq_completion")
            
            if cached_payload:
                from groq.types.chat import ChatCompletion
                return ChatCompletion(**cached_payload["output"])
            else:
                raise RuntimeError("Replay divergence: Missing Groq response in log")
        else:
            return original_create(*args, **kwargs)

    groq.resources.chat.Completions.create = wrapped_create
    print("AgentTrace: Groq Instrumented")

def patch_random():
    original_random = random.random

    def wrapped_random():
        tracer = Tracer.get_instance()

        if tracer.mode == Mode.RECORD:
            with tracer.disable_instrumentation():
                val = original_random()
            tracer.record_event("random", val)
            return val

        elif tracer.mode == Mode.REPLAY:
            val = tracer.get_next_replay_event("random")
            if val is None:
                return original_random()
            return val
            
        else:
            return original_random()

    random.random = wrapped_random
    print("AgentTrace: Randomness Instrumented")

def patch_time():
    """Intercept time.time() to make it deterministic during replay"""
    global _original_time_time, _original_start_time
    
    # Capture original in local variable for closure safety
    original_time = time_module.time
    _original_time_time = original_time
    
    def wrapped_time():
        global _original_start_time
        tracer = Tracer.get_instance()
        
        if tracer.mode == Mode.RECORD:
            # Record the actual time safely
            with tracer.disable_instrumentation():
                real_time = original_time()
            
            # Record start time on first call
            if _original_start_time is None:
                _original_start_time = real_time
                tracer.record_event("time_start", {"start_time": real_time})
            
            # Record the time value
            elapsed = real_time - _original_start_time
            tracer.record_event("time_call", {"elapsed": elapsed})
            return real_time
        
        elif tracer.mode == Mode.REPLAY:
            # Replay: return fake time based on original start + elapsed
            if _original_start_time is None:
                # Try to get start time from trace
                start_event = None
                for event in tracer.event_log:
                    if event.get("type") == "time_start":
                        start_event = event
                        break
                
                if start_event:
                    _original_start_time = start_event["payload"]["start_time"]
                else:
                    # Fallback: use current time (not ideal, but won't crash)
                    _original_start_time = _original_time_time()
            
            # Get elapsed time from trace
            elapsed = 0
            time_event = tracer.get_next_replay_event("time_call")
            if time_event:
                elapsed = time_event.get("elapsed", 0)
            
            return _original_start_time + elapsed
        
        else:
            return _original_time_time()
    
    time_module.time = wrapped_time
    print("AgentTrace: Time Instrumented")

def patch_datetime():
    """Intercept datetime.now() by replacing the datetime class in sys.modules"""
    import datetime as datetime_module
    
    original_datetime_class = datetime_module.datetime
    
    class PatchedDateTime(original_datetime_class):
        @staticmethod
        def now(tz=None):
            global _original_start_time
            tracer = Tracer.get_instance()
            
            if tracer.mode == Mode.RECORD:
                # Record actual datetime
                real_now = original_datetime_class.now(tz=tz)
                timestamp = real_now.timestamp()
                tracer.record_event("datetime_now", {
                    "timestamp": timestamp,
                    "tz": str(tz) if tz else None
                })
                return real_now
            
            elif tracer.mode == Mode.REPLAY:
                # Replay: get recorded timestamp
                cached = tracer.get_next_replay_event("datetime_now")
                if cached and isinstance(cached, dict) and "timestamp" in cached:
                    timestamp = cached["timestamp"]
                    return original_datetime_class.fromtimestamp(timestamp, tz=tz)
                else:
                    # Fallback if no cached value - use time-based estimation
                    if _original_start_time is None:
                        start_event = None
                        for event in tracer.event_log:
                            if event.get("type") == "time_start":
                                start_event = event
                                break
                        if start_event:
                            _original_start_time = start_event["payload"]["start_time"]
                        else:
                            _original_start_time = _original_time_time()
                    
                    # Estimate elapsed from cursor position
                    elapsed = tracer.replay_cursor * 0.1  # Rough estimate
                    return original_datetime_class.fromtimestamp(_original_start_time + elapsed, tz=tz)
            
            else:
                return original_datetime_class.now(tz=tz)
        
        @classmethod
        def today(cls):
            return cls.now().date()
        
        @classmethod
        def utcnow(cls):
            return cls.now(tz=None)
    
    # Copy all attributes from original datetime to our patched version
    for attr in dir(original_datetime_class):
        if not attr.startswith('_') and not hasattr(PatchedDateTime, attr):
            try:
                setattr(PatchedDateTime, attr, getattr(original_datetime_class, attr))
            except (TypeError, AttributeError):
                pass  # Some attributes can't be copied
    
    # Replace datetime in the module
    datetime_module.datetime = PatchedDateTime
    
    # Also replace in sys.modules for any modules that already imported it
    for module_name, module in sys.modules.items():
        if hasattr(module, 'datetime') and module.datetime is original_datetime_class:
            module.datetime = PatchedDateTime
    
    print("AgentTrace: DateTime Instrumented")

_PATCHES_APPLIED = False

def apply_patches():
    global _PATCHES_APPLIED
    if _PATCHES_APPLIED:
        print("AgentTrace: Patches already applied, skipping.")
        return

    patch_openai()
    patch_groq()
    patch_random()
    # patch_time() # Too noisy for asyncio!

    
    _PATCHES_APPLIED = True
    patch_datetime()
    
    # New VFS Patching
    from agenttrace.instrumentation.fs_patch import patch_fs
    patch_fs()

    # Async Patching
    from agenttrace.instrumentation.async_patch import patch_asyncio
    patch_asyncio()
