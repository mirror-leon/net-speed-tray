"""任务栏内网速浮窗：贴托盘、主题色面板；全屏游戏自动隐藏。"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import ImageTk

from . import fullscreen, taskbar_host
from .panel_render import measure_panel_size, render_speed_panel, theme_colors


class SpeedOverlay:
    """嵌在任务栏托盘旁；桌面可见，全屏隐藏。"""

    def __init__(self, on_close: Callable[[], None] | None = None) -> None:
        self._on_close = on_close
        self._user_wants_visible = True
        self._hidden_by_fullscreen = False
        self._width, self._height = measure_panel_size("0 B/s", "0 B/s")
        self._styles_ready = False
        self._last_geometry = ""
        self._photo: ImageTk.PhotoImage | None = None

        bg, _ = theme_colors()
        self._bg_hex = f"#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}"

        self.root = tk.Tk()
        self.root.title("网速监控")
        self.root.overrideredirect(True)
        self.root.configure(bg=self._bg_hex)
        self.root.attributes("-topmost", True)

        self._place_near_tray(force=True)

        self._label = tk.Label(
            self.root,
            bg=self._bg_hex,
            borderwidth=0,
            highlightthickness=0,
        )
        self._label.pack(fill="both", expand=True)
        self.update_speed("0 B/s", "0 B/s")

        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.root.after(80, self._init_win32_styles)
        self.root.after(400, self._tick_visibility)

    def _hwnd(self) -> int:
        try:
            return taskbar_host.resolve_toplevel_hwnd(int(self.root.winfo_id()))
        except tk.TclError:
            return 0

    def _show_on_desktop(self) -> None:
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self._place_near_tray(force=True)
        if self._styles_ready:
            taskbar_host.raise_topmost(self._hwnd())

    def _hide_for_fullscreen(self) -> None:
        self.root.attributes("-topmost", False)
        if self._styles_ready:
            taskbar_host.clear_topmost(self._hwnd())
        self.root.withdraw()

    def _place_near_tray(self, force: bool = False) -> None:
        """钉在任务栏内、系统托盘左侧。"""
        dock = taskbar_host.calc_tray_dock_point(self._width, self._height)
        if dock is not None:
            geometry = f"{self._width}x{self._height}+{dock.x}+{dock.y}"
        else:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            geometry = (
                f"{self._width}x{self._height}+{sw - self._width - 180}+{sh - self._height - 8}"
            )

        if force or geometry != self._last_geometry:
            self.root.geometry(geometry)
            self._last_geometry = geometry

    def _init_win32_styles(self) -> None:
        taskbar_host.apply_overlay_styles(self._hwnd())
        self._styles_ready = True
        self._show_on_desktop()

    def _tick_visibility(self) -> None:
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return

        if self._user_wants_visible:
            busy = fullscreen.is_foreground_fullscreen(exclude_hwnd=self._hwnd())
            if busy:
                if not self._hidden_by_fullscreen:
                    self._hidden_by_fullscreen = True
                    self._hide_for_fullscreen()
            else:
                if self._hidden_by_fullscreen:
                    self._hidden_by_fullscreen = False
                    self._show_on_desktop()
                else:
                    self._place_near_tray(force=False)
                    self.root.attributes("-topmost", True)
                    if self._styles_ready:
                        taskbar_host.raise_topmost(self._hwnd())

        self.root.after(400, self._tick_visibility)

    def update_speed(self, download_text: str, upload_text: str) -> None:
        """按文字重算尺寸并重绘，避免大块留白。"""
        width, height = measure_panel_size(download_text, upload_text)
        size_changed = (width, height) != (self._width, self._height)
        self._width, self._height = width, height

        image = render_speed_panel(download_text, upload_text, width=width, height=height)
        photo = ImageTk.PhotoImage(image)
        self._photo = photo
        self._label.configure(image=photo)

        if size_changed:
            self._place_near_tray(force=True)

    def set_visible(self, visible: bool) -> None:
        self._user_wants_visible = visible
        self._hidden_by_fullscreen = False
        if visible:
            if fullscreen.is_foreground_fullscreen(exclude_hwnd=self._hwnd()):
                self._hidden_by_fullscreen = True
                self._hide_for_fullscreen()
            else:
                self._show_on_desktop()
        else:
            self._hide_for_fullscreen()

    def toggle_visible(self) -> None:
        self.set_visible(not self._user_wants_visible)

    def is_visible(self) -> bool:
        return self._user_wants_visible and not self._hidden_by_fullscreen

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> None:
        self.root.after(delay_ms, callback)

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def _handle_close(self) -> None:
        if self._on_close:
            self._on_close()
        else:
            self.close()
