import asyncio
import sys
import functools
from agenttrace.core.tracer import Tracer, Mode

_original_new_event_loop = asyncio.new_event_loop
_original_run = asyncio.run

def _task_factory_wrapper(loop, coro, context=None):
    """
    Custom task factory to intercept task creation.
    """
    tracer = Tracer.get_instance()
    
    # Only instrument in RECORD mode
    if tracer.mode != Mode.RECORD:
        return asyncio.tasks.Task(coro, loop=loop, context=context)

    # 1. Assign ID and Record SPAWN
    # We need a predictable sequence for tasks.
    # Note: This might be called from multiple threads if we are not careful, 
    # but asyncio loops are single threaded. 
    # Tracer is thread-safe-ish (locks).
    
    # We trust the tracer's event sequence to be the deterministic identity mechanism?
    # Or should we maintain a separate task counter?
    # Let's use a task counter stored on the loop if possible, or global.
    if not hasattr(loop, "_agenttrace_task_counter"):
        loop._agenttrace_task_counter = 0
    
    task_id = loop._agenttrace_task_counter
    loop._agenttrace_task_counter += 1
    
    tid = f"T-{task_id}"
    
    # Record Spawn
    # We use disable_instrumentation to avoid recursion if we were patching other things called here
    tracer.record_event("async_task_spawn", {
        "task_id": tid,
        "coro_name": getattr(coro, "__name__", str(coro))
    })
    
    # 2. Wrap Coroutine to Record START / END
    async def _wrapped_coro():
        tracer.record_event("async_task_start", {"task_id": tid})
        try:
            result = await coro
            tracer.record_event("async_task_complete", {"task_id": tid, "status": "success"})
            return result
        except BaseException as e:
            tracer.record_event("async_task_complete", {"task_id": tid, "status": "failed", "error": str(e)})
            raise e

    # Create the task with wrapped coro
    task = asyncio.tasks.Task(_wrapped_coro(), loop=loop, context=context)
    task.set_name(tid) # Set standard asyncio name too
    return task

def patch_asyncio():
    """
    Patches asyncio to install the deterministic task factory.
    """
    
    # 1. Patch new_event_loop to install factory immediately
    def _patched_new_event_loop():
        loop = _original_new_event_loop()
        loop.set_task_factory(_task_factory_wrapper)
        return loop
    
    asyncio.new_event_loop = _patched_new_event_loop
    
    # 2. Patch asyncio.run because it might create a loop internally using a policy
    # Although typically it calls new_event_loop, some implementations might optimized.
    # Wrapping it ensures we touch the loop before the user coro runs.
    def _patched_run(main, *, debug=None):
        # Wrap the main coroutine to install the factory on the active loop
        async def _wrapper(c):
            loop = asyncio.get_running_loop()
            loop.set_task_factory(_task_factory_wrapper)
            return await c
            
        # Check if main is a coroutine or awaitable
        if asyncio.iscoroutine(main):
             return _original_run(_wrapper(main), debug=debug)
        else:
             # handle edge cases if any
             return _original_run(main, debug=debug)

    asyncio.run = _patched_run
    
    # 3. Patch current loop if exists
    try:
        loop = asyncio.get_event_loop()
        loop.set_task_factory(_task_factory_wrapper)
    except RuntimeError:
        pass # No current loop
        
    print("AgentTrace: AsyncIO Instrumented (Task Factory)")

