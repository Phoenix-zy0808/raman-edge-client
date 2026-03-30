"""
状态管理器模块
统一管理应用程序状态，避免状态和行为分离
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtCore import QObject, Signal


class AcquisitionState(Enum):
    """采集状态"""
    IDLE = 'idle'           # 空闲
    RUNNING = 'running'     # 采集中
    PAUSED = 'paused'       # 暂停


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = 'disconnected'  # 未连接
    CONNECTING = 'connecting'      # 连接中
    CONNECTED = 'connected'        # 已连接
    ERROR = 'error'                # 错误


@dataclass
class AppState:
    """应用程序状态数据类"""
    connection: ConnectionState = ConnectionState.DISCONNECTED
    acquisition: AcquisitionState = AcquisitionState.IDLE
    device_state: str = 'normal'
    noise_level: float = 0.02
    sample_rate: float = 10.0
    error_message: Optional[str] = None
    
    @property
    def is_connected(self) -> bool:
        return self.connection == ConnectionState.CONNECTED
    
    @property
    def is_acquiring(self) -> bool:
        return self.acquisition == AcquisitionState.RUNNING


class StateManager(QObject):
    """
    状态管理器

    统一管理应用程序状态，通过信号通知状态变化
    避免多个对象共享状态导致的线程安全问题
    """

    # 状态变化信号
    connectionChanged = Signal(ConnectionState)
    acquisitionChanged = Signal(AcquisitionState)
    deviceStateChanged = Signal(str)
    noiseLevelChanged = Signal(float)
    sampleRateChanged = Signal(float)
    errorOccurred = Signal(str)

    # 参数变化信号（P0 修复：通知所有监听者参数已更新）
    integrationTimeChanged = Signal(int)
    accumulationCountChanged = Signal(int)
    smoothingWindowChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = AppState()
        self._params = {
            'integration_time': 100,
            'accumulation_count': 1,
            'smoothing_window': 0,
        }
    
    @property
    def state(self) -> AppState:
        """获取当前状态"""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        return self._state.is_connected
    
    @property
    def is_acquiring(self) -> bool:
        return self._state.is_acquiring

    def set_integration_time(self, time_ms: int) -> None:
        """设置积分时间"""
        old_value = self._params['integration_time']
        self._params['integration_time'] = int(time_ms)
        if old_value != self._params['integration_time']:
            self.integrationTimeChanged.emit(self._params['integration_time'])

    def set_accumulation_count(self, count: int) -> None:
        """设置累加平均次数"""
        old_value = self._params['accumulation_count']
        self._params['accumulation_count'] = int(count)
        if old_value != self._params['accumulation_count']:
            self.accumulationCountChanged.emit(self._params['accumulation_count'])

    def set_smoothing_window(self, window: int) -> None:
        """设置平滑窗口"""
        old_value = self._params['smoothing_window']
        self._params['smoothing_window'] = int(window)
        if old_value != self._params['smoothing_window']:
            self.smoothingWindowChanged.emit(self._params['smoothing_window'])
    
    def connect_device(self) -> None:
        """设置连接中状态"""
        self._state.connection = ConnectionState.CONNECTING
        self.connectionChanged.emit(self._state.connection)

    def set_connected(self, success: bool, error_message: Optional[str] = None) -> None:
        """设置连接结果"""
        if success:
            self._state.connection = ConnectionState.CONNECTED
            self._state.error_message = None
        else:
            self._state.connection = ConnectionState.ERROR
            self._state.error_message = error_message or "连接失败"
        self.connectionChanged.emit(self._state.connection)
    
    def disconnect_device(self) -> None:
        """断开连接"""
        self._state.connection = ConnectionState.DISCONNECTED
        self._state.acquisition = AcquisitionState.IDLE
        self._state.error_message = None
        self.connectionChanged.emit(self._state.connection)
        self.acquisitionChanged.emit(self._state.acquisition)
    
    def start_acquisition(self) -> bool:
        """开始采集"""
        if not self._state.is_connected:
            return False
        self._state.acquisition = AcquisitionState.RUNNING
        self.acquisitionChanged.emit(self._state.acquisition)
        return True
    
    def stop_acquisition(self) -> None:
        """停止采集"""
        self._state.acquisition = AcquisitionState.IDLE
        self.acquisitionChanged.emit(self._state.acquisition)
    
    def set_device_state(self, state: str) -> None:
        """设置设备状态"""
        self._state.device_state = state
        self.deviceStateChanged.emit(state)
    
    def set_noise_level(self, level: float) -> None:
        """设置噪声水平"""
        self._state.noise_level = level
        self.noiseLevelChanged.emit(level)
    
    def set_sample_rate(self, rate: float) -> None:
        """设置采样率"""
        self._state.sample_rate = rate
        self.sampleRateChanged.emit(rate)

    def report_error(self, message: str) -> None:
        """报告错误"""
        self._state.error_message = message
        self.errorOccurred.emit(message)


# ==================== P11 新增：校准状态管理 ====================

@dataclass
class CalibrationState:
    """校准状态数据类"""
    wavelength_calibrated: bool = False
    wavelength_correction: float = 0.0
    wavelength_calibration_time: Optional[float] = None
    
    intensity_calibrated: bool = False
    intensity_correction_curve: Optional[list] = None
    intensity_calibration_time: Optional[float] = None
    
    auto_exposure_enabled: bool = False
    auto_exposure_target: float = 0.7


class CalibrationStateManager:
    """
    校准状态管理器
    
    统一管理波长校准、强度校准、自动曝光的状态
    """
    
    def __init__(self):
        self._state = CalibrationState()
    
    @property
    def state(self) -> CalibrationState:
        return self._state
    
    @property
    def is_wavelength_calibrated(self) -> bool:
        return self._state.wavelength_calibrated
    
    @property
    def wavelength_correction(self) -> float:
        return self._state.wavelength_correction
    
    @property
    def is_intensity_calibrated(self) -> bool:
        return self._state.intensity_calibrated
    
    @property
    def is_auto_exposure_enabled(self) -> bool:
        return self._state.auto_exposure_enabled
    
    def set_wavelength_calibrated(self, correction: float, calibration_time: float) -> None:
        """设置波长校准状态"""
        self._state.wavelength_calibrated = True
        self._state.wavelength_correction = correction
        self._state.wavelength_calibration_time = calibration_time
    
    def reset_wavelength_calibration(self) -> None:
        """重置波长校准"""
        self._state.wavelength_calibrated = False
        self._state.wavelength_correction = 0.0
        self._state.wavelength_calibration_time = None
    
    def set_intensity_calibrated(self, correction_curve: list, calibration_time: float) -> None:
        """设置强度校准状态"""
        self._state.intensity_calibrated = True
        self._state.intensity_correction_curve = correction_curve
        self._state.intensity_calibration_time = calibration_time
    
    def reset_intensity_calibration(self) -> None:
        """重置强度校准"""
        self._state.intensity_calibrated = False
        self._state.intensity_correction_curve = None
        self._state.intensity_calibration_time = None
    
    def set_auto_exposure_enabled(self, enabled: bool, target: float = 0.7) -> None:
        """设置自动曝光启用状态"""
        self._state.auto_exposure_enabled = enabled
        self._state.auto_exposure_target = target
