"""
profile-me: Enable external profiler attachment for Python processes
=====================================================================

This library provides a simple way to allow external profilers like Yantra,
py-spy, or gdb to attach to your Python process on Linux systems with
restricted ptrace (the default on most distributions).

Usage:
    import profile_me
    profile_me.enable_profiling()

Or as a one-liner at the top of your script:
    __import__('profile_me').enable_profiling()

This must be called early in your program, before the profiler attempts
to attach.
"""

__version__ = "0.1.0"
__all__ = ["enable_profiling", "is_profiling_enabled", "get_pid"]

import os
import sys
import ctypes
from typing import Optional

# Linux prctl constants
PR_SET_PTRACER = 0x59616D61  # "Yama" in hex
PR_SET_PTRACER_ANY = 0xFFFFFFFF  # Allow any process to ptrace

# Track state
_profiling_enabled = False
_libc: Optional[ctypes.CDLL] = None


def _get_libc() -> Optional[ctypes.CDLL]:
    """Get a handle to libc."""
    global _libc
    if _libc is None:
        try:
            _libc = ctypes.CDLL(None)
        except OSError:
            return None
    return _libc


def enable_profiling(quiet: bool = False) -> bool:
    """
    Enable external profiler attachment for this process.

    On Linux with Yama LSM (most modern distributions), processes cannot
    be ptraced by non-parent processes by default. This function calls
    prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY) to allow any process owned
    by the same user to attach.

    Args:
        quiet: If True, suppress the informational message.

    Returns:
        True if profiling was enabled successfully, False otherwise.

    Example:
        >>> import profile_me
        >>> profile_me.enable_profiling()
        [profile-me] Profiling enabled for PID 12345
        True
    """
    global _profiling_enabled

    # Already enabled
    if _profiling_enabled:
        return True

    # Only works on Linux
    if sys.platform != "linux":
        if not quiet:
            print(f"[profile-me] Not on Linux ({sys.platform}), skipping", file=sys.stderr)
        return False

    # Get libc
    libc = _get_libc()
    if libc is None:
        if not quiet:
            print("[profile-me] Could not load libc", file=sys.stderr)
        return False

    # Call prctl
    try:
        result = libc.prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY, 0, 0, 0)
        if result == 0:
            _profiling_enabled = True
            if not quiet:
                print(f"[profile-me] Profiling enabled for PID {os.getpid()}", file=sys.stderr)
            return True
        else:
            if not quiet:
                print(f"[profile-me] prctl failed with code {result}", file=sys.stderr)
            return False
    except Exception as e:
        if not quiet:
            print(f"[profile-me] Error: {e}", file=sys.stderr)
        return False


def is_profiling_enabled() -> bool:
    """
    Check if profiling has been enabled for this process.

    Returns:
        True if enable_profiling() was called successfully.
    """
    return _profiling_enabled


def get_pid() -> int:
    """
    Get the current process ID.

    Convenience function for use with profiler attach commands.

    Returns:
        The current process ID.

    Example:
        >>> import profile_me
        >>> profile_me.enable_profiling()
        >>> print(f"Attach with: yantra attach {profile_me.get_pid()}")
    """
    return os.getpid()


# Context manager for scoped profiling
class profiling_enabled:
    """
    Context manager to enable profiling for a block of code.

    Note: Once enabled, profiling cannot be disabled for the process.
    This context manager is provided for clarity of intent.

    Example:
        with profile_me.profiling_enabled():
            # Long-running code that you want to profile
            run_computation()
    """

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def __enter__(self):
        enable_profiling(quiet=self.quiet)
        return self

    def __exit__(self, *args):
        # Cannot disable ptrace allowance, but that's fine
        pass


# Auto-enable via environment variable
if os.environ.get("PROFILE_ME", "").lower() in ("1", "true", "yes"):
    enable_profiling(quiet=os.environ.get("PROFILE_ME_QUIET", "").lower() in ("1", "true", "yes"))
