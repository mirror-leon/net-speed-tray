"""网速数值格式化：字节/秒 -> 可读字符串。"""


def format_rate(bytes_per_sec: float) -> str:
    """将字节速率格式化为紧凑文本，便于任务栏旁展示。"""
    value = max(0.0, float(bytes_per_sec))
    units = ("B/s", "KB/s", "MB/s", "GB/s")
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    # 小数位数随量级调整，避免小窗被撑开
    if unit_index == 0:
        text = f"{value:.0f}"
    elif value >= 100:
        text = f"{value:.0f}"
    elif value >= 10:
        text = f"{value:.1f}"
    else:
        text = f"{value:.2f}"

    return f"{text} {units[unit_index]}"
