"""
集成测试套件

测试范围:
1. MockDriver - 驱动层测试
2. StateManager - 状态管理器测试
3. BridgeObject - 通信桥接测试
4. WorkerThread - 工作线程测试
5. 边界条件和压力测试
6. QWebChannel 集成测试
7. 日志系统集成测试
8. 推理模块集成测试
"""
import sys
import os
import time
import logging
from pathlib import Path

import pytest
import numpy as np

# 添加项目路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Windows 下 PySide6 需要添加 DLL 目录
if os.name == 'nt':
    try:
        os.add_dll_directory(r'C:\Windows\System32')
    except Exception:
        pass

from backend.driver import MockDriver, DeviceState
from backend.state_manager import StateManager, ConnectionState, AcquisitionState


# ==================== 1. MockDriver 测试 ====================
class TestMockDriver:
    """MockDriver 测试类"""

    def test_mock_driver_basic(self):
        """测试 MockDriver 基本功能"""
        driver = MockDriver(seed=42, noise_level=0.02)
        assert driver.connect() == True
        assert driver.connected == True

        wavelengths = driver.get_wavelengths()
        assert len(wavelengths) == 1024
        assert wavelengths.min() == 200.0
        assert wavelengths.max() == 3200.0

        spectrum = driver.read_spectrum()
        assert spectrum is not None
        assert len(spectrum) == 1024
        assert spectrum.min() >= 0

    def test_mock_driver_states(self):
        """测试 MockDriver 设备状态 (使用 Enum)"""
        driver = MockDriver()
        driver.connect()

        assert driver.device_state == DeviceState.NORMAL
        spectrum = driver.read_spectrum()
        assert spectrum is not None

        driver.device_state = DeviceState.HIGH_NOISE
        assert driver.device_state == DeviceState.HIGH_NOISE
        noisy_spectrum = driver.read_spectrum()
        assert noisy_spectrum is not None

        driver.device_state = DeviceState.ERROR
        error_spectrum = driver.read_spectrum()
        assert error_spectrum is None

        with pytest.raises(TypeError):
            driver.device_state = 'invalid'

    def test_mock_driver_peak_positions(self):
        """测试 MockDriver 特征峰配置"""
        driver = MockDriver()

        peaks = driver.peak_positions
        assert len(peaks) == 5

        new_peaks = [(500, 0.5), (1000, 0.8)]
        driver.set_peak_positions(new_peaks)
        assert driver.peak_positions == new_peaks

        driver.reset_peak_positions()
        assert len(driver.peak_positions) == 5


# ==================== 2. StateManager 测试 ====================
class TestStateManager:
    """StateManager 测试类"""

    def test_state_manager_basic(self):
        """测试 StateManager 基本功能"""
        state_manager = StateManager()

        assert state_manager.state.connection == ConnectionState.DISCONNECTED
        assert state_manager.state.acquisition == AcquisitionState.IDLE
        assert state_manager.is_connected == False
        assert state_manager.is_acquiring == False

        state_manager.connect_device()
        assert state_manager.state.connection == ConnectionState.CONNECTING

        state_manager.set_connected(True)
        assert state_manager.state.connection == ConnectionState.CONNECTED
        assert state_manager.is_connected == True

        result = state_manager.start_acquisition()
        assert result == True
        assert state_manager.is_acquiring == True

        state_manager.stop_acquisition()
        assert state_manager.is_acquiring == False

        state_manager.disconnect_device()
        assert state_manager.state.connection == ConnectionState.DISCONNECTED
        assert state_manager.is_acquiring == False

    def test_state_manager_signals(self):
        """测试 StateManager 信号"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        state_manager = StateManager()
        signals_received = []

        def on_connection_changed(state):
            signals_received.append(('connection', state))

        def on_acquisition_changed(state):
            signals_received.append(('acquisition', state))

        state_manager.connectionChanged.connect(on_connection_changed)
        state_manager.acquisitionChanged.connect(on_acquisition_changed)

        state_manager.connect_device()
        state_manager.set_connected(True)
        state_manager.start_acquisition()
        state_manager.stop_acquisition()
        state_manager.disconnect_device()

        app.processEvents()

        assert len(signals_received) >= 3


# ==================== 3. BridgeObject 测试 ====================
class TestBridgeObject:
    """BridgeObject 通信桥接测试"""

    def test_bridge_object(self):
        """测试 BridgeObject 通信桥接"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        state_manager = StateManager()
        driver = MockDriver()

        from main import BridgeObject
        bridge = BridgeObject(state_manager, driver)

        result = bridge.connect()
        assert result == True
        assert driver.connected == True

        bridge.disconnect()
        assert driver.connected == False

        bridge.connect()

        result = bridge.startAcquisition()
        assert result == True
        assert state_manager.is_acquiring == True

        bridge.stopAcquisition()
        assert state_manager.is_acquiring == False

        bridge.setNoiseLevel(0.05)
        assert state_manager.state.noise_level == 0.05
        assert driver._noise_level == 0.05

        bridge.setDeviceState('high_noise')
        assert state_manager.state.device_state == 'high_noise'
        assert driver.device_state == DeviceState.HIGH_NOISE

        status_str = bridge.getStatus()
        import json
        status = json.loads(status_str)
        assert 'connected' in status
        assert 'acquiring' in status


