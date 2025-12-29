def capture_current_state(agent=None) -> dict:
    """
    Capture the AGENT'S LOGICAL STATE, not Python interpreter frames.

    This is the correct approach for AgentTrace:
    - Portable
    - Serializable
    - Replayable
    - Cross-language compatible
    """

    if agent is None:
        # If no agent object passed, return empty state
        # This avoids capturing Python internals (locals/globals)
        return {
            "messages": [],
            "memory": {},
            "context": {},
            "step": None,
            "runtime": {
                "py_random": None,
                "numpy_random": None,
            }
        }

    # Optional numpy RNG capture
    try:
        import numpy as _np
        numpy_rng = _np.random.get_state()
    except Exception:
        numpy_rng = None

    # Optional Python RNG capture
    import random
    py_rng = random.getstate()

    # Deep State Capture (Pickle)
    deep_state_blob = None
    try:
        import pickle
        import base64
        # We try to pickle the agent object itself
        # This allows exact restoration of custom classes
        blob = pickle.dumps(agent)
        deep_state_blob = base64.b64encode(blob).decode('ascii')
    except Exception as e:
        # If pickling fails (e.g. unpickleable resources like open files), we skip it
        # deep_state_blob = f"<pickle_failed: {str(e)}>"
        deep_state_blob = None

    state = {
        "messages": getattr(agent, "messages", []),
        "memory": getattr(agent, "memory", {}),
        "context": getattr(agent, "context", {}),
        "step": getattr(agent, "step", None),
        "extra_state": getattr(agent, "extra_state", {}),
        "runtime": {
            "py_random": py_rng,
            "numpy_random": numpy_rng,
            "deep_state_blob": deep_state_blob
        }
    }

    return state
