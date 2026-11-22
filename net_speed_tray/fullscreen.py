"""检测前台是否有全屏应用（游戏等），用于自动隐藏浮窗。"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from .taskbar_host import Rect, _window_rect


user32 = ctypes.windll.user32

MONITOR_DEFAULTTONEAREST = 2

# 桌面/任务栏相关窗口，不算「挡住桌面的全屏应用」
_SHELL_CLASSES = {
    "Progman",
    "WorkerW",
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "NotifyIconOverflowWindow",
    "Windows.UI.Core.CoreWindow",  # 部分系统 UI
}


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _monitor_rect(hwnd: int) -> Rect | None:
    """前台窗口所在显示器的完整区域（含任务栏）。"""
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not monitor:
        return None
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return None
    r = info.rcMonitor
    return Rect(r.left, r.top, r.right, r.bottom)


def is_foreground_fullscreen(*, exclude_hwnd: int = 0) -> bool:
    """
    前台窗口是否几乎铺满整块屏幕（独占全屏 / 无边框全屏）。
    桌面与任务栏本身返回 False。
    """
    hwnd = int(user32.GetForegroundWindow() or 0)
    if not hwnd or hwnd == exclude_hwnd:
        return False

    cls = _class_name(hwnd)
    if cls in _SHELL_CLASSES:
        return False

    win = _window_rect(hwnd)
    mon = _monitor_rect(hwnd)
    if win is None or mon is None:
        return False

    # 允许少量像素误差（多显示器/DPI）
    tol = 8
    covers = (
        abs(win.left - mon.left) <= tol
        and abs(win.top - mon.top) <= tol
        and abs(win.right - mon.right) <= tol
        and abs(win.bottom - mon.bottom) <= tol
    )
    return covers