# ==================== 4. WorkerThread 测试 ====================
class TestWorkerThread:
    """WorkerThread 测试类"""

    def test_worker_thread_basic(self):
        """测试 WorkerThread 基本功能"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        driver = MockDriver()
        driver.connect()

        from main import WorkerThread
        worker = WorkerThread(driver, sample_rate=20.0)

        spectra_received = []

        def on_spectrum(data):
            spectra_received.append(data)

        worker.spectrumReady.connect(on_spectrum)

        worker.start()
        worker.acquiring = True

        for _ in range(10):
            app.processEvents()
            time.sleep(0.05)

        worker.acquiring = False
        worker.stop()

        assert worker.isRunning() == False

    def test_worker_thread_exception_handling(self):
        """测试 WorkerThread 异常处理"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        driver = MockDriver()
        driver.connect()
        driver.device_state = DeviceState.ERROR

        from main import WorkerThread
        worker = WorkerThread(driver, sample_rate=10.0)

        errors_received = []

        def on_error(msg):
            errors_received.append(msg)

        worker.errorOccurred.connect(on_error)
        worker.start()
        worker.acquiring = True

        time.sleep(0.3)

        worker.acquiring = False
        worker.stop()


# ==================== 5. 边界条件测试 ====================
class TestBoundaryConditions:
    """边界条件测试类"""

    def test_noise_level_boundaries(self):
        """测试噪声水平边界"""
        driver = MockDriver(noise_level=0.0)
        driver.connect()
        spectrum = driver.read_spectrum()
        assert spectrum is not None

        driver.set_params(noise_level=1.0)
        spectrum = driver.read_spectrum()
        assert spectrum is not None

    def test_sample_rate_boundaries(self):
        """测试采样率边界"""
        from main import WorkerThread
        driver = MockDriver()

        worker_low = WorkerThread(driver, sample_rate=0.1)
        assert worker_low._sample_rate == 0.1

        worker_high = WorkerThread(driver, sample_rate=100.0)
        assert worker_high._sample_rate == 100.0

        worker_extreme = WorkerThread(driver, sample_rate=1000.0)
        assert worker_extreme._sample_rate == 100.0

    def test_concurrent_state_changes(self):
        """测试并发状态切换"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        state_manager = StateManager()
        driver = MockDriver()
        from main import BridgeObject, WorkerThread

        bridge = BridgeObject(state_manager, driver)
        worker = WorkerThread(driver, sample_rate=50.0)
        worker.start()

        for i in range(10):
            bridge.connect()
            bridge.startAcquisition()
            time.sleep(0.05)
            bridge.stopAcquisition()
            time.sleep(0.02)

        bridge.stopAcquisition()
        bridge.disconnect()
        worker.stop()


# ==================== 6. 集成测试 ====================
class TestIntegration:
    """集成测试类"""

    def test_signal_emission(self):
        """测试信号触发 - 验证前端能收到通知"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        state_manager = StateManager()
        driver = MockDriver()
        from main import BridgeObject

        bridge = BridgeObject(state_manager, driver)

        signals_received = []

        def on_connect_success():
            signals_received.append('connected')

        def on_acquisition_started():
            signals_received.append('acquisitionStarted')

        def on_acquisition_stopped():
            signals_received.append('acquisitionStopped')

        bridge.connected.connect(on_connect_success)
        bridge.acquisitionStarted.connect(on_acquisition_started)
        bridge.acquisitionStopped.connect(on_acquisition_stopped)

        driver.connect()
        bridge.connect()
        app.processEvents()

        bridge.startAcquisition()
        app.processEvents()
        bridge.stopAcquisition()
        app.processEvents()

        assert 'connected' in signals_received
        assert 'acquisitionStarted' in signals_received
        assert 'acquisitionStopped' in signals_received

    def test_logging_integration(self):
        """测试日志系统集成"""
        from backend.logging_config import setup_logging, get_logger

        logger = setup_logging(
            log_level=logging.INFO,
            log_file=None,
            console_output=True,
            debug_mode=False
        )

        log = get_logger('test_integration')
        log.info("测试 INFO 日志")
        log.warning("测试 WARNING 日志")
        log.error("测试 ERROR 日志")

    def test_inference_integration(self):
        """测试推理模块集成"""
        from backend.inference import MockInference, LocalInference, create_inference

        mock_inf = create_inference(use_mock=True, seed=42)
        assert isinstance(mock_inf, MockInference)

        mock_inf.load_model("mock_model.onnx")

        driver = MockDriver()
        driver.connect()
        spectrum = driver.read_spectrum()
        wavenumbers = driver.get_wavelengths()

        result = mock_inf.predict(spectrum, wavenumbers)
        assert result.class_name != "no_model"
        assert len(result.peaks) > 0

        local_inf = create_inference(use_mock=False)
        assert isinstance(local_inf, LocalInference)
        assert local_inf.is_loaded == False

        result = local_inf.predict(spectrum, wavenumbers)
        assert result.class_name == "no_model"
