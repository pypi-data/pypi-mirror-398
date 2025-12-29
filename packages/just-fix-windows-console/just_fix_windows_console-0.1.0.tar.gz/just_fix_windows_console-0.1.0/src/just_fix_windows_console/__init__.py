"""
just_fix_windows_console.py

Enable Windows console Virtual Terminal (VT) processing on stdout/stderr.
"""

from __future__ import annotations

import os
import ctypes
from ctypes import wintypes
from functools import lru_cache
from typing import Final, TypedDict

JUST_FIX_WINDOWS_CONSOLE_ERROR = None

# Win32 constants
STD_OUTPUT_HANDLE: Final[int] = -11
STD_ERROR_HANDLE: Final[int] = -12

ENABLE_PROCESSED_OUTPUT: Final[int] = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING: Final[int] = 0x0004

INVALID_HANDLE_VALUE: Final[int] = wintypes.HANDLE(-1).value


class VTStatus(TypedDict):
    stdout: bool
    stderr: bool


@lru_cache(maxsize=1)
def _winapi():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    get_std_handle = kernel32.GetStdHandle
    get_std_handle.argtypes = [wintypes.DWORD]
    get_std_handle.restype = wintypes.HANDLE

    get_console_mode = kernel32.GetConsoleMode
    get_console_mode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    get_console_mode.restype = wintypes.BOOL

    set_console_mode = kernel32.SetConsoleMode
    set_console_mode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    set_console_mode.restype = wintypes.BOOL

    return get_std_handle, get_console_mode, set_console_mode


def _enable_vt_on_std_handle(std_handle_id: int) -> bool:
    """
    Enable ENABLE_VIRTUAL_TERMINAL_PROCESSING on the given std handle (stdout/stderr).
    """
    if os.name != "nt":
        return False

    GetStdHandle, GetConsoleMode, SetConsoleMode = _winapi()

    h = GetStdHandle(std_handle_id)  # let ctypes do the DWORD conversion/wrap
    if not h or h == INVALID_HANDLE_VALUE:
        return False

    mode = wintypes.DWORD()
    if not GetConsoleMode(h, ctypes.byref(mode)):
        return False

    desired = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_OUTPUT
    if desired == mode.value:
        return True

    if not SetConsoleMode(h, desired):  # pass int, matches argtypes cleanly
        global JUST_FIX_WINDOWS_CONSOLE_ERROR
        JUST_FIX_WINDOWS_CONSOLE_ERROR = ctypes.get_last_error()
        return False

    return True


def just_fix_windows_console() -> VTStatus:
    """
    Try to enable VT processing on stdout and stderr.
    """
    if os.name != "nt":
        return {"stdout": False, "stderr": False}

    return {
        "stdout": _enable_vt_on_std_handle(STD_OUTPUT_HANDLE),
        "stderr": _enable_vt_on_std_handle(STD_ERROR_HANDLE),
    }
