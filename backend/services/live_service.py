"""
实时采集服务模块

提供连续光谱采集和实时显示功能
"""

import threading
import time
from datetime import datetime
from typing import Callable, List, Optional
import numpy as np

from backend.logging_config import get_logger

log = get_logger(__name__)


class LiveAcquisitionService:
    """
    实时采集服务

    功能:
    - 连续采集光谱数据
    - 支持动态刷新率调节 (0.1-10.0 Hz)
    - 支持暂停/继续
    - 线程安全的数据回调
    """

    def __init__(self, driver):
        """
        初始化实时采集服务

        参数:
            driver: 设备驱动对象
        """
        self.driver = driver
        self.is_live = False
        self.is_paused = False
        self.refresh_rate = 1.0
        self.session_id = None
        self.start_time = None
        self.frame_count = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: List[Callable] = []
        self._mutex = threading.Lock()

    def start(self, refresh_rate: float = 1.0) -> dict:
        """
        启动实时采集

        参数:
            refresh_rate: 刷新率 (Hz), 范围 0.1-10.0

        返回:
            {"success": True/False, "data": {...}, "error": "..."}
        """
        # 参数验证
        if not 0.1 <= refresh_rate <= 10.0:
            return {
                "success": False,
                "error": "刷新率必须在 0.1-10.0 Hz 之间",
                "code": "INVALID_PARAMETER"
            }

        # 检查设备连接
        if not self.driver.is_connected():
            return {
                "success": False,
                "error": "设备未连接",
                "code": "DEVICE_NOT_CONNECTED"
            }

        with self._mutex:
            if self.is_live:
                return {
                    "success": False,
                    "error": "实时采集已在运行中",
                    "code": "ALREADY_RUNNING"
                }

            self.refresh_rate = refresh_rate
            self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
            self.is_live = True
            self.is_paused = False
            self.start_time = time.time()
            self.frame_count = 0
            self._stop_event.clear()

            # 启动采集线程
            self._thread = threading.Thread(
                target=self._acquisition_loop,
                daemon=True,
                name="LiveAcquisition"
            )
            self._thread.start()

            log.info(f"实时采集已启动：session_id={self.session_id}, refresh_rate={refresh_rate}Hz")

            return {
                "success": True,
                "data": {
                    "session_id": self.session_id,
                    "refresh_rate": refresh_rate
                }
            }

    def _acquisition_loop(self):
        """采集循环（后台线程）"""
        interval = 1.0 / self.refresh_rate

        while not self._stop_event.is_set():
            loop_start = time.time()

            if not self.is_paused:
                try:
                    # 采集光谱
                    spectrum = self.driver.acquire_spectrum()

                    # 通知回调
                    with self._mutex:
                        self.frame_count += 1
                        callbacks_copy = self._callbacks.copy()

                    for callback in callbacks_copy:
                        try:
                            callback(spectrum, self.frame_count)
                        except Exception as e:
                            log.error(f"实时采集回调失败：{e}")

                except Exception as e:
                    log.error(f"实时采集失败：{e}")

            # 控制刷新率
            elapsed = time.time() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)

        log.info("实时采集线程已退出")

    def stop(self) -> dict:
        """
        停止实时采集

        返回:
            {"success": True/False, "error": "..."}
        """
        with self._mutex:
            if not self.is_live:
                return {
                    "success": False,
                    "error": "实时采集未运行",
                    "code": "NOT_RUNNING"
                }

            self.is_live = False
            self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        log.info(f"实时采集已停止：session_id={self.session_id}, total_frames={self.frame_count}")

        return {"success": True}

    def pause(self, paused: bool) -> dict:
        """
        暂停/继续实时采集

        参数:
            paused: True=暂停，False=继续

        返回:
            {"success": True/False, "error": "..."}
        """
        with self._mutex:
            if not self.is_live:
                return {
                    "success": False,
                    "error": "实时采集未运行",
                    "code": "NOT_RUNNING"
                }

            self.is_paused = paused

        status = "暂停" if paused else "继续"
        log.info(f"实时采集已{status}")

        return {"success": True}

    def get_status(self) -> dict:
        """
        获取实时采集状态

        返回:
            {
                "is_live": bool,
                "is_paused": bool,
                "refresh_rate": float,
                "elapsed_time": float,  # 秒
                "frame_count": int
            }
        """
        with self._mutex:
            elapsed = time.time() - self.start_time if self.start_time and self.is_live else 0

            return {
                "is_live": self.is_live,
                "is_paused": self.is_paused,
                "refresh_rate": self.refresh_rate,
                "elapsed_time": elapsed,
                "frame_count": self.frame_count
            }

    def set_refresh_rate(self, refresh_rate: float) -> dict:
        """
        动态调节刷新率

        参数:
            refresh_rate: 刷新率 (Hz), 范围 0.1-10.0

        返回:
            {"success": True/False, "error": "..."}
        """
        if not 0.1 <= refresh_rate <= 10.0:
            return {
                "success": False,
                "error": "刷新率必须在 0.1-10.0 Hz 之间",
                "code": "INVALID_PARAMETER"
            }

        with self._mutex:
            self.refresh_rate = refresh_rate

        log.info(f"实时采集刷新率已更新：{refresh_rate}Hz")

        return {"success": True}

    def add_callback(self, callback: Callable):
        """
        添加数据回调

        参数:
            callback: 回调函数 (spectrum, frame_count) -> None
        """
        with self._mutex:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
                log.debug(f"添加实时采集回调：{callback}")

    def remove_callback(self, callback: Callable):
        """
        移除数据回调

        参数:
            callback: 要移除的回调函数
        """
        with self._mutex:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                log.debug(f"移除实时采集回调：{callback}")
