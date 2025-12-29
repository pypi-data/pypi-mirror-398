# agenttrace/core/replay.py
import json
from typing import List, Any, Dict

def load_parent_events(supabase_client, parent_trace_id: str) -> List[Dict[str, Any]]:
    """
    Download and parse parent events.jsonl from storage.
    Returns a list of event dicts sorted by seq if available.
    """
    # storage path
    path = f"{parent_trace_id}/events.jsonl"
    try:
        blob = supabase_client.storage.from_("traces").download(path)
        if not blob:
            print(f"⚠ load_parent_events: no events.jsonl for {parent_trace_id}")
            return []
        text = blob.decode() if isinstance(blob, (bytes, bytearray)) else blob.text()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        events = []
        for line in lines:
            try:
                ev = json.loads(line)
                events.append(ev)
            except Exception:
                # ignore malformed lines
                continue
        # sort by seq if present
        events.sort(key=lambda e: e.get("seq", e.get("step", 0)))
        return events
    except Exception as e:
        print(f"⚠ load_parent_events error: {e}")
        return []

def apply_event_to_state(state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal, conservative event applier.
    Designed for your JSON structured checkpoints / events.
    """
    # defensive copy shallow
    state = dict(state or {})
    try:
        t = event.get("type", "")
        payload = event.get("payload", {}) or {}
        # prefer post_state if available
        if "post_state" in event and event["post_state"] is not None:
            return event["post_state"]
        if t in ("message", "message_append", "llm_call"):
            msgs = state.get("messages", [])
            if isinstance(payload, dict) and "messages" in payload:
                msgs.extend(payload["messages"])
            elif isinstance(payload, dict) and "message" in payload:
                msgs.append(payload["message"])
            elif isinstance(payload, str):
                msgs.append({"role": "assistant", "content": payload})
            state["messages"] = msgs
        elif t in ("tool_call", "tool_result"):
            state.setdefault("memory", {})
            tools = state["memory"].get("tools", {})
            tool_name = payload.get("tool") or payload.get("name") or "unknown"
            tools[tool_name] = payload.get("result") or payload.get("output") or payload
            state["memory"]["tools"] = tools
        elif t == "state_update":
            # merge shallow
            if isinstance(payload, dict):
                for k,v in payload.items():
                    state[k] = v
        else:
            # fallback: if event has 'delta' or small state updates
            if isinstance(payload, dict):
                # merge into state top-level if keys don't collide violently
                for k, v in payload.items():
                    if k not in ("log", "debug"):
                        state[k] = v
    except Exception as e:
        print("⚠ apply_event_to_state error:", e)
    return state

def hydrate_state_from_events(base_state: Dict[str, Any], events: List[Dict[str, Any]], target_step: int) -> Dict[str, Any]:
    """
    Starting from a base_state (branch -1 checkpoint), fast-forward through
    parent events up to target_step and return the hydrated state.
    Assumption: events are sorted by seq.
    """
    state = dict(base_state or {})
    # If events include numeric seq/step keys, iterate until step == target_step (inclusive/exclusive as you prefer)
    for ev in events:
        seq = ev.get("seq", ev.get("step", None))
        if seq is None:
            continue
        if seq > target_step:
            break
        # apply event
        state = apply_event_to_state(state, ev)
    return state
