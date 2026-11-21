"""网速采样模块：基于系统累计流量差计算上下行速率。"""

from __future__ import annotations

import time
from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class SpeedSample:
    """一次网速采样结果。"""

    download_bps: float
    upload_bps: float
    timestamp: float


class NetSpeedMonitor:
    """通过两次网卡计数器差值计算实时上下行速度。"""

    def __init__(self) -> None:
        self._last_sent = 0
        self._last_recv = 0
        self._last_time = 0.0
        # 首次调用只建立基线，不产生有效速率
        self._primed = False
        self.reset()

    def reset(self) -> None:
        """重置基线，避免休眠/换网后出现异常尖峰。"""
        counters = psutil.net_io_counters()
        self._last_sent = counters.bytes_sent
        self._last_recv = counters.bytes_recv
        self._last_time = time.perf_counter()
        self._primed = False

    def sample(self) -> SpeedSample:
        """采样并返回下载/上传字节每秒。"""
        counters = psutil.net_io_counters()
        now = time.perf_counter()
        elapsed = max(now - self._last_time, 1e-6)

        sent = counters.bytes_sent
        recv = counters.bytes_recv

        # 计数器回绕或网卡重置时重新打基线
        if sent < self._last_sent or recv < self._last_recv:
            self._last_sent = sent
            self._last_recv = recv
            self._last_time = now
            self._primed = True
            return SpeedSample(0.0, 0.0, now)

        download_bps = (recv - self._last_recv) / elapsed
        upload_bps = (sent - self._last_sent) / elapsed

        self._last_sent = sent
        self._last_recv = recv
        self._last_time = now

        if not self._primed:
            self._primed = True
            return SpeedSample(0.0, 0.0, now)

        return SpeedSample(download_bps, upload_bps, now)
