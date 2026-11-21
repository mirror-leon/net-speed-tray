# 网速托盘监控（Net Speed Tray）

Windows 任务栏旁常驻显示实时上传/下载速度，支持系统托盘菜单与开机自启。

## 功能

- 任务栏托盘旁常驻圆角面板（白底黑字）
- 系统托盘图标，悬停可看当前速度
- 右键菜单：显示/隐藏浮窗、开机自启、退出
- 首次运行默认写入开机启动项
- 单实例运行，避免多开叠窗

## 安装

```powershell
git clone https://github.com/mirror-leon/net-speed-tray.git
cd net-speed-tray
python -m pip install -r requirements.txt
```

## 运行

```powershell
python main.py
```

或双击 `start.bat`（无黑框，推荐）。

## 开机自启

首次启动会自动启用。也可在托盘图标右键菜单中切换「开机时启动 / 取消开机自启」。

## 模块说明

| 模块 | 职责 |
| --- | --- |
| `net_speed_tray/speed.py` | 网速采样 |
| `net_speed_tray/formatter.py` | 速率格式化 |
| `net_speed_tray/panel_render.py` | 速度面板绘制 |
| `net_speed_tray/overlay.py` | 任务栏旁浮窗 |
| `net_speed_tray/tray.py` | 托盘图标与菜单 |
| `net_speed_tray/autostart.py` | 开机自启 |
| `net_speed_tray/taskbar_host.py` | 托盘旁定位 |
| `net_speed_tray/instance_lock.py` | 单实例锁 |
| `net_speed_tray/app.py` | 应用编排 |
