"""
Branch storage utilities for AgentTrace.
"""
import json
import os
import re
import time
from pathlib import Path

BRANCH_DIR = Path(".agenttrace/branches")
SNAPSHOT_DIR = Path(".agenttrace/snapshots")


def _ensure_branch_dir():
    BRANCH_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_name(name: str) -> str:
    if not name:
        name = f"branch-{int(time.time())}"
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "-", name.strip())
    return cleaned or f"branch-{int(time.time())}"


def _branch_file(branch_id: str) -> Path:
    return BRANCH_DIR / f"{branch_id}.json"


def list_branches(trace_id: str | None = None):
    """
    Return list of branch metadata dicts. If trace_id provided, filter by parent.
    """
    if not BRANCH_DIR.exists():
        return []
    items = []
    for path in BRANCH_DIR.glob("*.json"):
        try:
            with path.open() as f:
                data = json.load(f)
            if trace_id and data.get("parent_trace_id") != trace_id:
                continue
            items.append(data)
        except Exception:
            continue
    return items


def load_branch(branch_id: str):
    path = _branch_file(branch_id)
    if not path.exists():
        raise FileNotFoundError(f"Branch not found: {branch_id}")
    with path.open() as f:
        data = json.load(f)
    return data


def create_branch(trace_id: str, fork_step: int, name: str | None = None):
    """
    Create a new branch metadata entry. Requires snapshot at fork_step.
    """
    snapshot_path = SNAPSHOT_DIR / f"{trace_id}_{fork_step}.pkl"
    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"No snapshot found for trace {trace_id} at step {fork_step}. "
            "Replay the trace with keyframes enabled before creating a branch."
        )

    _ensure_branch_dir()
    branch_name = _sanitize_name(name or f"step-{fork_step}")
    branch_id = f"{trace_id}__{branch_name}"
    path = _branch_file(branch_id)
    if path.exists():
        raise FileExistsError(f"Branch already exists: {branch_id}")

    data = {
        "branch_id": branch_id,
        "name": branch_name,
        "parent_trace_id": trace_id,
        "fork_step": fork_step,
        "created_at": time.time(),
        "overrides": {},
    }
    with path.open("w") as f:
        json.dump(data, f, indent=2)
    return data


def save_branch(data: dict):
    branch_id = data.get("branch_id")
    if not branch_id:
        raise ValueError("Branch data missing branch_id")
    _ensure_branch_dir()
    with _branch_file(branch_id).open("w") as f:
        json.dump(data, f, indent=2)


def update_override(branch_id: str, event_seq: int, payload: dict):
    data = load_branch(branch_id)
    overrides = data.setdefault("overrides", {})
    overrides[str(event_seq)] = payload
    save_branch(data)
    return data


