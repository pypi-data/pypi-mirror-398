import os
from agenttrace.instrumentation.patch import apply_patches
from agenttrace.core.tracer import Tracer
from agenttrace.runtime.exceptions import install_exception_hook
from agenttrace.runtime.state_restorer import install_state_restorer
from agenttrace.branches import storage as branch_storage

def bootstrap():
    # Check environment variables to decide if we should auto-start recording
    # e.g. AGENTTRACE_MODE=RECORD
    
    mode = os.environ.get("AGENTTRACE_MODE", "").upper()
    trace_id = os.environ.get("AGENTTRACE_ID")

    if mode or trace_id:
        print(f"AgentTrace: Bootstrap active (Mode: {mode})")
        tracer = Tracer.get_instance()
        
        # Set mode FIRST, then apply patches (patches check the mode)
        restore_state = None

        branch_data = None

        if mode == "RECORD":
            # Preserve script info if already set
            script_path = tracer.script_path
            script_content = tracer.script_content
            tracer.start_recording(script_path=script_path, script_content=script_content, trace_id=trace_id)
            install_exception_hook()
            print("AgentTrace: Exception Interceptor Active")
        elif mode == "REPLAY" and trace_id:
            target_step = os.environ.get("AGENTTRACE_STEP")
            target_step = int(target_step) if target_step else None

            branch_id = os.environ.get("AGENTTRACE_BRANCH")
            if branch_id:
                try:
                    branch_data = branch_storage.load_branch(branch_id)
                except Exception as e:
                    print(f"AgentTrace: Failed to load branch {branch_id}: {e}")
                    branch_data = None

            if branch_data and target_step is None:
                target_step = branch_data.get("fork_step")

            tracer.start_replay(trace_id, target_step=target_step, branch_data=branch_data)
            restore_state = tracer.consume_pending_restore_state()
        
        # Now apply patches (they will see the correct mode)
        apply_patches()

        if restore_state:
            install_state_restorer(restore_state)

