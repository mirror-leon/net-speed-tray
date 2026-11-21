"""网速面板渲染：PIL 超采样绘制，文字清晰不发虚。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 圆角外镂空色（给 Tk -transparentcolor 用）
CHROMA_RGB = (1, 2, 3)
CHROMA_HEX = "#010203"
PANEL_BG = (255, 255, 255, 250)
PANEL_BORDER = (210, 210, 210, 255)
TEXT_RGBA = (0, 0, 0, 255)


def _font(size: int) -> ImageFont.ImageFont:
    """加载清晰的系统 UI 字体。"""
    windir = Path(r"C:\Windows\Fonts")
    for name in ("segoeui.ttf", "msyh.ttc", "arial.ttf"):
        path = windir / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_speed_panel(
    download_text: str,
    upload_text: str,
    *,
    width: int = 132,
    height: int = 48,
    scale: int = 3,
) -> Image.Image:
    """渲染圆角白底、纯黑字的速度面板（RGB，圆角外为色键）。"""
    tw, th = width * scale, height * scale
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(
        (scale, scale, tw - scale - 1, th - scale - 1),
        radius=12 * scale,
        fill=PANEL_BG,
        outline=PANEL_BORDER,
        width=max(1, scale),
    )

    font = _font(12 * scale)
    line1 = f"↓  {download_text}"
    line2 = f"↑  {upload_text}"

    bbox1 = draw.textbbox((0, 0), line1, font=font)
    bbox2 = draw.textbbox((0, 0), line2, font=font)
    h1 = bbox1[3] - bbox1[1]
    h2 = bbox2[3] - bbox2[1]
    gap = 3 * scale
    total_h = h1 + h2 + gap
    x = 14 * scale
    y = (th - total_h) // 2 - bbox1[1]

    draw.text((x, y), line1, font=font, fill=TEXT_RGBA)
    draw.text((x, y + h1 + gap), line2, font=font, fill=TEXT_RGBA)

    panel = canvas.resize((width, height), Image.Resampling.LANCZOS)

    # 半透明边缘先合到白底，保证字和圆角抗锯齿正常；全透明区改色键
    white = Image.new("RGBA", panel.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(white, panel)
    alpha = panel.getchannel("A")
    mask = alpha.point(lambda a: 255 if a > 16 else 0)

    result = Image.new("RGB", panel.size, CHROMA_RGB)
    result.paste(flattened.convert("RGB"), (0, 0), mask)
    return result
