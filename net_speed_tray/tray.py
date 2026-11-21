"""系统托盘图标与右键菜单。"""

from __future__ import annotations

from typing import Callable

import pystray
from PIL import Image, ImageDraw


def create_tray_image(size: int = 64) -> Image.Image:
    """
    简单黑白托盘图标。
    速度数字只画在浮窗上，避免托盘图标再画一套造成「两个重叠」。
    """
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = size // 8
    black = (0, 0, 0, 255)

    # 下行箭头
    draw.polygon(
        [
            (size // 2, size - margin),
            (margin, size // 2),
            (size - margin, size // 2),
        ],
        fill=black,
    )
    # 上行箭头
    draw.polygon(
        [
            (size // 2, margin),
            (margin, size // 2 - margin // 2),
            (size - margin, size // 2 - margin // 2),
        ],
        fill=black,
    )
    return image


def build_tray_icon(
    *,
    on_toggle_overlay: Callable[[], None],
    on_toggle_autostart: Callable[[], None],
    on_quit: Callable[[], None],
    get_autostart_enabled: Callable[[], bool],
    get_overlay_visible: Callable[[], bool],
) -> pystray.Icon:
    """构建托盘菜单。"""

    def overlay_text(_: pystray.MenuItem) -> str:
        return "隐藏浮窗" if get_overlay_visible() else "显示浮窗"

    def autostart_text(_: pystray.MenuItem) -> str:
        return "取消开机自启" if get_autostart_enabled() else "开机时启动"

    menu = pystray.Menu(
        pystray.MenuItem(overlay_text, lambda: on_toggle_overlay()),
        pystray.MenuItem(autostart_text, lambda: on_toggle_autostart()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", lambda: on_quit()),
    )

    return pystray.Icon(
        name="NetSpeedTray",
        icon=create_tray_image(),
        title="网速监控",
        menu=menu,
    )
