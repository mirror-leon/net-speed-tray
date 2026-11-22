"""任务栏定位：只负责算托盘旁坐标，不改窗口父子关系。"""

from __future__ import annotations

from ctypes import byref, windll, wintypes
from dataclasses import dataclass


user32 = windll.user32

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SW_SHOWNOACTIVATE = 4
GA_ROOT = 2
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class Point:
    x: int
    y: int


def _window_rect(hwnd: int) -> Rect | None:
    if not hwnd:
        return None
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, byref(rect)):
        return None
    return Rect(rect.left, rect.top, rect.right, rect.bottom)


def resolve_toplevel_hwnd(raw_hwnd: int) -> int:
    """把 Tk 控件句柄提升到顶层窗口句柄。"""
    if not raw_hwnd:
        return 0
    root = int(user32.GetAncestor(raw_hwnd, GA_ROOT) or 0)
    return root or int(raw_hwnd)


def find_taskbar_hwnd() -> int:
    return int(user32.FindWindowW("Shell_TrayWnd", None) or 0)


def find_tray_notify_hwnd(taskbar_hwnd: int) -> int:
    if not taskbar_hwnd:
        return 0
    return int(user32.FindWindowExW(taskbar_hwnd, None, "TrayNotifyWnd", None) or 0)


def calc_tray_dock_point(width: int, height: int) -> Point | None:
    """计算嵌在任务栏内、系统托盘左侧的屏幕坐标。"""
    taskbar = find_taskbar_hwnd()
    taskbar_rect = _window_rect(taskbar)
    if taskbar_rect is None:
        return None

    notify = find_tray_notify_hwnd(taskbar)
    notify_rect = _window_rect(notify) if notify else None

    # 紧贴 TrayNotifyWnd 左侧，垂直在任务栏内居中（像托盘扩展）
    if notify_rect is not None:
        x = notify_rect.left - width - 2
    else:
        x = taskbar_rect.right - width - 160

    y = taskbar_rect.top + max(0, (taskbar_rect.height - height) // 2)

    if x < taskbar_rect.left + 4:
        x = taskbar_rect.left + 4
    return Point(int(x), int(y))


def apply_overlay_styles(hwnd: int) -> None:
    """工具窗口 + 不抢焦点。透明由 Tk transparentcolor 处理，避免再加 LAYERED 造成叠影。"""
    hwnd = resolve_toplevel_hwnd(hwnd)
    if not hwnd:
        return
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    # 不强制 WS_EX_LAYERED：与 transparentcolor 叠用时 Win+Shift+S 下容易出现「两个重叠」
    style = (style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~0x00040000
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def clear_topmost(hwnd: int) -> None:
    """取消置顶，避免浮窗盖住游戏/全屏应用。"""
    hwnd = resolve_toplevel_hwnd(hwnd)
    if not hwnd:
        return
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if style & WS_EX_TOPMOST:
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TOPMOST)
    user32.SetWindowPos(
        hwnd,
        HWND_NOTOPMOST,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )


def raise_topmost(hwnd: int) -> None:
    """桌面场景下置顶，保证能看见；全屏时应先 hide 再 clear_topmost。"""
    hwnd = resolve_toplevel_hwnd(hwnd)
    if not hwnd:
        return
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)


def is_window_visible(hwnd: int) -> bool:
    hwnd = resolve_toplevel_hwnd(hwnd)
    if not hwnd:
        return False
    return bool(user32.IsWindowVisible(hwnd))
