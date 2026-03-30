"""
拉曼光谱边缘客户端 - 主程序

架构说明:
- StateManager: 统一管理状态，避免状态共享
- BridgeObject: 仅负责前后端通信，不持有状态
- WorkerThread: 仅负责数据采集，通过信号与外部通信
"""
import sys
import os
import json
import time
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime

# 配置日志（必须在其他导入之前）
from backend.logging_config import setup_logging, get_logger, cleanup_old_logs

# P1 修复：启动时清理旧日志
cleanup_old_logs(max_total_size=100*1024*1024)  # 最大 100MB

# P2 修复：使用环境变量控制日志配置
log_level_str = os.getenv('RAMAN_LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

log_file = os.getenv('RAMAN_LOG_FILE', None)
if log_file is None and os.getenv('RAMAN_LOG_ENABLED', 'false').lower() == 'true':
    from backend.logging_config import create_log_filename
    log_file = create_log_filename("raman")

console_output = os.getenv('RAMAN_LOG_CONSOLE', 'true').lower() == 'true'
debug_mode = os.getenv('RAMAN_DEBUG', 'false').lower() == 'true'

# 初始化日志系统
logger = setup_logging(
    log_level=log_level,
    log_file=log_file,
    console_output=console_output,
    debug_mode=debug_mode
)
log = get_logger(__name__)

if debug_mode:
    log.info("[Main] 调试模式已启用")
if log_file:
    log.info(f"[Main] 日志文件：{log_file}")

from PySide6.QtCore import (
    QObject, Signal, Slot, QThread, QTimer, QUrl, Qt,
    QElapsedTimer, QMutex, QMutexLocker, QWaitCondition
)
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QSplashScreen, QLabel, QInputDialog
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入 Qt 资源（打包前端文件到 exe）
import resources

from backend.driver import BaseDriver, MockDriver, DeviceState
from backend.state_manager import StateManager, ConnectionState, AcquisitionState, CalibrationStateManager

from backend.algorithms import (
    WavelengthCalibrator,
    IntensityCalibrator,
    AutoExposure,
    # P0 新增算法
    find_peaks_auto,
    fit_peak_auto,
    calculate_peak_statistics,
    preprocess_spectrum,
    subtract_spectra,
)
from backend.services.live_service import LiveAcquisitionService
from backend.error_handler import ApiResponse, ErrorCode, CalibrationLog, AutoExposureLog

# P12 新增：导入 AI 推理模块
try:
    from backend.ai_inference import AIInference
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI 推理模块导入失败：{e}，将使用 MockInference")
    AI_AVAILABLE = False

import json
import csv
import numpy as np


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件路径，兼容打包后的环境
    """
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return str(base_path / relative_path)


class BridgeObject(QObject):
    """
    前后端通信桥接对象

    职责：仅负责通信，不持有业务逻辑状态
    所有状态由 StateManager 管理
    
    注意：避免使用 connect/disconnect 作为方法名，会与 Signal.connect 冲突
    """

    # ========== 发送给前端的信号 ==========
    connected = Signal()
    connectFailed = Signal()
    acquisitionStarted = Signal()
    acquisitionStopped = Signal()
    spectrumReady = Signal(list)
    dataExported = Signal(str)
    baselineCorrected = Signal(list, list)
    peakAreaCalculated = Signal(dict)
    libraryMatched = Signal(list)

    # P0 新增：实时采集信号
    liveModeStarted = Signal(str)  # session_id
    liveModeStopped = Signal()
    liveModePaused = Signal(bool)

    # P0 修复：错误信号（带错误码和错误信息）
    errorSignal = Signal(int, str)

    def __init__(self, state_manager: StateManager, driver: BaseDriver, parent=None):
        super().__init__(parent)
        self._state_manager = state_manager
        self._driver = driver
        self._export_path = ""
        self._spectrum_data = None
        self._wavelengths = None
        self._inference = None
        self._ai_inference = None  # P12 新增：AI 推理模块
        self._worker_thread = None  # P1 修复：添加私有属性

        # P11 新增：校准状态管理
        self._calibration_manager = CalibrationStateManager()

        # P11 新增：校准器实例
        self._wavelength_calibrator = WavelengthCalibrator()
        self._intensity_calibrator = IntensityCalibrator()
        self._auto_exposure = AutoExposure()

        # P0 新增：实时采集服务
        self._live_service: Optional[LiveAcquisitionService] = None

        self._state_manager.connectionChanged.connect(self._on_connection_changed)
        self._state_manager.acquisitionChanged.connect(self._on_acquisition_changed)

        try:
            self._wavelengths = self._driver.get_wavelengths().tolist()
        except Exception as e:
            log.warning(f"[Bridge] 获取波长数据失败：{e}")

        try:
            from backend.inference import MockInference
            self._inference = MockInference()
            self._inference.load_model("mock_model.onnx")
        except Exception as e:
            log.warning(f"[Bridge] 初始化推理模块失败：{e}")

        # P12 新增：初始化 AI 推理模块
        if AI_AVAILABLE:
            try:
                self._ai_inference = AIInference()
                # 尝试加载模型（如果存在）
                model_path = Path(__file__).parent / "backend" / "models" / "transformer_minerals.npz"
                if model_path.exists():
                    self._ai_inference.load_model(str(model_path))
                    log.info(f"[Bridge] AI 推理模块已加载：{model_path}")
                else:
                    log.info(f"[Bridge] AI 模型文件不存在，使用随机初始化：{model_path}")
            except Exception as e:
                log.warning(f"[Bridge] 初始化 AI 推理模块失败：{e}")
                self._ai_inference = None

    # P1 修复：添加公有方法设置 worker_thread
    def set_worker_thread(self, worker_thread):
        """
        设置工作线程引用

        Args:
            worker_thread: WorkerThread 实例
        """
        self._worker_thread = worker_thread
        log.info("[Bridge] WorkerThread 引用已设置")

    # ========== 前端调用的方法 ==========

    @Slot(result=bool)
    def connectDevice(self) -> bool:
        """连接设备"""
        log.info("[Bridge] 尝试连接设备...")
        self._state_manager.connect_device()
        success = self._driver.connect()
        self._state_manager.set_connected(success)
        if success:
            log.info("[Bridge] 设备连接成功")
        else:
            log.warning("[Bridge] 设备连接失败")
        return success

    @Slot()
    def disconnectDevice(self):
        """断开连接"""
        log.info("[Bridge] 断开设备连接")
        self._driver.disconnect()
        self._state_manager.disconnect_device()

    @Slot(result=bool)
    def startAcquisition(self) -> bool:
        """开始采集"""
        log.info("[Bridge] 开始采集")
        return self._state_manager.start_acquisition()

    @Slot()
    def stopAcquisition(self):
        """停止采集"""
        log.info("[Bridge] 停止采集")
        self._state_manager.stop_acquisition()

    @Slot(float)
    def setNoiseLevel(self, level: float):
        """设置噪声水平"""
        log.info(f"[Bridge] 设置噪声水平：{level}")
        self._state_manager.set_noise_level(level)
        if isinstance(self._driver, MockDriver):
            self._driver.set_params(noise_level=level)

    @Slot(str)
    def setDeviceState(self, state: str):
        """设置设备状态"""
        log.info(f"[Bridge] 设置设备状态：{state}")
        self._state_manager.set_device_state(state)
        if isinstance(self._driver, MockDriver):
            try:
                self._driver.device_state = DeviceState(state)
            except ValueError as e:
                log.error(f"[Bridge] 无效的设备状态：{e}")

    @Slot(int, result=int)
    def setIntegrationTime(self, time_ms: int) -> int:
        """设置积分时间"""
        if time_ms < 10:
            time_ms = 10
            log.warning("[Bridge] 积分时间过小，已设置为 10ms")
        elif time_ms > 10000:
            time_ms = 10000
            log.warning("[Bridge] 积分时间过大，已设置为 10000ms")
        log.info(f"[Bridge] 积分时间设置为：{time_ms}ms")
        if isinstance(self._driver, MockDriver):
            self._driver.set_params(integration_time=time_ms)
        self._state_manager.set_integration_time(time_ms)
        if hasattr(self, '_worker_thread') and self._worker_thread is not None:
            self._worker_thread.integration_time = time_ms
        return time_ms

    @Slot(int, result=int)
    def setAccumulationCount(self, count: int) -> int:
        """设置累加平均次数"""
        if count < 1:
            count = 1
            log.warning("[Bridge] 累加次数过小，已设置为 1")
        elif count > 100:
            count = 100
            log.warning("[Bridge] 累加次数过大，已设置为 100")
        log.info(f"[Bridge] 累加平均次数设置为：{count}")
        if isinstance(self._driver, MockDriver):
            self._driver.set_params(accumulation_count=count)
        self._state_manager.set_accumulation_count(count)
        if hasattr(self, '_worker_thread') and self._worker_thread is not None:
            self._worker_thread.accumulation_count = count
        return count

    @Slot(int, result=int)
    def setSmoothingWindow(self, window: int) -> int:
        """设置平滑滤波窗口大小"""
        if window < 0:
            window = 0
            log.warning("[Bridge] 平滑窗口过小，已设置为 0")
        elif window > 51:
            window = 51
            log.warning("[Bridge] 平滑窗口过大，已设置为 51")
        if window > 1 and window % 2 == 0:
            window += 1
            log.info(f"[Bridge] 平滑窗口调整为奇数：{window}")
        log.info(f"[Bridge] 平滑窗口设置为：{window}")
        if isinstance(self._driver, MockDriver):
            self._driver.set_params(smoothing_window=window)
        self._state_manager.set_smoothing_window(window)
        if hasattr(self, '_worker_thread') and self._worker_thread is not None:
            self._worker_thread.smoothing_window = window
        return window

    @Slot(float)
    def calculatePeakArea(self, peak_center: float):
        """计算峰面积"""
        log.info(f"[Bridge] 计算峰面积，中心位置：{peak_center} cm⁻¹")
        if self._spectrum_data is None or self._wavelengths is None:
            log.warning("[Bridge] 没有光谱数据可供计算")
            self.errorSignal.emit(ErrorCode.SPECTRUM_READ_FAILED, "没有可用的光谱数据")
            self.peakAreaCalculated.emit({})
            return
        if self._inference is None:
            log.error("[Bridge] 推理模块未初始化")
            self.errorSignal.emit(ErrorCode.DEVICE_INIT_FAILED, "推理模块未初始化")
            self.peakAreaCalculated.emit({})
            return
        try:
            spectrum = np.array(self._spectrum_data)
            wavenumbers = np.array(self._wavelengths)
            result = self._inference.calculate_peak_area(spectrum, wavenumbers, peak_center)
            self.peakAreaCalculated.emit(result)
            log.info(f"[Bridge] 峰面积计算完成：{result}")
        except ValueError as e:
            error_msg = f"峰面积计算失败：参数无效 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.INVALID_PARAMETER, str(e))
            self.peakAreaCalculated.emit({})
        except Exception as e:
            error_msg = f"峰面积计算失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.PEAK_AREA_CALCULATION_FAILED, error_msg)
            self.peakAreaCalculated.emit({})

    @Slot(int)
    def matchLibrary(self, top_k: int = 5):
        """谱库匹配"""
        log.info(f"[Bridge] 谱库匹配，返回 Top {top_k} 结果")
        if self._spectrum_data is None or self._wavelengths is None:
            log.warning("[Bridge] 没有光谱数据可供匹配")
            self.errorSignal.emit(ErrorCode.SPECTRUM_READ_FAILED, "没有可用的光谱数据")
            self.libraryMatched.emit([])
            return
        if self._inference is None:
            log.error("[Bridge] 推理模块未初始化")
            self.errorSignal.emit(ErrorCode.DEVICE_INIT_FAILED, "推理模块未初始化")
            self.libraryMatched.emit([])
            return
        try:
            spectrum = np.array(self._spectrum_data)
            wavenumbers = np.array(self._wavelengths)
            results = self._inference.match_library(spectrum, wavenumbers, top_k=top_k)
            self.libraryMatched.emit(results)
            log.info(f"[Bridge] 谱库匹配完成：{results[:2]}")
        except Exception as e:
            error_msg = f"谱库匹配失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.LIBRARY_MATCH_FAILED, error_msg)
            self.libraryMatched.emit([])

    # ========== P12 新增：AI 推理方法 ==========

    @Slot(result=str)
    def aiPredict(self) -> str:
        """
        AI 预测（基础版）

        Returns:
            JSON 格式的预测结果
        """
        log.info("[Bridge] AI 预测")
        if self._ai_inference is None:
            result = {'success': False, 'error': 'AI 模块未初始化'}
            return json.dumps(result, ensure_ascii=False)
        
        if self._spectrum_data is None:
            result = {'success': False, 'error': '没有光谱数据'}
            return json.dumps(result, ensure_ascii=False)
        
        try:
            spectrum = np.array(self._spectrum_data)
            result = self._ai_inference.predict(spectrum)
            log.info(f"[Bridge] AI 预测完成：{result.get('class_name', 'unknown')}")
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bridge] AI 预测失败：{e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def aiPredictWithUncertainty(self) -> str:
        """
        AI 预测（带不确定性量化）

        Returns:
            JSON 格式的预测结果（包含不确定性信息）
        """
        log.info("[Bridge] AI 预测（带不确定性）")
        if self._ai_inference is None:
            result = {'success': False, 'error': 'AI 模块未初始化'}
            return json.dumps(result, ensure_ascii=False)
        
        if self._spectrum_data is None:
            result = {'success': False, 'error': '没有光谱数据'}
            return json.dumps(result, ensure_ascii=False)
        
        try:
            spectrum = np.array(self._spectrum_data)
            result = self._ai_inference.predict_with_uncertainty(spectrum)
            log.info(
                f"[Bridge] AI 预测完成：{result.get('class_name', 'unknown')}, "
                f"置信度：{result.get('confidence', 0):.3f}±{result.get('uncertainty', 0):.3f}"
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bridge] AI 预测失败：{e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)

    @Slot(str, int, result=str)
    def aiExplain(self, method: str = "attention", top_k: int = 5) -> str:
        """
        AI 可解释性分析

        Args:
            method: 解释方法 ('attention', 'gradient', 'occlusion', 'shap')
            top_k: 返回前 k 个重要特征

        Returns:
            JSON 格式的解释结果
        """
        log.info(f"[Bridge] AI 可解释性分析，方法：{method}")
        if self._ai_inference is None:
            result = {'success': False, 'error': 'AI 模块未初始化'}
            return json.dumps(result, ensure_ascii=False)
        
        if self._spectrum_data is None:
            result = {'success': False, 'error': '没有光谱数据'}
            return json.dumps(result, ensure_ascii=False)
        
        try:
            spectrum = np.array(self._spectrum_data)
            result = self._ai_inference.explain(spectrum, method=method, top_k=top_k)
            log.info(f"[Bridge] AI 解释完成：{result.get('class_name', 'unknown')}")
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bridge] AI 解释失败：{e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def aiFullAnalysis(self) -> str:
        """
        AI 完整分析（预测 + 不确定性 + 可解释性）

        Returns:
            JSON 格式的完整分析结果
        """
        log.info("[Bridge] AI 完整分析")
        if self._ai_inference is None:
            result = {'success': False, 'error': 'AI 模块未初始化'}
            return json.dumps(result, ensure_ascii=False)
        
        if self._spectrum_data is None:
            result = {'success': False, 'error': '没有光谱数据'}
            return json.dumps(result, ensure_ascii=False)
        
        try:
            spectrum = np.array(self._spectrum_data)
            result = self._ai_inference.full_analysis(spectrum)
            log.info(
                f"[Bridge] AI 完整分析完成：{result.get('class_name', 'unknown')}, "
                f"耗时：{result.get('analysis_time_ms', 0):.1f}ms"
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bridge] AI 分析失败：{e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)

    @Slot(result=str)
    def aiGetModelInfo(self) -> str:
        """
        获取 AI 模型信息

        Returns:
            JSON 格式的模型信息
        """
        if self._ai_inference is None:
            return json.dumps({'loaded': False}, ensure_ascii=False)
        
        info = self._ai_inference.get_model_info()
        return json.dumps(info, ensure_ascii=False)

    @Slot(str, result=str)
    def aiDetectOutlier(self, threshold: str = "0.5") -> str:
        """
        检测异常样本（未知物质）

        Args:
            threshold: 不确定性阈值

        Returns:
            JSON 格式的检测结果
        """
        log.info(f"[Bridge] AI 异常检测，阈值：{threshold}")
        if self._ai_inference is None:
            result = {'success': False, 'error': 'AI 模块未初始化'}
            return json.dumps(result, ensure_ascii=False)
        
        if self._spectrum_data is None:
            result = {'success': False, 'error': '没有光谱数据'}
            return json.dumps(result, ensure_ascii=False)
        
        try:
            spectrum = np.array(self._spectrum_data)
            result = self._ai_inference.detect_outlier(spectrum, threshold=float(threshold))
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"[Bridge] AI 异常检测失败：{e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)

    @Slot()
    def loadData(self):
        """导入历史数据文件"""
        log.info("[Bridge] 导入历史数据")
        file_path, _ = QFileDialog.getOpenFileName(
            None, "导入光谱数据", "",
            "光谱数据文件 (*.json *.csv);;JSON 文件 (*.json);;CSV 文件 (*.csv)"
        )
        if not file_path:
            log.info("[Bridge] 用户取消导入")
            return
        try:
            if file_path.endswith('.json'):
                self._load_from_json(file_path)
            elif file_path.endswith('.csv'):
                self._load_from_csv(file_path)
            else:
                log.error(f"[Bridge] 不支持的文件格式：{file_path}")
                self.errorSignal.emit(ErrorCode.INVALID_FILE_FORMAT, f"不支持的格式：{file_path}")
                return
            log.info(f"[Bridge] 数据导入成功：{file_path}")
        except FileNotFoundError as e:
            error_msg = f"导入失败：文件不存在 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.FILE_NOT_FOUND, error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"导入失败：JSON 格式错误 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.INVALID_FILE_FORMAT, error_msg)
        except ValueError as e:
            error_msg = f"导入失败：数据格式无效 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.INVALID_FILE_FORMAT, error_msg)
        except Exception as e:
            error_msg = f"导入失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.DATA_IMPORT_FAILED, error_msg)

    def _load_from_json(self, file_path: str):
        """从 JSON 文件加载光谱数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'spectrum' in data:
            self._spectrum_data = np.array(data['spectrum'])
        elif 'data' in data:
            self._spectrum_data = np.array(data['data'])
        else:
            raise ValueError("JSON 文件中未找到光谱数据")
        if 'wavelengths' in data:
            self._wavelengths = np.array(data['wavelengths'])
        elif 'wavenumbers' in data:
            self._wavelengths = np.array(data['wavenumbers'])
        else:
            self._wavelengths = self._driver.get_wavelengths()
        self.spectrumReady.emit(self._spectrum_data.tolist())

    def _load_from_csv(self, file_path: str):
        """从 CSV 文件加载光谱数据"""
        data = np.loadtxt(file_path, delimiter=',')
        if data.ndim == 1:
            self._spectrum_data = data
            self._wavelengths = self._driver.get_wavelengths()
        elif data.ndim == 2:
            if data.shape[0] == 2:
                data = data.T
            self._wavelengths = data[:, 0]
            self._spectrum_data = data[:, 1]
        else:
            raise ValueError("CSV 文件格式不正确")
        self.spectrumReady.emit(self._spectrum_data.tolist())

    @Slot(str)
    def exportData(self, format: str = "json"):
        """导出数据"""
        log.info(f"[Bridge] 导出数据，格式：{format}")
        if self._spectrum_data is None:
            log.warning("[Bridge] 没有可导出的光谱数据")
            self.errorSignal.emit(ErrorCode.SPECTRUM_READ_FAILED, "没有可用的光谱数据")
            self.dataExported.emit("")
            return
        if format.lower() == "json":
            default_name = "raman_spectrum.json"
        else:
            default_name = "raman_spectrum.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            None, "导出光谱数据", default_name,
            f"{'JSON' if format.lower() == 'json' else 'CSV'} 文件 (*.{format.lower()})"
        )
        if not file_path:
            log.info("[Bridge] 用户取消导出")
            self.dataExported.emit("")
            return
        try:
            if format.lower() == "json":
                self._export_to_json(file_path)
            elif format.lower() == "csv":
                self._export_to_csv(file_path)
            else:
                log.error(f"[Bridge] 不支持的导出格式：{format}")
                self.errorSignal.emit(ErrorCode.INVALID_FILE_FORMAT, f"不支持的格式：{format}")
                self.dataExported.emit("")
                return
            log.info(f"[Bridge] 数据导出成功：{file_path}")
            self.dataExported.emit(file_path)
        except PermissionError as e:
            error_msg = f"导出失败：文件权限不足 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.DATA_EXPORT_FAILED, error_msg)
            self.dataExported.emit("")
        except OSError as e:
            error_msg = f"导出失败：磁盘错误 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.DATA_EXPORT_FAILED, error_msg)
            self.dataExported.emit("")
        except Exception as e:
            error_msg = f"导出失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.DATA_EXPORT_FAILED, error_msg)
            self.dataExported.emit("")

    @Slot()
    def exportBatchData(self):
        """P2 修复：批量导出所有历史数据"""
        log.info("[Bridge] 批量导出数据")
        if self._spectrum_data is None:
            log.warning("[Bridge] 没有可导出的光谱数据")
            self.errorSignal.emit(ErrorCode.SPECTRUM_READ_FAILED, "没有可用的光谱数据")
            return

        # 选择导出目录
        output_dir = QFileDialog.getExistingDirectory(
            None, "选择批量导出目录", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveAliasNames
        )
        if not output_dir:
            log.info("[Bridge] 用户取消批量导出")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 导出 JSON 格式
            json_path = os.path.join(output_dir, f"raman_spectrum_{timestamp}.json")
            self._export_to_json(json_path)
            log.info(f"[Bridge] 批量导出 JSON 完成：{json_path}")

            # 导出 CSV 格式
            csv_path = os.path.join(output_dir, f"raman_spectrum_{timestamp}.csv")
            self._export_to_csv(csv_path)
            log.info(f"[Bridge] 批量导出 CSV 完成：{csv_path}")

            # 导出带免责声明的文本文件
            txt_path = os.path.join(output_dir, f"disclaimer_{timestamp}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("⚠️ 免责声明\n")
                f.write("=" * 60 + "\n\n")
                f.write("本数据由拉曼光谱边缘客户端（模拟驱动）生成。\n\n")
                f.write("重要提示：\n")
                f.write("1. 本软件为教学演示软件，谱库数据为高斯峰模拟数据\n")
                f.write("2. 峰值检测算法为简化实现，可能存在误差\n")
                f.write("3. 设备驱动为模拟驱动，不支持真实仪器\n\n")
                f.write("⚠️ 本软件仅用于教学演示和算法验证，不可用于实际物质分析或科研用途。\n\n")
                f.write("=" * 60 + "\n")
                f.write(f"导出时间：{timestamp}\n")
            log.info(f"[Bridge] 批量导出免责声明完成：{txt_path}")

            self.dataExported.emit(output_dir)
            log.info(f"[Bridge] 批量导出完成：{output_dir}")

        except Exception as e:
            error_msg = f"批量导出失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.DATA_EXPORT_FAILED, error_msg)

    @Slot()
    def applyBaselineCorrection(self):
        """应用基线校正"""
        log.info("[Bridge] 应用基线校正")
        if self._spectrum_data is None:
            log.warning("[Bridge] 没有可校正的光谱数据")
            self.errorSignal.emit(ErrorCode.SPECTRUM_READ_FAILED, "没有可用的光谱数据")
            self.baselineCorrected.emit([], [])
            return
        if self._inference is None:
            log.error("[Bridge] 推理模块未初始化")
            self.errorSignal.emit(ErrorCode.DEVICE_INIT_FAILED, "推理模块未初始化")
            self.baselineCorrected.emit([], [])
            return
        try:
            spectrum = np.array(self._spectrum_data)
            corrected, baseline = self._inference.baseline_correction(spectrum)
            self.baselineCorrected.emit(corrected.tolist(), baseline.tolist())
            log.info("[Bridge] 基线校正完成")
        except ValueError as e:
            error_msg = f"基线校正失败：数据无效 - {e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.INVALID_PARAMETER, str(e))
            self.baselineCorrected.emit([], [])
        except Exception as e:
            error_msg = f"基线校正失败：{e}"
            log.error(f"[Bridge] {error_msg}")
            self.errorSignal.emit(ErrorCode.BASELINE_CORRECTION_FAILED, error_msg)
            self.baselineCorrected.emit([], [])

    def _export_to_json(self, file_path: str):
        """导出为 JSON 格式（P0 修复：添加免责声明）"""
        data = {
            "disclaimer": "⚠️ 重要提示：本数据由模拟驱动生成，仅用于教学演示，不可用于实际物质分析。",
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "device_state": self._state_manager.state.device_state,
                "noise_level": self._state_manager.state.noise_level,
                "wavelength_range": [
                    float(min(self._wavelengths)) if self._wavelengths else 0,
                    float(max(self._wavelengths)) if self._wavelengths else 0
                ],
                "num_points": len(self._wavelengths) if self._wavelengths else 0
            },
            "wavelengths": self._wavelengths,
            "spectrum": self._spectrum_data.tolist() if hasattr(self._spectrum_data, 'tolist') else self._spectrum_data
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_to_csv(self, file_path: str):
        """导出为 CSV 格式（P0 修复：添加免责声明水印）"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 添加免责声明水印行
            writer.writerow(["# ⚠️ 免责声明：本数据由模拟驱动生成，仅用于教学演示，不可用于实际物质分析。"])
            writer.writerow(["# Disclaimer: This data is generated by mock driver, for teaching/demo purposes only."])
            writer.writerow([])
            writer.writerow(["Wavenumber (cm^-1)", "Intensity (a.u.)"])
            if self._wavelengths and self._spectrum_data is not None:
                spectrum_list = self._spectrum_data.tolist() if hasattr(self._spectrum_data, 'tolist') else self._spectrum_data
                for i, wavelength in enumerate(self._wavelengths):
                    if i < len(spectrum_list):
                        writer.writerow([wavelength, spectrum_list[i]])

    @Slot(result=str)
    def getStatus(self) -> str:
        """获取当前状态"""
        status = {
            "connected": self._state_manager.is_connected,
            "acquiring": self._state_manager.is_acquiring,
            "device_state": self._state_manager.state.device_state,
            "noise_level": self._state_manager.state.noise_level
        }
        return json.dumps(status, ensure_ascii=False)

    def get_spectrum_data(self) -> Optional[np.ndarray]:
        """获取存储的光谱数据"""
        return self._spectrum_data

    def get_wavelengths(self) -> Optional[List[float]]:
        """获取波长数据"""
        return self._wavelengths

    # ========== 信号转发 ==========

    @Slot(ConnectionState)
    def _on_connection_changed(self, state: ConnectionState):
        """连接状态变化时通知前端"""
        if state == ConnectionState.CONNECTED:
            self.connected.emit()
        elif state == ConnectionState.ERROR:
            self.connectFailed.emit()

    @Slot(AcquisitionState)
    def _on_acquisition_changed(self, state: AcquisitionState):
        """采集状态变化时通知前端"""
        if state == AcquisitionState.RUNNING:
            self.acquisitionStarted.emit()
        elif state == AcquisitionState.IDLE:
            self.acquisitionStopped.emit()

    # ========== P11 新增：P0 功能接口 ==========

    @Slot(str, result=str)
    def calibrateWavelength(self, reference_peaks_json: str) -> str:
        """
        波长校准
        
        Args:
            reference_peaks_json: JSON 格式的参考峰位置列表，如 "[520.5, 1332.2]"
        
        Returns:
            JSON 格式的 ApiResponse
        """
        log.info("[Bridge] 波长校准")
        try:
            reference_peaks = json.loads(reference_peaks_json)
            
            if not isinstance(reference_peaks, list) or len(reference_peaks) == 0:
                result = ApiResponse.error(
                    ErrorCode.CALIBRATION_DATA_INVALID,
                    "参考峰位置必须是非空列表"
                )
                return json.dumps(result.to_dict(), ensure_ascii=False)
            
            # 执行波长校准
            result = self._wavelength_calibrator.calibrate(reference_peaks)
            
            # 更新校准状态
            if result.success:
                self._calibration_manager.set_wavelength_calibrated(
                    result.data["correction"],
                    result.data["calibrated_at"]
                )
                log.info(CalibrationLog.wavelength_calibration_success(result.data["correction"]))
            else:
                log.error(CalibrationLog.wavelength_calibration_failed(result.message, result.error_code))
            
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except json.JSONDecodeError as e:
            result = ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"JSON 格式错误：{e}"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
        except Exception as e:
            result = ApiResponse.error(
                ErrorCode.CALIBRATION_FAILED,
                f"波长校准异常：{e}"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)

    @Slot(result=str)
    def getWavelengthCorrection(self) -> str:
        """获取波长校正值"""
        status = self._wavelength_calibrator.get_status()
        return json.dumps(status.to_dict(), ensure_ascii=False)

    @Slot(result=str)
    def isWavelengthCalibrated(self) -> str:
        """检查是否已进行波长校准"""
        status = ApiResponse.ok(
            data={"calibrated": self._calibration_manager.is_wavelength_calibrated}
        )
        return json.dumps(status.to_dict(), ensure_ascii=False)

    @Slot(str, str, result=str)
    def calibrateIntensity(self, reference_spectrum_json: str, theoretical_spectrum_json: str) -> str:
        """
        强度校准
        
        Args:
            reference_spectrum_json: JSON 格式的参考光谱（实测）
            theoretical_spectrum_json: JSON 格式的理论光谱（标准值）
        
        Returns:
            JSON 格式的 ApiResponse
        """
        log.info("[Bridge] 强度校准")
        try:
            reference_spectrum = np.array(json.loads(reference_spectrum_json))
            theoretical_spectrum = np.array(json.loads(theoretical_spectrum_json))
            
            if self._wavelengths is None:
                result = ApiResponse.error(
                    ErrorCode.CALIBRATION_DATA_INVALID,
                    "波长数据未就绪"
                )
                return json.dumps(result.to_dict(), ensure_ascii=False)
            
            wavenumbers = np.array(self._wavelengths)
            
            # 执行强度校准
            result = self._intensity_calibrator.calibrate(
                reference_spectrum, theoretical_spectrum, wavenumbers
            )
            
            # 更新校准状态
            if result.success:
                self._calibration_manager.set_intensity_calibrated(
                    result.data["correction_curve"],
                    result.data["calibrated_at"]
                )
                log.info(CalibrationLog.intensity_calibration_success(
                    tuple(result.data["wavelength_range"])
                ))
            else:
                log.error(CalibrationLog.intensity_calibration_failed(result.message, result.error_code))
            
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except Exception as e:
            result = ApiResponse.error(
                ErrorCode.INTENSITY_CALIBRATION_ERROR,
                f"强度校准异常：{e}"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)

    @Slot(result=str)
    def getIntensityCorrection(self) -> str:
        """获取强度校正曲线"""
        status = self._intensity_calibrator.get_status()
        return json.dumps(status.to_dict(), ensure_ascii=False)

    @Slot(float, int, result=str)
    def autoExposure(self, target_intensity: float = 0.7, max_iterations: int = 3) -> str:
        """
        自动曝光
        
        Args:
            target_intensity: 目标强度（0.5-0.8）
            max_iterations: 最大迭代次数
        
        Returns:
            JSON 格式的 ApiResponse
        """
        log.info(f"[Bridge] 自动曝光，目标强度={target_intensity:.2f}")
        
        # 参数验证
        if not 0.5 <= target_intensity <= 0.8:
            result = ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"目标强度必须在 0.5-0.8 范围内"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
        
        # 设置目标强度
        self._auto_exposure.set_target_intensity(target_intensity)
        
        # 检查是否有光谱数据
        if self._spectrum_data is None:
            result = ApiResponse.error(
                ErrorCode.SPECTRUM_EMPTY,
                "请先采集光谱数据"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
        
        current_time = self._state_manager._params.get('integration_time', 100)
        
        # 定义采集函数（用于自动曝光算法）
        def acquire_spectrum(integration_time: int) -> np.ndarray:
            # 这里需要调用实际的采集函数
            # 暂时返回当前光谱数据
            return self._spectrum_data
        
        # 执行自动曝光
        result = self._auto_exposure.execute(
            acquire_spectrum,
            current_time,
            max_iterations
        )
        
        if result.success:
            log.info(AutoExposureLog.auto_exposure_success(
                result.data["final_integration_time"],
                result.data["iterations"]
            ))
        else:
            log.error(AutoExposureLog.auto_exposure_failed(result.message, result.error_code))
        
        return json.dumps(result.to_dict(), ensure_ascii=False)

    @Slot(bool)
    def setAutoExposureEnabled(self, enabled: bool):
        """设置自动曝光启用状态"""
        self._auto_exposure.set_enabled(enabled)
        self._calibration_manager.set_auto_exposure_enabled(enabled)
        log.info(f"[Bridge] 自动曝光已{'启用' if enabled else '禁用'}")

    @Slot(result=str)
    def isAutoExposureEnabled(self) -> str:
        """检查自动曝光是否启用"""
        status = ApiResponse.ok(
            data={"enabled": self._calibration_manager.is_auto_exposure_enabled}
        )
        return json.dumps(status.to_dict(), ensure_ascii=False)

    @Slot(result=str)
    def getCalibrationStatus(self) -> str:
        """获取校准状态"""
        status = ApiResponse.ok(
            data={
                "wavelength": {
                    "calibrated": self._calibration_manager.is_wavelength_calibrated,
                    "correction": self._calibration_manager.wavelength_correction
                },
                "intensity": {
                    "calibrated": self._calibration_manager.is_intensity_calibrated
                },
                "auto_exposure": {
                    "enabled": self._calibration_manager.is_auto_exposure_enabled
                }
            }
        )
        return json.dumps(status.to_dict(), ensure_ascii=False)

    # ==================== P0-1 实时采集 API ====================

    @Slot(str, result=str)
    def startLiveMode(self, refresh_rate_json: str) -> str:
        """
        启动实时采集模式
        
        使用 LiveAcquisitionService 实现真正的实时采集
        
        Args:
            refresh_rate_json: JSON 格式的刷新率，如 '{"value": 5.0}'
            
        Returns:
            JSON 格式的结果
        """
        try:
            refresh_rate_data = json.loads(refresh_rate_json)
            refresh_rate = float(refresh_rate_data.get("value", 5.0))
            
            # 验证刷新率
            if not 0.1 <= refresh_rate <= 10.0:
                return ApiResponse.error(
                    ErrorCode.INVALID_PARAMETER,
                    "刷新率必须在 0.1-10.0 Hz 之间"
                ).to_dict()
            
            # 初始化实时采集服务（如果尚未初始化）
            if self._live_service is None:
                self._live_service = LiveAcquisitionService(self._driver)
                # 注册回调，将数据发送到前端
                self._live_service.add_callback(self._on_live_spectrum)
            
            # 启动采集
            result = self._live_service.start(refresh_rate)
            
            if result.get("success"):
                session_id = result.get("session_id", "")
                self.liveModeStarted.emit(session_id)
                log.info(f"[Bridge] 实时采集启动成功，刷新率：{refresh_rate} Hz, session_id: {session_id}")
                return ApiResponse.ok(
                    data={"refresh_rate": refresh_rate, "session_id": session_id, "started": True},
                    message="实时采集已启动"
                ).to_dict()
            else:
                log.error(f"[Bridge] 实时采集启动失败：{result.get('error')}")
                return ApiResponse.error(
                    ErrorCode.ACQUISITION_FAILED,
                    result.get("error", "未知错误")
                ).to_dict()
            
        except json.JSONDecodeError as e:
            log.error(f"[Bridge] 解析刷新率参数失败：{e}")
            return ApiResponse.error(ErrorCode.INVALID_PARAMETER, f"参数解析失败：{str(e)}").to_dict()
        except Exception as e:
            log.error(f"[Bridge] 启动实时采集失败：{e}", exc_info=True)
            return ApiResponse.error(ErrorCode.ACQUISITION_FAILED, str(e)).to_dict()

    def _on_live_spectrum(self, spectrum: np.ndarray, frame_count: int):
        """
        实时采集回调 - 当新的光谱数据到达时触发
        
        Args:
            spectrum: 光谱数据数组
            frame_count: 帧计数
        """
        try:
            data = {
                "spectrum": spectrum.tolist(),
                "frame_count": frame_count,
                "timestamp": time.time()
            }
            # 通过信号发送到前端
            self.spectrumReady.emit(spectrum.tolist())
        except Exception as e:
            log.error(f"[Bridge] 实时光谱回调失败：{e}")

    @Slot(str, result=str)
    def pauseLiveMode(self, paused_json: str) -> str:
        """
        暂停/继续实时采集
        
        Args:
            paused_json: JSON 格式的暂停状态，如 '{"paused": true}'
            
        Returns:
            JSON 格式的结果
        """
        try:
            paused_data = json.loads(paused_json)
            paused = bool(paused_data.get("paused", False))
            
            if self._live_service is None:
                return ApiResponse.error(
                    ErrorCode.ACQUISITION_ERROR,
                    "实时采集服务未初始化"
                ).to_dict()
            
            result = self._live_service.pause(paused)
            
            if result.get("success"):
                self.liveModePaused.emit(paused)
                log.info(f"[Bridge] 实时采集{'已暂停' if paused else '已继续'}")
                return ApiResponse.ok(
                    data={"paused": paused},
                    message=f"实时采集已{'暂停' if paused else '继续'}"
                ).to_dict()
            else:
                return ApiResponse.error(
                    ErrorCode.ACQUISITION_ERROR,
                    result.get("error", "未知错误")
                ).to_dict()
            
        except Exception as e:
            log.error(f"[Bridge] 暂停/继续实时采集失败：{e}")
            return ApiResponse.error(ErrorCode.ACQUISITION_ERROR, str(e)).to_dict()

    @Slot(result=str)
    def stopLiveMode(self) -> str:
        """
        停止实时采集
        
        Returns:
            JSON 格式的结果
        """
        try:
            if self._live_service is None:
                return ApiResponse.ok(
                    data={"stopped": True},
                    message="实时采集服务未运行"
                ).to_dict()
            
            result = self._live_service.stop()
            
            if result.get("success"):
                self.liveModeStopped.emit()
                log.info("[Bridge] 实时采集已停止")
                return ApiResponse.ok(
                    data={"stopped": True},
                    message="实时采集已停止"
                ).to_dict()
            else:
                return ApiResponse.error(
                    ErrorCode.ACQUISITION_ERROR,
                    result.get("error", "未知错误")
                ).to_dict()
            
        except Exception as e:
            log.error(f"[Bridge] 停止实时采集失败：{e}")
            return ApiResponse.error(ErrorCode.ACQUISITION_ERROR, str(e)).to_dict()

    @Slot(str, result=str)
    def setRefreshRate(self, refresh_rate_json: str) -> str:
        """
        设置实时采集刷新率
        
        Args:
            refresh_rate_json: JSON 格式的刷新率
            
        Returns:
            JSON 格式的结果
        """
        try:
            refresh_rate_data = json.loads(refresh_rate_json)
            refresh_rate = float(refresh_rate_data.get("value", 5.0))
            
            if self._live_service is None:
                return ApiResponse.error(
                    ErrorCode.ACQUISITION_ERROR,
                    "实时采集服务未初始化"
                ).to_dict()
            
            result = self._live_service.set_refresh_rate(refresh_rate)
            
            if result.get("success"):
                log.info(f"[Bridge] 刷新率设置为：{refresh_rate} Hz")
                return ApiResponse.ok(
                    data={"refresh_rate": refresh_rate},
                    message=f"刷新率已设置为 {refresh_rate} Hz"
                ).to_dict()
            else:
                return ApiResponse.error(
                    ErrorCode.INVALID_PARAMETER,
                    result.get("error", "未知错误")
                ).to_dict()
            
        except Exception as e:
            log.error(f"[Bridge] 设置刷新率失败：{e}")
            return ApiResponse.error(ErrorCode.ACQUISITION_ERROR, str(e)).to_dict()

    # ==================== P0-2 峰值识别 API ====================

    @Slot(str, str, result=str)
    def findPeaks(self, spectrum_json: str, params_json: str) -> str:
        """
        自动寻峰
        
        Args:
            spectrum_json: JSON 格式的光谱数据数组
            params_json: JSON 格式的寻峰参数
            
        Returns:
            JSON 格式的结果
        """
        try:
            spectrum = np.array(json.loads(spectrum_json))
            params = json.loads(params_json)
            
            peaks = find_peaks_auto(
                spectrum,
                sensitivity=params.get("sensitivity", 0.5),
                min_snr=params.get("minSnr", 3.0),
                min_distance=params.get("minDistance", 5)
            )
            
            peak_stats = calculate_peak_statistics(spectrum, peaks)
            
            result = ApiResponse.ok(
                data={
                    "peaks": peaks.tolist() if hasattr(peaks, 'tolist') else peaks,
                    "count": len(peaks),
                    "statistics": peak_stats
                },
                message=f"检测到 {len(peaks)} 个峰"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except Exception as e:
            log.error(f"[Bridge] 寻峰失败：{e}")
            result = ApiResponse.error(ErrorCode.PEAK_DETECTION_FAILED, str(e))
            return json.dumps(result.to_dict(), ensure_ascii=False)

    @Slot(str, str, str, result=str)
    def fitPeak(self, spectrum_json: str, position_json: str, fit_type_json: str) -> str:
        """
        峰值拟合
        
        Args:
            spectrum_json: JSON 格式的光谱数据数组
            position_json: JSON 格式的峰值位置
            fit_type_json: JSON 格式的拟合类型
            
        Returns:
            JSON 格式的结果
        """
        try:
            spectrum = np.array(json.loads(spectrum_json))
            position = json.loads(position_json)
            fit_type = json.loads(fit_type_json)
            
            peak_index = position.get("index", 0)
            fit_type_str = fit_type.get("type", "gaussian")
            
            fit_result = fit_peak_auto(spectrum, peak_index, fit_type_str)
            
            result = ApiResponse.ok(
                data=fit_result,
                message=f"峰值拟合完成，R²: {fit_result.get('r_squared', 'N/A'):.4f}"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except Exception as e:
            log.error(f"[Bridge] 峰值拟合失败：{e}")
            result = ApiResponse.error(ErrorCode.ALGORITHM_FAILED, str(e))
            return json.dumps(result.to_dict(), ensure_ascii=False)

    # ==================== P0-3 预处理 API ====================

    @Slot(str, str, result=str)
    def preprocess(self, spectrum_json: str, params_json: str) -> str:
        """
        谱图预处理
        
        Args:
            spectrum_json: JSON 格式的光谱数据数组
            params_json: JSON 格式的预处理参数
            
        Returns:
            JSON 格式的结果
        """
        try:
            spectrum = np.array(json.loads(spectrum_json))
            params = json.loads(params_json)
            
            tools = params.get("tools", [])
            result_spectrum = preprocess_spectrum(spectrum, tools)
            
            result = ApiResponse.ok(
                data={
                    "spectrum": result_spectrum.tolist(),
                    "applied_tools": tools
                },
                message="谱图预处理完成"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except Exception as e:
            log.error(f"[Bridge] 谱图预处理失败：{e}")
            result = ApiResponse.error(ErrorCode.ALGORITHM_FAILED, str(e))
            return json.dumps(result.to_dict(), ensure_ascii=False)

    # ==================== P0-4 差谱运算 API ====================

    @Slot(str, str, str, result=str)
    def subtractSpectra(self, spectrum1_json: str, spectrum2_json: str, coefficient_json: str) -> str:
        """
        差谱运算 - 两个光谱相减
        
        Args:
            spectrum1_json: JSON 格式的光谱 1 数据数组
            spectrum2_json: JSON 格式的光谱 2 数据数组
            coefficient_json: JSON 格式的系数
            
        Returns:
            JSON 格式的结果
        """
        try:
            spectrum1 = np.array(json.loads(spectrum1_json))
            spectrum2 = np.array(json.loads(spectrum2_json))
            coefficient_data = json.loads(coefficient_json)
            coefficient = float(coefficient_data.get("value", 1.0))
            
            # 验证维度
            if spectrum1.shape != spectrum2.shape:
                result = ApiResponse.error(
                    ErrorCode.SPECTRUM_DIMENSION_MISMATCH,
                    f"光谱维度不匹配：{spectrum1.shape} vs {spectrum2.shape}"
                )
                return json.dumps(result.to_dict(), ensure_ascii=False)
            
            difference = subtract_spectra(spectrum1, spectrum2, coefficient)
            
            result = ApiResponse.ok(
                data={
                    "difference": difference.tolist(),
                    "coefficient": coefficient
                },
                message="差谱运算完成"
            )
            return json.dumps(result.to_dict(), ensure_ascii=False)
            
        except Exception as e:
            log.error(f"[Bridge] 差谱运算失败：{e}")
            result = ApiResponse.error(ErrorCode.ALGORITHM_FAILED, str(e))
            return json.dumps(result.to_dict(), ensure_ascii=False)


class WorkerThread(QThread):
    """数据采集工作线程"""

    spectrumReady = Signal(list)
    errorOccurred = Signal(str)

    def __init__(self, driver: BaseDriver, sample_rate: float = 10.0,
                 integration_time: int = 100, accumulation_count: int = 1,
                 smoothing_window: int = 0, parent=None):
        super().__init__(parent)
        self._driver = driver
        self._sample_rate = np.clip(sample_rate, 0.1, 100.0)
        self._integration_time = integration_time
        self._accumulation_count = accumulation_count
        self._smoothing_window = smoothing_window
        self._running = False
        self._wavelengths = None
        self._acquiring = 0
        self._wait_condition = QWaitCondition()
        self._wait_mutex = QMutex()

        try:
            from backend.inference import MockInference
            self._inference = MockInference()
            self._inference.load_model("mock_model.onnx")
        except Exception as e:
            log.warning(f"[WorkerThread] 初始化推理模块失败：{e}")
            self._inference = None

    @property
    def integration_time(self) -> int:
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value: int):
        self._integration_time = int(value)

    @property
    def accumulation_count(self) -> int:
        return self._accumulation_count

    @accumulation_count.setter
    def accumulation_count(self, value: int):
        self._accumulation_count = int(value)

    @property
    def smoothing_window(self) -> int:
        return self._smoothing_window

    @smoothing_window.setter
    def smoothing_window(self, value: int):
        self._smoothing_window = int(value)

    @property
    def acquiring(self) -> bool:
        return bool(self._acquiring)

    @acquiring.setter
    def acquiring(self, value: bool):
        old_value = self._acquiring
        self._acquiring = 1 if value else 0
        if value and not old_value:
            with QMutexLocker(self._wait_mutex):
                self._wait_condition.wakeOne()

    def update_params(self, params: dict):
        """
        P0 修复：动态更新采集参数
        
        Args:
            params: 参数字典，可包含 integration_time, accumulation_count, smoothing_window
        """
        if 'integration_time' in params:
            self._integration_time = int(params['integration_time'])
        if 'accumulation_count' in params:
            self._accumulation_count = int(params['accumulation_count'])
        if 'smoothing_window' in params:
            self._smoothing_window = int(params['smoothing_window'])
        log.debug(f"[WorkerThread] 参数已更新：{params}")

    def run(self):
        """线程主循环"""
        self._running = True
        interval = 1.0 / self._sample_rate

        try:
            self._wavelengths = self._driver.get_wavelengths()
        except Exception as e:
            self.errorOccurred.emit(f"获取波长数据失败：{e}")
            return

        elapsed_timer = QElapsedTimer()

        while self._running:
            acquiring = bool(self._acquiring)

            if acquiring and self._driver.connected:
                elapsed_timer.start()
                try:
                    spectrum = self._driver.read_spectrum()
                    if spectrum is not None:
                        if self._smoothing_window > 1 and self._inference is not None:
                            spectrum = self._inference.smooth(spectrum, self._smoothing_window)
                        data = spectrum.tolist()
                        self.spectrumReady.emit(data)
                    else:
                        if not self._driver.connected:
                            self.errorOccurred.emit("设备未连接")
                except Exception as e:
                    error_msg = f"数据采集错误：{e}"
                    log.error(f"[WorkerThread] {error_msg}")
                    self.errorOccurred.emit(error_msg)

                elapsed = elapsed_timer.elapsed() / 1000.0
                sleep_time = max(0, (interval - elapsed) * 1000)
                if sleep_time > 0:
                    self.msleep(int(sleep_time))
            else:
                with QMutexLocker(self._wait_mutex):
                    self._wait_condition.wait(self._wait_mutex, 100)

    def stop(self):
        """优雅停止线程"""
        self._running = False
        self._acquiring = 0
        with QMutexLocker(self._wait_mutex):
            self._wait_condition.wakeOne()
        self.wait(1000)
        if self.isRunning():
            self.terminate()
            log.warning("[WorkerThread] 线程强制终止")


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.state_manager = StateManager()
        self.driver = MockDriver(seed=42, noise_level=0.02, simulate_failure=False)
        self.bridge = BridgeObject(self.state_manager, self.driver)
        self.worker_thread = WorkerThread(
            self.driver, sample_rate=10.0,
            integration_time=100, accumulation_count=1, smoothing_window=0
        )
        # P1 修复：使用公有方法设置 worker_thread
        self.bridge.set_worker_thread(self.worker_thread)
        self._setup_connections()
        self.setWindowTitle("拉曼光谱边缘客户端")
        self.setGeometry(100, 100, 1400, 900)
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        self._setup_webchannel()
        self._load_frontend()
        self.worker_thread.start()
        log.info("[Main] 应用程序初始化完成")

    def _setup_connections(self):
        """设置信号连接"""
        self.worker_thread.spectrumReady.connect(self._on_spectrum_ready)
        self.worker_thread.errorOccurred.connect(self._on_worker_error)
        self.state_manager.acquisitionChanged.connect(self._on_acquisition_changed)

    def _setup_webchannel(self):
        """设置 QWebChannel 通信"""
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("pythonBackend", self.bridge)
        profile = self.web_view.page().profile()
        profile.setHttpUserAgent("QWebEngineView")
        self.web_view.page().setWebChannel(self.web_channel)
        log.info("[Main] QWebChannel 设置完成")

    def _load_frontend(self):
        """加载前端 HTML 页面"""
        url = QUrl("qrc:///frontend/index.html")
        self.web_view.setUrl(url)
        log.info("[Main] 已加载前端页面：qrc:///frontend/index.html")

    def _on_acquisition_changed(self, state: AcquisitionState):
        """采集状态变化处理（P0 修复：启动时同步参数）"""
        if state == AcquisitionState.RUNNING:
            # P0 修复：启动采集前同步参数到 WorkerThread
            self.worker_thread.update_params({
                'integration_time': self.state_manager._params['integration_time'],
                'accumulation_count': self.state_manager._params['accumulation_count'],
                'smoothing_window': self.state_manager._params['smoothing_window']
            })
            log.info(f"[Main] 采集参数已同步到 WorkerThread: {self.state_manager._params}")
            self.worker_thread.acquiring = True
        else:
            self.worker_thread.acquiring = False

    def _on_spectrum_ready(self, spectrum):
        """光谱数据就绪"""
        self.bridge._spectrum_data = np.array(spectrum) if isinstance(spectrum, list) else spectrum
        self.bridge.spectrumReady.emit(spectrum)

    def _on_worker_error(self, error_msg: str):
        """工作线程错误处理"""
        log.error(f"[Main] 工作线程错误：{error_msg}")
        self.state_manager.report_error(error_msg)

    def closeEvent(self, event):
        """窗口关闭事件"""
        log.info("[Main] 正在关闭应用程序...")
        self.state_manager.stop_acquisition()
        self.worker_thread.stop()
        self.driver.disconnect()
        log.info("[Main] 应用程序已关闭")
        event.accept()


def main():
    """主函数"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("拉曼光谱边缘客户端")
    app.setOrganizationName("Edge-Client")

    splash = QSplashScreen()
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #1a1a2e;
            border: 2px solid #00d9ff;
            border-radius: 10px;
        }
        QLabel {
            color: #00d9ff;
            font-size: 24px;
            font-weight: bold;
        }
    """)
    splash_label = QLabel(splash)
    splash_label.setAlignment(Qt.AlignCenter)
    splash_label.setText("🔬 拉曼光谱边缘客户端\n\n正在初始化...")
    splash_label.setStyleSheet("color: #00d9ff; font-size: 18px; padding: 40px;")
    splash.resize(400, 200)
    splash.show()
    app.processEvents()

    window = MainWindow()
    app.processEvents()
    splash.finish(window)
    log.info("[Main] 启动画面已关闭")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
