import os
import io
from typing import Dict, Union, Optional, Any

class VFSManager:
    _instance = None
    
    def __init__(self):
        # files: path -> content (str or bytes)
        self.files: Dict[str, Union[str, bytes]] = {}
        # change_log: list of modified paths since last snapshot
        self.modified_paths = set()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def reset(self):
        self.files = {}
        self.modified_paths = set()

    def write_file(self, path: str, content: Union[str, bytes]):
        """Write content to VFS at path."""
        norm_path = os.path.normpath(path)
        self.files[norm_path] = content
        self.modified_paths.add(norm_path)
        
        # Notify Tracer
        try:
            from agenttrace.core.tracer import Tracer
            t = Tracer.get_instance()
            # Only record if we are in recording mode
            # content payload might be large, maybe truncate for event stream?
            # For V1, let's store full content for small text files.
            display_content = content
            if isinstance(content, bytes):
                display_content = f"<binary: {len(content)} bytes>"
            elif len(content) > 5000:
                display_content = content[:5000] + "...(truncated)"

            t.record_event("file_write", {
                "path": norm_path,
                "content_preview": display_content,
                "size": len(content),
                "is_binary": isinstance(content, bytes)
            })
            # Also attach full content to the snapshot/keyframe logic via Tracer if needed
            # But strictly speaking, the 'file_write' event is enough to reconstruct if we replay.
        except Exception as e:
            print(f"[VFS] Failed to record event: {e}")

    def read_file(self, path: str, binary: bool = False) -> Union[str, bytes]:
        """Read from VFS. Falls back to disk if allowed (TODO)."""
        norm_path = os.path.normpath(path)
        if norm_path in self.files:
            content = self.files[norm_path]
            return content
        else:
            raise FileNotFoundError(f"VFS: File not found: {path}")

    def exists(self, path: str) -> bool:
        return os.path.normpath(path) in self.files

    def get_snapshot(self) -> Dict[str, Any]:
        """Return copy of current state."""
        return self.files.copy()
    
    def pop_modified_files(self) -> Dict[str, Any]:
        """Return dict of {path: content} for files changed since last call."""
        diff = {}
        for path in self.modified_paths:
            diff[path] = self.files[path]
        self.modified_paths.clear()
        return diff
