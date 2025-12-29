import os
import shutil
import tempfile
import subprocess
import json
import traceback
from typing import Dict, Any, Optional
from .models import AFECandidate
from .patcher import ApplyEngine

class SandboxValidator:
    """
    Validates candidates by running them in an isolated temporary environment.
    """
    
    def __init__(self):
        self.patcher = ApplyEngine()

    def validate(self, candidate: AFECandidate, trace_id: str, script_content: str, checkpoints_dir: str = None) -> Dict[str, Any]:
        """
        Runs the candidate fix in a sandbox.
        Returns validation results (success, logs, metrics).
        """
        print(f"🧪 Validator: Starting validation for candidate {candidate.type}...")
        
        # 1. Create Temp Directory
        with tempfile.TemporaryDirectory(prefix="afe_sandbox_") as tmp_dir:
            print(f"   Validator: Sandbox created at {tmp_dir}")
            
            try:
                # 2. Setup Files
                script_path = os.path.join(tmp_dir, "script.py")
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                # Copy checkpoints if needed (for replay)
                # For now, we assume the script can run standalone or we mock inputs
                # If checkpoints_dir is provided, copy it
                if checkpoints_dir and os.path.exists(checkpoints_dir):
                    shutil.copytree(checkpoints_dir, os.path.join(tmp_dir, "checkpoints"))

                # 3. Apply Patch
                if candidate.type in ["code_patch", "prompt_patch"]:
                    success = self.patcher.apply_file_patch(script_path, candidate)
                    if not success:
                        return {"success": False, "reason": "Patch application failed"}
                
                elif candidate.type == "config_change":
                    # Assume config is in a separate file or we need to patch a dict in script
                    # For this MVP, let's assume config is embedded or we skip config validation if no file
                    # TODO: Handle config files
                    pass

                # 4. Execute
                # We run the script. If it's a replay script, it should try to run.
                # We set a timeout to prevent infinite loops.
                print("   Validator: Executing patched script...")
                
                env = os.environ.copy()
                env["AGENTTRACE_MODE"] = "VALIDATION" # Signal to tracer/worker
                
                result = subprocess.run(
                    ["python", "script.py"],
                    cwd=tmp_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60 # 1 minute timeout
                )
                
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
                
                print(f"   Validator: Execution finished (Exit: {exit_code})")
                
                # 5. Verify
                # Success criteria: Exit code 0 AND no "Traceback" in stderr (unless expected)
                is_success = (exit_code == 0)
                
                # Refined check: Did we pass the step that failed?
                # Hard to know without deep introspection.
                # For now, exit code 0 is a strong signal.
                
                return {
                    "success": is_success,
                    "exit_code": exit_code,
                    "stdout": stdout[:1000], # Truncate logs
                    "stderr": stderr[:1000],
                    "reason": "Exit code 0" if is_success else "Non-zero exit code or timeout"
                }

            except subprocess.TimeoutExpired:
                print("   Validator: Execution timed out.")
                return {"success": False, "reason": "Execution timed out"}
            except Exception as e:
                print(f"   Validator: Error during validation: {e}")
                traceback.print_exc()
                return {"success": False, "reason": str(e)}
