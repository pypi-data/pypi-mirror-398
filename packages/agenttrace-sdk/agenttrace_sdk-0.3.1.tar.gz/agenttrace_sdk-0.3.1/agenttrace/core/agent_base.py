# agenttrace/core/agent_base.py

import random
from typing import Dict, Any, List

try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False


class AgentBase:
    """
    A base class providing:
      - Unified state representation
      - Easy serialization/deserialization
      - Replay-safe RNG handling
      - Stable cross-framework memory format
    """

    def __init__(self):
        # Standardized AgentTrace-compatible fields
        self.messages: List[Dict[str, Any]] = []      # conversation history
        self.memory: Dict[str, Any] = {}              # app-level variables
        self.context: Dict[str, Any] = {}             # per-run execution context
        self.step: int = 0                            # logical step index
        self.extra_state: Dict[str, Any] = {}         # user-defined variables

    # ------------------------------------------------
    # SERIALIZATION (used during keyframe creation)
    # ------------------------------------------------
    def serialize_state(self) -> Dict[str, Any]:
        """
        Convert the agent's logical state into a JSON-serializable structure.
        DO NOT include Python interpreter internals.
        """

        # Optional: capture runtime seeds for deterministic replay
        try:
            py_random_state = random.getstate()
        except Exception:
            py_random_state = None

        if _HAS_NUMPY:
            try:
                numpy_state = _np.random.get_state()
            except Exception:
                numpy_state = None
        else:
            numpy_state = None

        return {
            "messages": self.messages,
            "memory": self.memory,
            "context": self.context,
            "step": self.step,
            "extra_state": self.extra_state,

            # Deterministic execution
            "runtime": {
                "py_random": py_random_state,
                "numpy_random": numpy_state,
            }
        }

    # ------------------------------------------------
    # DESERIALIZATION (used during replay hydration)
    # ------------------------------------------------
    def load_state(self, state: Dict[str, Any]):
        """
        Restore logical agent state — safe for replay.
        Note: This does NOT resume Python stack/frames (not possible).
        """

        self.messages = state.get("messages", [])
        self.memory = state.get("memory", {})
        self.context = state.get("context", {})
        self.step = state.get("step", 0)
        self.extra_state = state.get("extra_state", {})

        # Restore RNG for deterministic replay
        runtime = state.get("runtime", {})
        
        py_rng = runtime.get("py_random")
        if py_rng is not None:
            try:
                random.setstate(tuple(py_rng))
            except Exception:
                pass

        if _HAS_NUMPY:
            numpy_rng = runtime.get("numpy_random")
            if numpy_rng is not None:
                try:
                    _np.random.set_state(numpy_rng)
                except Exception:
                    pass

    # ------------------------------------------------
    # Utility: Logging helper (optional)
    # ------------------------------------------------
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.step += 1

    def set_memory(self, key: str, value: Any):
        self.memory[key] = value

    def set_context(self, key: str, value: Any):
        self.context[key] = value

    def set_extra(self, key: str, value: Any):
        self.extra_state[key] = value
