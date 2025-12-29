import json
import os
import random
import time
from typing import Dict, Any, Optional

class CheckpointManager:
    def __init__(self, storage_dir=".agenttrace/checkpoints"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_checkpoint(self, trace_id: str, step_id: int, agent_state: Dict[str, Any], 
                        event_offset: int) -> str:
        """
        Save a structured checkpoint. This is a KEYFRAME, not a full memory dump.
        """
        filename = f"{trace_id}_{step_id}.json"
        path = os.path.join(self.storage_dir, filename)

        checkpoint = {
            "trace_id": trace_id,
            "step_id": step_id,
            "timestamp": time.time(),

            # ------- Agent State (user-level) -------
            "agent_state": self._clean_for_json(agent_state),

            # ------- Runtime State (determinism) -------
            "runtime": {
                "random_state": self._serialize_random_state(),
                "next_step": step_id + 1,
                "event_offset": event_offset
            },

            # ------- Environment Metadata (moat) -------
            "python_meta": {
                "version": self._python_version(),
                "platform": self._platform(),
            }
        }

        try:
            with open(path, "w") as f:
                json.dump(checkpoint, f, indent=2)
            return path

        except Exception as e:
            print(f"[AgentTrace] Failed to save checkpoint {step_id}: {e}")
            return None

    def load_checkpoint(self, trace_id: str, step_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a structured checkpoint.
        """
        filename = f"{trace_id}_{step_id}.json"
        path = os.path.join(self.storage_dir, filename)

        if not os.path.exists(path):
            return None

        try:
            with open(path, "r") as f:
                checkpoint = json.load(f)
                return checkpoint

        except Exception as e:
            print(f"[AgentTrace] Failed to load checkpoint {step_id}: {e}")
            return None

    # ----------------------------------------------------
    # Helpers
    # ----------------------------------------------------

    def _serialize_random_state(self):
        try:
            return random.getstate()
        except Exception:
            return "<unserializable-random-state>"

    def _python_version(self):
        import sys
        return sys.version

    def _platform(self):
        import platform
        return platform.platform()

    def _clean_for_json(self, obj: Any) -> Any:
        """
        Recursively convert object to JSON-safe form.
        """
        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                if not k.startswith('_'):
                    cleaned[k] = self._clean_for_json(v)
            return cleaned

        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]

        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj

        else:
            # Non-serializable = string fallback
            return f"<non-serializable: {type(obj).__name__}>"
