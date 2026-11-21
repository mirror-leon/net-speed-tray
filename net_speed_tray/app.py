"""应用编排：把采样、浮窗、托盘、开机自启拼在一起。"""

from __future__ import annotations

import threading
from typing import Optional

from . import autostart
from .formatter import format_rate
from .overlay import SpeedOverlay
from .speed import NetSpeedMonitor
from .tray import build_tray_icon


class NetSpeedApp:
    """网速监控主应用，负责生命周期与模块协作。"""

    def __init__(self, refresh_ms: int = 1000) -> None:
        self._refresh_ms = refresh_ms
        self._monitor = NetSpeedMonitor()
        self._overlay = SpeedOverlay(on_close=self.quit)
        self._tray = None
        self._tray_thread: Optional[threading.Thread] = None
        self._stopping = False

        # 默认开启开机自启
        if not autostart.is_enabled():
            try:
                autostart.enable()
            except OSError:
                pass

        self._tray = build_tray_icon(
            on_toggle_overlay=self._toggle_overlay,
            on_toggle_autostart=self._toggle_autostart,
            on_quit=self.quit,
            get_autostart_enabled=autostart.is_enabled,
            get_overlay_visible=self._overlay.is_visible,
        )

    def run(self) -> None:
        """启动托盘线程并进入浮窗主循环。"""
        assert self._tray is not None
        self._tray_thread = threading.Thread(target=self._tray.run, name="tray", daemon=True)
        self._tray_thread.start()
        self._tick()
        self._overlay.run()

    def _tick(self) -> None:
        """定时采样并同步刷新浮窗 / 托盘提示 / 托盘图标。"""
        if self._stopping:
            return

        sample = self._monitor.sample()
        down_text = format_rate(sample.download_bps)
        up_text = format_rate(sample.upload_bps)

        # 浮窗与托盘用同一份采样，避免两边不一致
        self._overlay.update_speed(down_text, up_text)

        # 速度只显示在浮窗；托盘仅保留悬停提示，避免两套数字叠在一起
        if self._tray is not None:
            self._tray.title = f"↓ {down_text}  ↑ {up_text}"

        self._overlay.schedule(self._refresh_ms, self._tick)

    def _toggle_overlay(self) -> None:
        self._overlay.schedule(0, self._overlay.toggle_visible)

    def _toggle_autostart(self) -> None:
        if autostart.is_enabled():
            autostart.disable()
        else:
            autostart.enable()

    def quit(self) -> None:
        """退出托盘与浮窗。"""
        if self._stopping:
            return
        self._stopping = True

        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass

        self._overlay.schedule(0, self._overlay.close)
