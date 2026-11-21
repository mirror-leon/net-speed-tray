"""任务栏旁常驻网速浮窗（PIL 面板渲染）。"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import ImageTk

from . import taskbar_host
from .panel_render import CHROMA_HEX, render_speed_panel


class SpeedOverlay:
    """圆角白底黑字面板，钉在系统托盘左侧。"""

    def __init__(self, on_close: Callable[[], None] | None = None) -> None:
        self._on_close = on_close
        self._visible = True
        self._width = 132
        self._height = 48
        self._styles_ready = False
        self._last_geometry = ""
        self._photo: ImageTk.PhotoImage | None = None

        self.root = tk.Tk()
        self.root.title("网速监控")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=CHROMA_HEX)

        try:
            self.root.wm_attributes("-transparentcolor", CHROMA_HEX)
        except tk.TclError:
            pass

        self._place_near_tray(force=True)

        # 用图片标签展示面板，避免 Tk 字体在色键下发虚
        self._label = tk.Label(self.root, bg=CHROMA_HEX, borderwidth=0, highlightthickness=0)
        self._label.pack(fill="both", expand=True)
        self.update_speed("0 B/s", "0 B/s")

        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.root.after(80, self._init_win32_styles)
        self.root.after(500, self._keep_alive)

    def _hwnd(self) -> int:
        try:
            return taskbar_host.resolve_toplevel_hwnd(int(self.root.winfo_id()))
        except tk.TclError:
            return 0

    def _place_near_tray(self, force: bool = False) -> None:
        """定位到托盘左侧。"""
        dock = taskbar_host.calc_tray_dock_point(self._width, self._height)
        if dock is not None:
            geometry = f"{self._width}x{self._height}+{dock.x}+{dock.y}"
        else:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            geometry = (
                f"{self._width}x{self._height}+{sw - self._width - 12}+{sh - self._height - 48}"
            )

        if force or geometry != self._last_geometry:
            self.root.geometry(geometry)
            self._last_geometry = geometry

    def _init_win32_styles(self) -> None:
        taskbar_host.apply_overlay_styles(self._hwnd())
        self._styles_ready = True
        self._place_near_tray(force=True)
        self.root.attributes("-topmost", True)

    def _keep_alive(self) -> None:
        """截屏后恢复置顶。"""
        try:
            if not self.root.winfo_exists():
                return
        except tk.TclError:
            return

        if self._visible:
            self._place_near_tray(force=False)
            self.root.attributes("-topmost", True)
            if self._styles_ready:
                taskbar_host.raise_topmost(self._hwnd())

        self.root.after(500, self._keep_alive)

    def update_speed(self, download_text: str, upload_text: str) -> None:
        """重绘速度面板。"""
        image = render_speed_panel(
            download_text,
            upload_text,
            width=self._width,
            height=self._height,
        )
        photo = ImageTk.PhotoImage(image)
        # 必须挂在实例上，防止被 GC 清掉
        self._photo = photo
        self._label.configure(image=photo)

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        if visible:
            self.root.deiconify()
            self._place_near_tray(force=True)
            self.root.attributes("-topmost", True)
            taskbar_host.raise_topmost(self._hwnd())
        else:
            self.root.withdraw()

    def toggle_visible(self) -> None:
        self.set_visible(not self._visible)

    def is_visible(self) -> bool:
        return self._visible

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
