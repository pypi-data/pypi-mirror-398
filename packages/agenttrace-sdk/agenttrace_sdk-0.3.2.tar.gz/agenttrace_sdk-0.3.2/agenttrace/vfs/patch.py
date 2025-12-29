import builtins
import os
import contextlib
from typing import IO, Any
from .manager import VFSManager

# Save originals
_original_open = builtins.open
_original_remove = os.remove
_original_exists = os.path.exists

class VFSFileObj:
    """Mock file object for VFS with complete file-like interface."""
    def __init__(self, path, mode, vfs):
        self.path = path
        self.mode = mode
        self.vfs = vfs
        self.closed = False
        self._pos = 0
        self._buffer = ""
        
    def write(self, content):
        if self.closed:
            raise ValueError("I/O operation on closed file.")
        self.vfs.write_file(self.path, content)
        return len(content) if isinstance(content, (str, bytes)) else 0
        
    def read(self, size=-1):
        if self.closed:
            raise ValueError("I/O operation on closed file.")
        content = self.vfs.read_file(self.path) or ""
        if size < 0:
            return content[self._pos:]
        result = content[self._pos:self._pos + size]
        self._pos += len(result)
        return result

    def readline(self, limit=-1):
        """Read a single line from the file."""
        content = self.vfs.read_file(self.path) or ""
        remaining = content[self._pos:]
        newline_idx = remaining.find('\n')
        if newline_idx == -1:
            line = remaining
        else:
            line = remaining[:newline_idx + 1]
        if limit > 0:
            line = line[:limit]
        self._pos += len(line)
        return line

    def readlines(self, hint=-1):
        """Read all lines from the file."""
        lines = []
        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines

    def writelines(self, lines):
        """Write a list of lines to the file."""
        for line in lines:
            self.write(line)

    def seek(self, pos, whence=0):
        """Set file position."""
        if whence == 0:
            self._pos = pos
        elif whence == 1:
            self._pos += pos
        elif whence == 2:
            content = self.vfs.read_file(self.path) or ""
            self._pos = len(content) + pos
        return self._pos

    def tell(self):
        """Return current file position."""
        return self._pos

    def flush(self):
        """Flush write buffers (no-op for VFS)."""
        pass

    def fileno(self):
        """Return file descriptor (not supported by VFS)."""
        raise OSError("VFS does not support fileno()")

    def isatty(self):
        """Return whether this is a TTY (always False for VFS)."""
        return False

    def truncate(self, size=None):
        """Truncate file to specified size."""
        content = self.vfs.read_file(self.path) or ""
        if size is None:
            size = self._pos
        self.vfs.write_file(self.path, content[:size])
        return size

    def close(self):
        self.closed = True

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def _vfs_open(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    # CRITICAL: Exclude .agenttrace paths from VFS to allow tracer to write events to disk
    file_str = str(file)
    if ".agenttrace" in file_str or "agenttrace" in file_str:
        return _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
    
    # Use singleton instance
    vfs = VFSManager.get_instance()
    
    if "w" in mode or "a" in mode or "+" in mode:
        return VFSFileObj(file_str, mode, vfs)
    
    if vfs.exists(file_str):
        return VFSFileObj(file_str, mode, vfs)
        
    return _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

def _vfs_remove(path, *, dir_fd=None):
    vfs = VFSManager.get_instance()
    if vfs.exists(str(path)):
        vfs.remove(str(path))
    else:
        # Fallback only if we want to support deleting real files (Dangerous!)
        # Safety: Block real deletions in this mode
        raise FileNotFoundError(f"VFS: File not found and deletion blocked on host: {path}")

def _vfs_exists(path):
    vfs = VFSManager.get_instance()
    if vfs.exists(str(path)):
        return True
    return _original_exists(path)

@contextlib.contextmanager
def patch_io():
    """Context manager to intercept I/O calls."""
    builtins.open = _vfs_open
    os.remove = _vfs_remove
    os.path.exists = _vfs_exists
    
    try:
        yield
    finally:
        builtins.open = _original_open
        os.remove = _original_remove
        os.path.exists = _original_exists
