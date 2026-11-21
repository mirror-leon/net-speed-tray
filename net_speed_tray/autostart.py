"""开机自启：通过当前用户 Startup 目录注册/取消。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "NetSpeedTray"
STARTUP_BAT_NAME = f"{APP_NAME}.bat"


def _startup_dir() -> Path:
    """返回当前用户的开机启动目录。"""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("无法定位 APPDATA，无法配置开机自启。")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_shortcut_path() -> Path:
    """开机启动脚本完整路径。"""
    return _startup_dir() / STARTUP_BAT_NAME


def _pythonw_path() -> Path:
    """优先使用 pythonw，避免开机时弹出黑框。"""
    candidate = Path(sys.executable).with_name("pythonw.exe")
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def _entry_script() -> Path:
    """定位项目入口 main.py。"""
    return Path(__file__).resolve().parent.parent / "main.py"


def is_enabled() -> bool:
    """是否已启用开机自启。"""
    return startup_shortcut_path().exists()


def enable() -> Path:
    """写入 Startup 启动脚本并返回路径。"""
    startup = _startup_dir()
    startup.mkdir(parents=True, exist_ok=True)

    pythonw = _pythonw_path()
    entry = _entry_script()
    bat_path = startup_shortcut_path()

    # 使用 /d 切换盘符，保证从任意目录启动都能找到脚本
    content = (
        "@echo off\r\n"
        f'cd /d "{entry.parent}"\r\n'
        f'start "" "{pythonw}" "{entry}"\r\n'
    )
    bat_path.write_text(content, encoding="gbk", errors="ignore")
    return bat_path


def disable() -> None:
    """删除 Startup 启动脚本。"""
    path = startup_shortcut_path()
    if path.exists():
        path.unlink()
