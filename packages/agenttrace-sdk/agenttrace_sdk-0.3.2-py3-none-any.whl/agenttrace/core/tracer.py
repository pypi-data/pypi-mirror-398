# agenttrace/core/tracer.py
import os
import sys
import json
import uuid
import time as time_module
import threading
from enum import Enum
from typing import Optional, Dict, Any, Iterable
from contextlib import contextmanager

# Local imports — ensure these exist
from agenttrace.core.checkpoint import CheckpointManager
# You must implement capture_current_state() to return serializable agent_state dict
from agenttrace.core.state_capture import capture_current_state

# optional numpy support for RNG
try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False

_original_time = time_module.time

class Mode(Enum):
    RECORD = "RECORD"
    REPLAY = "REPLAY"
    OFF = "OFF"

def _atomic_write(path: str, data: bytes):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

class Tracer:
    _instance = None
    _instance_pid = None

    @classmethod
    def get_instance(cls):
        pid = os.getpid()
        if cls._instance is None or cls._instance_pid != pid:
            cls._instance = cls()
            cls._instance_pid = pid
        return cls._instance

    def __init__(self, keyframe_interval: int = 10, storage_root: str = ".agenttrace/traces"):
        self.mode = Mode.OFF
        self.trace_id: Optional[str] = None
        self.storage_root = storage_root
        self.keyframe_interval = keyframe_interval
        self.checkpoint_manager = CheckpointManager()
        self._pending_restore_state = None
        self.branch_overrides: Dict[int, Any] = {}
        self.branch_id: Optional[str] = None
        
        # Forking support: "Silent Fast Forward"
        # If set, we skip recording events until seq > fork_step
        self.fork_step: Optional[int] = None
        try:
            if os.environ.get("AGENTTRACE_FORK_STEP"):
                self.fork_step = int(os.environ["AGENTTRACE_FORK_STEP"])
                print(f"[Tracer] Fork mode active. Fast-forwarding until step {self.fork_step}...")
        except ValueError:
            pass
        
        self.branch_fork_step: Optional[int] = None
        self.script_path: Optional[str] = None
        self.script_content: Optional[str] = None

        # In-memory cache for small traces; large traces are appended to disk
        self._event_lock = threading.Lock()
        self._event_seq = 0  # next seq number
        self._events_mem: list = []  # short-term caching
        self._events_file_path: Optional[str] = None
        self.keyframes: Dict[int, str] = {}  # step -> checkpoint_path (on disk)
        os.makedirs(self.storage_root, exist_ok=True)
        self._closed = False
        self._guard = threading.local()
        
        # Audit context for compliance tracking
        self.audit_context: Dict[str, Any] = {
            "user_id": os.environ.get("AGENTTRACE_USER_ID"),
            "job_id": os.environ.get("AGENTTRACE_JOB_ID"),
            "run_version": os.environ.get("AGENTTRACE_RUN_VERSION", "1"),
            "seed": None  # Set during deterministic runs
        }

        # Auto-start if running in worker context (subprocess)
        env_trace_id = os.environ.get("AGENTTRACE_TRACE_ID")
        # SAFETY GUARD: Only auto-start if explicitly enabled
        # This prevents accidental tracing in tests or parent processes
        auto_enable = os.environ.get("AGENTTRACE_ENABLE") == "1"
        
        if env_trace_id and auto_enable:
            print(f"[Tracer] Auto-starting recording for trace {env_trace_id} (from environment)")
            # Use append_mode to preserve existing events from parent worker process
            self.start_recording(trace_id=env_trace_id, append_mode=True)

    @contextmanager
    def disable_instrumentation(self):
        if not hasattr(self._guard, "disabled"):
            self._guard.disabled = False
        prev = self._guard.disabled
        self._guard.disabled = True
        try:
            yield
        finally:
            self._guard.disabled = prev

    # @classmethod get_instance is now defined above for clarity


    # -----------------------
    # Lifecycle: start/stop
    # -----------------------
    def _trace_dir(self, trace_id: str) -> str:
        d = os.path.join(self.storage_root, trace_id)
        os.makedirs(d, exist_ok=True)
        return d

    def start_recording(
        self, 
        script_path: Optional[str] = None, 
        script_content: Optional[str] = None, 
        trace_id: Optional[str] = None, 
        append_mode: bool = False,
        # Atomic injection parameters - applied AFTER initialization
        fork_step: Optional[int] = None,
        event_override: Optional[dict] = None,  # Legacy single override (backward compat)
        event_overrides: Optional[Dict[str, dict]] = None,  # NEW: Multi-tool overrides
        # Test isolation - skip heavy patching
        skip_instrumentation: bool = False
    ):
        """Start recording a new trace.
        
        Args:
            script_path: Path to the script being traced
            script_content: Optional content of the script
            trace_id: UUID for the trace (generated if not provided)
            append_mode: If True, append to existing events instead of clearing
            fork_step: Optional step number for What-If injection (applied atomically)
            event_override: (Legacy) Single event override payload for What-If injection
            event_overrides: Dict of {tool_name: override} for multi-tool What-If injection
            skip_instrumentation: If True, skip auto-instrumentation and VFS patching (for tests)
        """
        with self._event_lock:
            # Reset closed flag for new recording session
            self._closed = False
            
            self.mode = Mode.RECORD
            self.trace_id = trace_id or str(uuid.uuid4())
            trace_dir = self._trace_dir(self.trace_id)
            self._events_file_path = os.path.join(trace_dir, "events.jsonl")
            
            if append_mode:
                # Append mode: count existing events to continue sequencing
                # Optimized: use _next_sequence_number_from_file instead of full read
                self._events_mem = []
                self._event_seq = self._next_sequence_number_from_file()
                print(f"[AgentTrace] Append mode: starting at seq {self._event_seq}")
            else:
                # Fresh start: clear old events file if it exists
                if os.path.exists(self._events_file_path):
                    try:
                        os.remove(self._events_file_path)
                    except Exception as e:
                        print(f"[AgentTrace] warning: failed to remove old trace {self._events_file_path}: {e}")
                
                # FORCE CREATION NOW to ensure file exists before append
                try:
                    with open(self._events_file_path, "w") as f:
                        pass
                    print(f"[AgentTrace] Created new events file: {self._events_file_path}")
                except Exception as e:
                    print(f"[AgentTrace] ❌ Failed to create events file {self._events_file_path}: {e}")
                    print(f"[AgentTrace] Cleared old events file for fresh recording")
                self._event_seq = 0
            
            self._events_mem = []
            self.keyframes = {}
            self.script_path = script_path
            self.script_content = script_content
            
            # Reset fork/branch state FIRST
            self.branch_overrides = {}
            self.branch_id = None
            self.branch_fork_step = None
            
            # ATOMIC INJECTION: Apply fork_step and event_override AFTER reset
            # This ensures they cannot be accidentally clobbered
            if fork_step is not None:
                self.fork_step = int(fork_step)
                print(f"[AgentTrace] 🔮 Fork mode enabled: injection at step {self.fork_step}")
            else:
                self.fork_step = None
            
            if event_override is not None:
                # Deep copy to prevent external mutations
                import copy
                self.event_override = copy.deepcopy(event_override)
                override_tool = event_override.get("payload", {}).get("tool") or event_override.get("tool", "unknown")
                print(f"[AgentTrace] 🔮 Event override set for tool: {override_tool}")
            else:
                self.event_override = None
            
            # NEW: Multi-tool overrides dict
            if event_overrides is not None:
                import copy
                self.event_overrides = copy.deepcopy(event_overrides)
                print(f"[AgentTrace] 🔮 Multi-tool overrides set for: {list(event_overrides.keys())}")
            else:
                self.event_overrides = {}
            
            self._save_metadata()
            
            # Auto-Instrumentation and VFS (skip for tests)
            if not skip_instrumentation:
                try:
                    from agenttrace.instrumentation.patch import apply_patches
                    apply_patches()
                    print(f"[AgentTrace] Auto-instrumentation applied for {self.trace_id}")
                except Exception as e:
                    print(f"[AgentTrace] Failed to apply auto-instrumentation: {e}")

                # Initialize VFS Patcher
                try:
                    from agenttrace.vfs.patcher import VFSPatcher
                    self.vfs_patcher = VFSPatcher()
                    self.vfs_patcher.__enter__()
                    print(f"[AgentTrace] VFS Patcher active for trace {self.trace_id}")
                except Exception as e:
                    print(f"[AgentTrace] Failed to activate VFS: {e}")
                    self.vfs_patcher = None

            print(f"[AgentTrace] Recording started: {self.trace_id}")

    def try_consume_injected_result(self, tool_name: str) -> tuple:
        """Atomically check and consume an injected result for this tool invocation.
        
        This is the ONLY method decorators should call for injection. It combines:
        1. Check if injection should happen (matching tool name)
        2. Parse and return the injected value
        3. Record the synthetic tool_end event
        4. Clear the override (one-time use per tool)
        
        Supports both:
        - Legacy: self.event_override (single override)
        - New: self.event_overrides[tool_name] (multi-tool dict)
        
        All under a single lock to prevent race conditions.
        
        Returns:
            (True, result) if injection applied
            (False, None) if no injection
        """
        with self._event_lock:
            override_payload = None
            override_source = None  # Track which source was used
            
            # Check multi-tool overrides first (new way)
            if hasattr(self, 'event_overrides') and tool_name in self.event_overrides:
                override_entry = self.event_overrides[tool_name]
                override_payload = override_entry.get("payload", override_entry)
                override_source = "multi"
                print(f"[Tracer] Found multi-tool override for {tool_name}")
            
            # Fall back to legacy single override
            elif self.event_override is not None:
                override_entry = self.event_override
                override_payload_raw = override_entry.get("payload", {})
                override_tool = override_payload_raw.get("tool") or override_entry.get("tool")
                override_type = override_entry.get("type", "")
                
                # Legacy requires type and tool match
                if override_type == "tool_end" and override_tool == tool_name:
                    override_payload = override_payload_raw
                    override_source = "legacy"
                    print(f"[Tracer] Found legacy override for {tool_name}")
            
            # No matching override found
            if override_payload is None:
                return False, None
            
            # Parse the result from override
            result = override_payload.get("result")
            
            # Parse if string representation of dict/list
            if isinstance(result, str):
                try:
                    import ast
                    result = ast.literal_eval(result)
                except:
                    pass  # Keep as string if parsing fails
            
            print(f"[Tracer] 🔮 INJECTION APPLIED for {tool_name}: {result}")
            
            # Record the synthetic tool_end event IMMEDIATELY (crash resilience)
            seq = self._event_seq
            event = {
                "seq": seq,
                "type": "tool_end",
                "payload": {
                    "tool": tool_name,
                    "result": result,
                    "injected": True
                },
                "timestamp": __import__('time').time()
            }
            self._event_seq += 1
            
            # Persist immediately to disk for crash resilience
            self._append_events_to_file([event])
            
            # Clear the override after successful injection (one-time use)
            if override_source == "multi":
                del self.event_overrides[tool_name]
            else:
                self.event_override = None
            
            return True, result
    
    # Keep old methods as deprecated wrappers for backward compatibility
    def should_inject_result(self, tool_name: str) -> bool:
        """DEPRECATED: Use try_consume_injected_result() instead."""
        with self._event_lock:
            if self.fork_step is None or self.event_override is None:
                return False
            override_payload = self.event_override.get("payload", {})
            override_tool = override_payload.get("tool") or self.event_override.get("tool")
            override_type = self.event_override.get("type", "")
            return override_type == "tool_end" and override_tool == tool_name
    
    def consume_injected_result(self) -> Any:
        """DEPRECATED: Use try_consume_injected_result() instead."""
        with self._event_lock:
            if self.event_override is None:
                return None
            payload = self.event_override.get("payload", self.event_override)
            result = payload.get("result")
            if isinstance(result, str):
                try:
                    import ast
                    result = ast.literal_eval(result)
                except:
                    pass
            self.event_override = None
            return result

    def start_replay(self, trace_id: str, target_step: Optional[int] = None, branch_data: Optional[dict] = None):
        # We generally do NOT want to patch VFS during replay unless we are simulating
        # Simulation uses EXECUTION mode (Worker), not Replay mode.
        # But if we want to "replay" file state, we rely on the events "file_write".
        # So we don't need VFS patcher here.
        with self._event_lock:
            self.mode = Mode.REPLAY
            self.trace_id = trace_id
            trace_dir = self._trace_dir(self.trace_id)
            self._events_file_path = os.path.join(trace_dir, "events.jsonl")
            self.keyframes = self._load_keyframes(trace_id)
            self.branch_overrides = {}
            self.branch_id = None
            self.branch_fork_step = None
            self._events_mem = []
            # load event seq from disk header if exists
            self._event_seq = self._next_sequence_number_from_file()
            # Load event log in memory lazily via _load_trace()
            if branch_data:
                if branch_data.get("parent_trace_id") != trace_id:
                    raise ValueError("Branch parent mismatch")
                overrides = branch_data.get("overrides", {})
                self.branch_overrides = {int(k): v for k, v in overrides.items()}
                self.branch_id = branch_data.get("branch_id")
                self.branch_fork_step = branch_data.get("fork_step")
                if target_step is None:
                    target_step = self.branch_fork_step
            if target_step is not None:
                self._jump_to_step(target_step)
            else:
                self.replay_cursor = 0
            print(f"[AgentTrace] Replay started: {trace_id} cursor={getattr(self,'replay_cursor',0)}")

    def stop(self):
        """Flush and close resources — call on worker shutdown."""
        trace_id_copy = self.trace_id  # Capture before reset
        script_content_copy = self.script_content
        script_path_copy = self.script_path
        
        with self._event_lock:
            if self._events_mem:
                self._flush_events_to_disk()
            
            self.mode = Mode.OFF

            
            # Teardown VFS Patcher
            if getattr(self, 'vfs_patcher', None):
                self.vfs_patcher.__exit__(None, None, None)
                self.vfs_patcher = None
                print("[AgentTrace] VFS Patcher deactivated")

            self._closed = True
            print("[AgentTrace] stopped and flushed")
        
        # AUTO-UPLOAD SCRIPT TO CLOUD (outside lock to avoid blocking)
        # This ensures Replay works for all end users
        self._upload_script_to_cloud(trace_id_copy, script_content_copy, script_path_copy)

    # -----------------------
    # Event recording & storage
    # -----------------------
    def record_event(self, event_type: str, payload: Any, state_snapshot: Optional[dict] = None, auto_capture: bool = True):
        if getattr(self._guard, "disabled", False):
            return None

        print(f"DEBUG: record_event {event_type}", flush=True)
        if self.mode not in (Mode.RECORD, Mode.REPLAY):
            return None
        
        # Prevent internal recursion (e.g. time.time() calls inside here)
        with self.disable_instrumentation():
            with self._event_lock:
                seq = self._event_seq
                self._event_seq += 1

                # Fork Logic: Silent Fast Forward
                # If we are in a fork and this step is already in history, skip recording it.
                if self.fork_step is not None and seq <= self.fork_step:
                    return seq

                # 1. Prepare event
                event = {
                    "seq": seq,
                    "type": event_type,
                    "payload": self._clean_for_json(payload),
                    "timestamp": time_module.time_ns() / 1e9,
                    "is_keyframe": False
                }
                
                # CRITICAL FIX: Direct append only. 
                # Do NOT buffer in memory for persistence to avoid double-write risks during crashes.
                # self._events_mem.append(event) 

            # flush on buffer growth to keep memory low
            # if len(self._events_mem) >= 50:
            #    self._flush_events_to_disk()

            # maybe create snapshot
            if state_snapshot is not None:
                snapshot = state_snapshot
            elif (seq % self.keyframe_interval == 0) and auto_capture:
                try:
                    snapshot = capture_current_state()
                except Exception:
                    snapshot = None
            else:
                snapshot = None

            if snapshot is not None:
                # checkpoint manager expected: save_checkpoint(trace_id, step_id, agent_state, event_offset)
                try:
                    cp_path = self.checkpoint_manager.save_checkpoint(self.trace_id, seq, snapshot, event_offset=seq)
                    if cp_path:
                        self.keyframes[seq] = cp_path
                        event["is_keyframe"] = True
                        # optionally persist keyframes metadata immediately
                        self._save_keyframes()
                except Exception as e:
                    print(f"[AgentTrace] warning: failed to save keyframe {seq}: {e}")

            # persist event immediately (IMMEDIATE FLUSH)
            # This guarantees durability even if process crashes immediately after
            self._append_events_to_file([event])
            
            # self._events_mem = []  # cleared after flush



            # save metadata on first event
            if seq == 0:
                self._save_metadata()

            return event["seq"]

    # -----------------------
    # High-level Helpers
    # -----------------------
    def thought(self, content: str):
        self.record_event("thought", {"content": content})

    def llm(self, content: str):
        self.record_event("llm", {"content": content})

    def tool(self, name: str, result: Any):
        self.record_event("tool_result", {"tool_name": name, "result": result})

    def exception(self, message: str, error: Exception):
        import traceback
        self.record_event("python_exception", {
            "error_type": type(error).__name__,
            "message": f"{message}: {str(error)}",
            "traceback": traceback.format_exc()
        })

    def _append_events_to_file(self, events: Iterable[dict]):
        """
        Append list of events to events.jsonl atomically.
        We write to a temp file and append to actual file to avoid interleaving in concurrent workers.
        """
        if not self.trace_id:
            raise RuntimeError("No trace id set")
        trace_dir = self._trace_dir(self.trace_id)
        events_path = os.path.join(trace_dir, "events.jsonl")
        
        # print(f"DEBUG: appending {len(list(events))} events to {events_path}") # Consumes iterable!
        ev_list = list(events)
        if not ev_list:
            return

        # open in append binary and write newline-delimited json
        try:
            # Bypass patched open() to ensure disk write
            import stat
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
            fd = os.open(events_path, flags, 0o666)
            with os.fdopen(fd, "a", encoding="utf-8") as f: # usage of "a" matches O_APPEND
                for ev in ev_list:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception: 
                    pass
        except Exception as e:
            print(f"[{os.getpid()}] [AgentTrace] failed to append events to {events_path}: {e}")
            import traceback
            traceback.print_exc()

    def _flush_events_to_disk(self):
        # wrapper for any buffered events (kept for safety)
        if self._events_mem:
            self._append_events_to_file(self._events_mem)
            self._events_mem = []

    def _next_sequence_number_from_file(self) -> int:
        if not self.trace_id:
            return 0
        events_path = os.path.join(self._trace_dir(self.trace_id), "events.jsonl")
        if not os.path.exists(events_path):
            return 0
            
        # SAFETY: Attempt repair first if file is corrupted
        self._recover_corrupted_events_file(events_path)

        # read last line quickly
        try:
            with open(events_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                filesize = f.tell()
                # walk backwards until newline found
                step_back = 1024
                while True:
                    pos = max(0, filesize - step_back)
                    f.seek(pos)
                    chunk = f.read(min(step_back, filesize))
                    if b"\n" in chunk:
                        # parse last line
                        last_line = chunk.split(b"\n")[-2] if chunk.endswith(b"\n") else chunk.split(b"\n")[-1]
                        try:
                            last = json.loads(last_line.decode("utf-8"))
                            return last.get("seq", 0) + 1
                        except Exception:
                            return 0
                    if pos == 0:
                        # full small file
                        f.seek(0)
                        all_lines = f.read().splitlines()
                        if not all_lines:
                            return 0
                        try:
                            last = json.loads(all_lines[-1].decode("utf-8"))
                            return last.get("seq", 0) + 1
                        except Exception:
                            return 0
                    step_back *= 2
        except Exception:
            return 0
            
    def _recover_corrupted_events_file(self, path: str) -> None:
        """Truncate file to last valid newline if corruption detected"""
        try:
             with open(path, "rb+") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                if size == 0: return
                
                # Check last byte
                f.seek(-1, os.SEEK_END)
                if f.read(1) == b'\n':
                    return # Looks ok ending in newline
                
                # If not ending in newline, we might have partial write
                print(f"[AgentTrace] ⚠️ Detected potential corruption/partial write in {path}. Attempting repair...")
                
                # Scan backwards for last newline
                f.seek(0, os.SEEK_END)
                # Simple recovery: truncate to last newline
                # (Production grade would be more sophisticated, but this prevents crashes)
                pos = size - 1
                while pos > 0:
                    f.seek(pos)
                    if f.read(1) == b'\n':
                        # Found valid end of previous line
                        f.seek(pos + 1)
                        f.truncate()
                        print(f"[AgentTrace] ✅ Repaired file by truncating to {pos+1}")
                        return
                    pos -= 1
                
                # If we got here, file has no newlines? Truncate everything? 
                # Or keep as is if it's just one line without newline.
                pass
        except Exception as e:
            print(f"[AgentTrace] Failed to repair corrupted file: {e}")

    # -----------------------
    # Replay helpers
    # -----------------------
    def _jump_to_step(self, target_step: int):
        """
        Jump to specific step using keyframe + pending restore state.
        """
        trace_dir = self._trace_dir(self.trace_id)
        # find nearest keyframe <= target
        nearest = None
        for s in sorted(self.keyframes.keys(), reverse=True):
            if s <= target_step:
                nearest = s
                break

        if nearest is None:
            print(f"[AgentTrace] no keyframe <= {target_step}; starting from beginning")
            self.replay_cursor = 0
            self._pending_restore_state = None
            return

        cp_path = self.keyframes.get(nearest)
        if not cp_path or not os.path.exists(cp_path):
            print(f"[AgentTrace] missing checkpoint file for step {nearest}")
            self.replay_cursor = 0
            self._pending_restore_state = None
            return

        cp = self.checkpoint_manager.load_checkpoint(self.trace_id, nearest)
        if cp is None:
            print(f"[AgentTrace] checkpoint load returned None for {nearest}")
            self.replay_cursor = 0
            self._pending_restore_state = None
            return

        print(f"[AgentTrace] loaded keyframe {nearest}, pending restore; fast-forwarding cursor to {target_step}")
        self._pending_restore_state = cp
        self.replay_cursor = target_step

    def get_next_replay_event(self, expected_type: Optional[str] = None) -> Optional[dict]:
        """
        When replaying, runtime calls this to obtain next payload.
        It returns the payload (with branch override applied) or None at EOF.
        """
        if self.mode != Mode.REPLAY:
            return None

        # read next event from disk by seeking the replay_cursor
        ev = self._read_event_by_seq(self.replay_cursor)
        if ev is None:
            return None

        if expected_type and ev.get("type") != expected_type:
            print(f"[AgentTrace] divergence: expected {expected_type} but found {ev.get('type')} at seq {ev.get('seq')}")

        payload = ev.get("payload")
        override = self.branch_overrides.get(ev.get("seq"))
        if override is not None:
            payload = override

        # advance cursor for next call
        self.replay_cursor += 1
        return payload

    def _read_event_by_seq(self, seq: int) -> Optional[dict]:
        """
        Sequential read from events.jsonl. Optimized to stream until seq is reached.
        For simplicity: read file line-by-line until matching seq.
        For big files you can optimize via an index or simple chunked reads.
        """
        path = os.path.join(self._trace_dir(self.trace_id), "events.jsonl")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    ev = json.loads(line)
                    if ev.get("seq") == seq:
                        return ev
            return None
        except Exception as e:
            print(f"[AgentTrace] failed to read event {seq}: {e}")
            return None

    # -----------------------
    # Utility: keyframes + metadata
    # -----------------------
    def _save_keyframes(self):
        if not self.trace_id:
            return
        try:
            path = os.path.join(self._trace_dir(self.trace_id), "keyframes.json")
            _atomic_write(path, json.dumps({str(k): v for k,v in self.keyframes.items()}, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            print(f"[AgentTrace] failed to save keyframes: {e}")

    def _load_keyframes(self, trace_id: str) -> Dict[int, str]:
        path = os.path.join(self._trace_dir(trace_id), "keyframes.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): v for k,v in raw.items()}
        except Exception as e:
            print(f"[AgentTrace] failed to load keyframes: {e}")
            return {}

    def _save_metadata(self):
        if not self.trace_id:
            return
        try:
            meta = {"script_path": self.script_path, "script_content": self.script_content, "created_at": _original_time()}
            path = os.path.join(self._trace_dir(self.trace_id), "metadata.json")
            _atomic_write(path, json.dumps(meta, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            print(f"[AgentTrace] failed to save metadata: {e}")

    def _load_metadata(self, trace_id: str) -> dict:
        path = os.path.join(self._trace_dir(trace_id), "metadata.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[AgentTrace] failed to load metadata: {e}")
            return {}

    def _upload_script_to_cloud(self, trace_id: str, script_content: Optional[str], script_path: Optional[str]):
        """Auto-upload script to cloud storage for Replay support.
        
        Tries API key auth first (simple), falls back to direct Supabase.
        """
        if not trace_id:
            return
        
        # Get script content
        content_str = None
        if script_content:
            content_str = script_content if isinstance(script_content, str) else script_content.decode("utf-8")
        elif script_path and os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                content_str = f.read()
        
        if not content_str:
            print(f"[AgentTrace] ⚠ No script content to upload for trace {trace_id[:8]}")
            return
        
        # Method 1: API Key auth (preferred - simple for users)
        api_key = os.environ.get("AGENTTRACE_API_KEY")
        api_url = os.environ.get("AGENTTRACE_API_URL", "https://moat-kappa.vercel.app/api")
        
        if api_key:
            try:
                import requests
                response = requests.post(
                    f"{api_url}/sdk/trace/end",
                    json={
                        "trace_id": trace_id,
                        "status": "completed",
                        "script_content": content_str
                    },
                    headers={"X-API-Key": api_key},
                    timeout=30
                )
                if response.ok:
                    print(f"[AgentTrace] ✅ Script synced to cloud via API ({trace_id[:8]})")
                    return
                else:
                    print(f"[AgentTrace] ⚠ API sync failed: {response.status_code}")
            except Exception as e:
                print(f"[AgentTrace] ⚠ API sync error: {e}")
        
        # Method 2: Direct Supabase (fallback)
        supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                client = create_client(supabase_url, supabase_key)
                
                content_bytes = content_str.encode("utf-8")
                dest_path = f"{trace_id}/script.py"
                
                try:
                    client.storage.from_("traces").upload(
                        dest_path, content_bytes, {"content-type": "text/x-python", "upsert": "true"}
                    )
                    print(f"[AgentTrace] ✅ Script uploaded to Supabase ({trace_id[:8]})")
                except Exception as upload_err:
                    if "already exists" in str(upload_err).lower():
                        client.storage.from_("traces").update(
                            dest_path, content_bytes, {"content-type": "text/x-python"}
                        )
                        print(f"[AgentTrace] ✅ Script updated in Supabase ({trace_id[:8]})")
                    else:
                        raise
            except ImportError:
                pass
            except Exception as e:
                print(f"[AgentTrace] ⚠ Supabase upload failed: {e}")

    # -----------------------
    # JSON cleaning
    # -----------------------
    def _clean_for_json(self, obj: Any):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k.startswith("_"):
                    continue
                out[k] = self._clean_for_json(v)
            return out
        if isinstance(obj, (list, tuple)):
            return [self._clean_for_json(x) for x in obj]
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        try:
            s = str(obj)
            if len(s) > 1000:
                s = s[:1000] + "...(truncated)"
            return s
        except Exception:
            return f"<non-serializable:{type(obj).__name__}>"

    # -----------------------
    # pending restore
    # -----------------------
    def consume_pending_restore_state(self):
        with self._event_lock:
            state = self._pending_restore_state
            self._pending_restore_state = None
            return state

    # -----------------------
    # Helpers for RNG capture (used by CheckpointManager)
    # -----------------------
    def capture_runtime_state(self) -> dict:
        """Return deterministic runtime state to be stored in keyframe"""
        rt = {}
        try:
            rt["py_random"] = _serialize_random_state()
        except Exception:
            rt["py_random"] = "<error>"
        if _HAS_NUMPY:
            try:
                rt["numpy_random"] = _np.random.get_state()
            except Exception:
                rt["numpy_random"] = "<error>"
        return rt
