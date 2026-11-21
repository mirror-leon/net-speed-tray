"""网速托盘监控入口。"""

import sys

from net_speed_tray.app import NetSpeedApp
from net_speed_tray.instance_lock import acquire


def main() -> None:
    # 禁止多开：旧浮窗残留会一直显示 0，而新托盘是正确的
    if not acquire():
        print("网速监控已在运行。", file=sys.stderr)
        sys.exit(0)

    app = NetSpeedApp(refresh_ms=1000)
    app.run()


if __name__ == "__main__":
    main()
