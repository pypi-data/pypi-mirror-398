"""
Subprocess Sandboxing for VFS Isolation

This module patches subprocess.run(), subprocess.Popen(), and os.system()
to prevent scripts from escaping the VFS sandbox.
"""
import subprocess
import os

# Store originals
_original_run = subprocess.run
_original_popen = subprocess.Popen
_original_system = os.system
_original_execv = os.execv
_original_execve = os.execve

_sandbox_enabled = False

class SubprocessBlockedError(PermissionError):
    """Raised when subprocess calls are blocked in sandbox mode."""
    pass

def _blocked_run(*args, **kwargs):
    if _sandbox_enabled:
        raise SubprocessBlockedError(
            "subprocess.run() is disabled in sandbox mode. "
            "External process execution is not allowed during replay."
        )
    return _original_run(*args, **kwargs)

def _blocked_popen(*args, **kwargs):
    if _sandbox_enabled:
        raise SubprocessBlockedError(
            "subprocess.Popen() is disabled in sandbox mode. "
            "External process execution is not allowed during replay."
        )
    return _original_popen(*args, **kwargs)

def _blocked_system(command):
    if _sandbox_enabled:
        raise SubprocessBlockedError(
            "os.system() is disabled in sandbox mode. "
            "External process execution is not allowed during replay."
        )
    return _original_system(command)

def _blocked_execv(path, args):
    if _sandbox_enabled:
        raise SubprocessBlockedError(
            "os.execv() is disabled in sandbox mode. "
            "External process execution is not allowed during replay."
        )
    return _original_execv(path, args)

def _blocked_execve(path, args, env):
    if _sandbox_enabled:
        raise SubprocessBlockedError(
            "os.execve() is disabled in sandbox mode. "
            "External process execution is not allowed during replay."
        )
    return _original_execve(path, args, env)

def enable_sandbox():
    """Enable subprocess sandboxing - blocks all process creation."""
    global _sandbox_enabled
    _sandbox_enabled = True
    subprocess.run = _blocked_run
    subprocess.Popen = _blocked_popen
    os.system = _blocked_system
    os.execv = _blocked_execv
    os.execve = _blocked_execve
    print("[AgentTrace] 🔒 Subprocess sandbox enabled")

def disable_sandbox():
    """Disable subprocess sandboxing - restore original functions."""
    global _sandbox_enabled
    _sandbox_enabled = False
    subprocess.run = _original_run
    subprocess.Popen = _original_popen
    os.system = _original_system
    os.execv = _original_execv
    os.execve = _original_execve
    print("[AgentTrace] 🔓 Subprocess sandbox disabled")

def is_sandbox_enabled():
    """Check if sandbox is currently enabled."""
    return _sandbox_enabled
