"""单实例锁：防止多开导致托盘正确、浮窗残留显示 0。"""

from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183
_kernel32 = ctypes.windll.kernel32
_mutex_handle = None


def acquire(name: str = "Local\\NetSpeedTraySingleton") -> bool:
    """
    获取命名互斥量。
    返回 True 表示当前进程是唯一实例；False 表示已有实例在跑。
    """
    global _mutex_handle
    handle = _kernel32.CreateMutexW(None, False, name)
    if not handle:
        return False
    _mutex_handle = handle
    if _kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        return False

    def _release() -> None:
        if _mutex_handle:
            _kernel32.ReleaseMutex(_mutex_handle)
            _kernel32.CloseHandle(_mutex_handle)

    atexit.register(_release)
    return True
