"""网速面板渲染：贴合任务栏风格的紧凑黑字面板。"""

from __future__ import annotations

import winreg
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _is_light_taskbar() -> bool:
    """读取系统任务栏浅色/深色主题。"""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            return int(value) == 1
    except OSError:
        return True


def _font(size: int) -> ImageFont.ImageFont:
    windir = Path(r"C:\Windows\Fonts")
    for name in ("segoeui.ttf", "segoeuisl.ttf", "msyh.ttc", "arial.ttf"):
        path = windir / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def theme_colors() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """返回 (背景色, 文字色)。浅色任务栏用近白底黑字。"""
    if _is_light_taskbar():
        return (243, 243, 243), (0, 0, 0)
    # 深色任务栏：仍用黑字会看不清，改用浅灰字；背景贴近任务栏
    return (44, 44, 44), (240, 240, 240)


def measure_panel_size(
    download_text: str,
    upload_text: str,
    *,
    scale: int = 2,
) -> tuple[int, int]:
    """按文字内容估算面板宽高。"""
    font = _font(11 * scale)
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    line1 = f"↓ {download_text}"
    line2 = f"↑ {upload_text}"
    b1 = dummy.textbbox((0, 0), line1, font=font)
    b2 = dummy.textbbox((0, 0), line2, font=font)
    text_w = max(b1[2] - b1[0], b2[2] - b2[0])
    text_h = (b1[3] - b1[1]) + (b2[3] - b2[1]) + 2 * scale
    width = (text_w + 16 * scale) // scale
    height = (text_h + 10 * scale) // scale
    return max(width, 88), max(height, 34)


def render_speed_panel(
    download_text: str,
    upload_text: str,
    *,
    width: int | None = None,
    height: int | None = None,
    scale: int = 2,
) -> Image.Image:
    """
    渲染紧凑面板：保留字体抗锯齿，背景贴近任务栏，不再用透明色键咬字。
    """
    bg, fg = theme_colors()
    auto_w, auto_h = measure_panel_size(download_text, upload_text, scale=scale)
    width = width or auto_w
    height = height or auto_h

    tw, th = width * scale, height * scale
    image = Image.new("RGB", (tw, th), bg)
    draw = ImageDraw.Draw(image)
    font = _font(11 * scale)

    line1 = f"↓ {download_text}"
    line2 = f"↑ {upload_text}"
    b1 = draw.textbbox((0, 0), line1, font=font)
    b2 = draw.textbbox((0, 0), line2, font=font)
    h1 = b1[3] - b1[1]
    h2 = b2[3] - b2[1]
    gap = 2 * scale
    total_h = h1 + h2 + gap
    x = 8 * scale
    y = (th - total_h) // 2 - b1[1]

    draw.text((x, y), line1, font=font, fill=fg)
    draw.text((x, y + h1 + gap), line2, font=font, fill=fg)

    return image.resize((width, height), Image.Resampling.LANCZOS)
