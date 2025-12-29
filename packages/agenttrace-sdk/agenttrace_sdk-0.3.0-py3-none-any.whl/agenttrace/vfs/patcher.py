import builtins
import os
import io
from .manager import VFSManager

class VFSFile(io.BytesIO):
    """
    A file-like object acting as a proxy for VFS content.
    For text mode, we wrap string IO. For binary, BytesIO.
    """
    def __init__(self, path, mode='r', initial_content=None, manager=None):
        self.path = path
        self.mode = mode
        self.manager = manager
        
        # Determine if binary
        self.is_binary = 'b' in mode
        self.is_write = 'w' in mode or 'a' in mode or '+' in mode or 'x' in mode
        
        # Prepare buffer
        if initial_content is not None:
            if isinstance(initial_content, str) and not self.is_binary:
                super().__init__(initial_content.encode('utf-8'))
            elif isinstance(initial_content, str) and self.is_binary:
                super().__init__(initial_content.encode('utf-8'))
            else:
                super().__init__(initial_content)
        else:
            super().__init__()
            
        if 'a' in mode:
            self.seek(0, 2) # seek to end
        elif 'r' in mode:
            self.seek(0)
            
    def close(self):
        # On close, flush to manager if writing
        if self.is_write and self.manager:
            # Get value
            self.seek(0)
            # Use super().read() to get raw bytes, because self.read() might decode to str
            content_bytes = super().read()
            
            if self.is_binary:
                self.manager.write_file(self.path, content_bytes)
            else:
                # Text mode: decode
                try:
                    text_content = content_bytes.decode('utf-8')
                    self.manager.write_file(self.path, text_content)
                except UnicodeDecodeError:
                    # Fallback to saving bytes if decode fails even in text mode intent
                     self.manager.write_file(self.path, content_bytes)
                     
        super().close()
        
    # Implement TextIOWrapper-like methods for text mode COMPATIBILITY
    # If the user expects a TextIO object, BytesIO might fail on 'write(str)'
    # So we need to handle that.
    # Actually, subclassing BytesIO is tricky for Text mode.
    # Better to use composition or a hybrid class.
    
    def write(self, s):
        if not self.is_binary and isinstance(s, str):
            return super().write(s.encode('utf-8'))
        return super().write(s)

    def read(self, size=-1):
        ret = super().read(size)
        if not self.is_binary and isinstance(ret, bytes):
            return ret.decode('utf-8')
        return ret


class VFSPatcher:
    def __init__(self):
        self.original_open = builtins.open
        self.manager = VFSManager.get_instance()
        self.active = False
        
    def __enter__(self):
        self.active = True
        builtins.open = self._vfs_open
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active = False
        builtins.open = self.original_open

    def _vfs_open(self, file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        # Only intercept if it's a file path we want to manage (e.g. not absolute system paths? or ALL paths?)
        # For Sandbox safety, we should ideally trap ALL writes.
        # But we need to allow imports (reading libraries).
        
        # Rule:
        # 1. Write ('w', 'a', '+', 'x') -> Always VFS.
        # 2. Read ('r') -> Try VFS, if not found -> Try Real Disk (Pass-through).
        
        # Normalize path
        str_path = str(file)
        
        # KEY FIX: Bypass VFS for internal AgentTrace storage
        # We don't want to capture the tracer writing its own events!
        if ".agenttrace" in str_path or "agenttrace" in str_path and "worker" in str_path: 
            # (simple heuristic, maybe improves later)
            pass
        if ".agenttrace" in str_path:
             return self.original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
        
        is_writing = 'w' in mode or 'a' in mode or '+' in mode or 'x' in mode
        
        if is_writing:
             # Create VFS File
             # Handle 'a' (append) by reading existing if present
             initial = None
             if self.manager.exists(str_path):
                 initial = self.manager.read_file(str_path)
             
             vfs_file = VFSFile(str_path, mode, initial_content=initial, manager=self.manager)
             return vfs_file
             
        # Reading
        if self.manager.exists(str_path):
             content = self.manager.read_file(str_path)
             return VFSFile(str_path, mode, initial_content=content, manager=self.manager)
        
        # Fallback to real open
        return self.original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
