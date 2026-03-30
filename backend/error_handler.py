"""
错误处理模块

提供统一的错误码定义、错误处理策略和用户友好消息映射

P11 修复（第二轮）:
- 重构错误码分类，使其连续且有意义
- 创建统一的 API 响应类
- 统一日志格式规范
"""
from enum import IntEnum
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, field
import logging
import time

logger = logging.getLogger(__name__)


# ==================== 统一的 API 响应格式 ====================

@dataclass
class ApiResponse:
    """
    统一的 API 响应格式
    
    所有后端方法都应返回此格式，确保前端调用一致性
    
    Attributes:
        success: 操作是否成功
        error_code: 错误码（成功时为 0 或 None）
        message: 用户友好的消息
        data: 响应数据（可选）
        timestamp: 时间戳
    """
    success: bool
    error_code: Optional[int] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "success": self.success,
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def ok(cls, data: Optional[Dict[str, Any]] = None, message: str = "操作成功") -> "ApiResponse":
        """创建成功响应"""
        return cls(success=True, error_code=None, message=message, data=data)
    
    @classmethod
    def error(cls, error_code: int, message: str, data: Optional[Dict[str, Any]] = None) -> "ApiResponse":
        """创建错误响应"""
        return cls(success=False, error_code=error_code, message=message, data=data)


# ==================== 错误码定义 ====================

class ErrorCode(IntEnum):
    """
    错误码枚举
    
    错误码分类（P11 重构：连续编号，避免跳跃）:
    0-99:    系统级错误
    100-199: 设备相关错误
    200-249: 数据采集错误
    250-279: 校准相关错误（波长、强度、自动曝光）
    280-299: 保留
    300-349: 数据处理错误
    350-399: 谱图数据错误
    400-499: 文件操作错误
    500-599: 网络/通信错误
    """
    # ==================== 系统级错误 (0-99) ====================
    UNKNOWN_ERROR = 0
    INVALID_PARAMETER = 1
    NOT_INITIALIZED = 2
    OUT_OF_MEMORY = 3
    UNSUPPORTED_OPERATION = 4
    
    # ==================== 设备相关错误 (100-199) ====================
    DEVICE_NOT_FOUND = 100
    DEVICE_INIT_FAILED = 101
    DEVICE_CONNECTION_FAILED = 102
    DEVICE_DISCONNECTED = 103
    DEVICE_BUSY = 104
    DEVICE_TIMEOUT = 105
    DEVICE_STATE_ERROR = 106
    
    # ==================== 数据采集错误 (200-249) ====================
    ACQUISITION_NOT_STARTED = 200
    ACQUISITION_FAILED = 201
    ACQUISITION_TIMEOUT = 202
    SPECTRUM_READ_FAILED = 203
    SPECTRUM_INVALID = 204
    SPECTRUM_EMPTY = 205
    
    # ==================== 校准相关错误 (250-279) ====================
    # 通用校准错误 (250-254)
    CALIBRATION_FAILED = 250
    CALIBRATION_TIMEOUT = 251
    REFERENCE_PEAK_NOT_FOUND = 252
    CALIBRATION_DATA_INVALID = 253
    
    # 波长校准错误 (255-259)
    WAVELENGTH_CALIBRATION_ERROR = 255
    
    # 强度校准错误 (260-264)
    INTENSITY_CALIBRATION_ERROR = 260
    INTENSITY_REFERENCE_INVALID = 261
    
    # 自动曝光错误 (265-269)
    AUTO_EXPOSURE_TIMEOUT = 265
    AUTO_EXPOSURE_FAILED = 266
    
    # ==================== 数据处理错误 (300-349) ====================
    ALGORITHM_FAILED = 300
    SMOOTHING_FAILED = 301
    BASELINE_CORRECTION_FAILED = 302
    PEAK_DETECTION_FAILED = 303
    LIBRARY_MATCH_FAILED = 304
    PEAK_AREA_CALCULATION_FAILED = 305
    
    # ==================== 谱图数据错误 (350-399) ====================
    INVALID_SPECTRUM_FORMAT = 350
    SPECTRUM_DIMENSION_MISMATCH = 351
    SPECTRUM_WAVELENGTH_RANGE_ERROR = 352
    
    # ==================== 文件操作错误 (400-499) ====================
    FILE_NOT_FOUND = 400
    FILE_READ_FAILED = 401
    FILE_WRITE_FAILED = 402
    FILE_FORMAT_UNSUPPORTED = 403
    FILE_PERMISSION_DENIED = 404
    
    # ==================== 网络/通信错误 (500-599) ====================
    NETWORK_ERROR = 500
    CONNECTION_TIMEOUT = 501
    BRIDGE_ERROR = 502


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    code: ErrorCode
    message: str
    level: str  # 'critical', 'error', 'warning', 'info'
    retryable: bool = False
    suggestion: str = ""


# 错误处理策略表
ERROR_STRATEGIES: Dict[ErrorCode, ErrorInfo] = {
    # 系统级错误
    ErrorCode.UNKNOWN_ERROR: ErrorInfo(
        code=ErrorCode.UNKNOWN_ERROR,
        message="发生未知错误",
        level="error",
        retryable=False,
        suggestion="请记录操作步骤并联系开发人员"
    ),
    ErrorCode.INVALID_PARAMETER: ErrorInfo(
        code=ErrorCode.INVALID_PARAMETER,
        message="参数无效",
        level="warning",
        retryable=True,
        suggestion="请检查输入参数是否正确"
    ),
    ErrorCode.NOT_INITIALIZED: ErrorInfo(
        code=ErrorCode.NOT_INITIALIZED,
        message="系统未初始化",
        level="error",
        retryable=False,
        suggestion="请重新启动程序"
    ),
    
    # 设备相关错误
    ErrorCode.DEVICE_NOT_FOUND: ErrorInfo(
        code=ErrorCode.DEVICE_NOT_FOUND,
        message="未找到设备",
        level="error",
        retryable=True,
        suggestion="请检查设备是否正确连接并开启电源"
    ),
    ErrorCode.DEVICE_INIT_FAILED: ErrorInfo(
        code=ErrorCode.DEVICE_INIT_FAILED,
        message="设备初始化失败",
        level="error",
        retryable=True,
        suggestion="请重启设备后重试"
    ),
    ErrorCode.DEVICE_CONNECTION_FAILED: ErrorInfo(
        code=ErrorCode.DEVICE_CONNECTION_FAILED,
        message="设备连接失败",
        level="error",
        retryable=True,
        suggestion="请检查 USB 连接是否正常"
    ),
    ErrorCode.DEVICE_DISCONNECTED: ErrorInfo(
        code=ErrorCode.DEVICE_DISCONNECTED,
        message="设备已断开",
        level="warning",
        retryable=True,
        suggestion="请重新连接设备"
    ),
    ErrorCode.DEVICE_TIMEOUT: ErrorInfo(
        code=ErrorCode.DEVICE_TIMEOUT,
        message="设备响应超时",
        level="warning",
        retryable=True,
        suggestion="请检查设备状态后重试"
    ),
    
    # 数据采集错误
    ErrorCode.ACQUISITION_NOT_STARTED: ErrorInfo(
        code=ErrorCode.ACQUISITION_NOT_STARTED,
        message="采集未开始",
        level="warning",
        retryable=False,
        suggestion="请先开始数据采集"
    ),
    ErrorCode.ACQUISITION_FAILED: ErrorInfo(
        code=ErrorCode.ACQUISITION_FAILED,
        message="数据采集失败",
        level="error",
        retryable=True,
        suggestion="请检查设备状态后重试"
    ),
    ErrorCode.SPECTRUM_READ_FAILED: ErrorInfo(
        code=ErrorCode.SPECTRUM_READ_FAILED,
        message="光谱读取失败",
        level="error",
        retryable=True,
        suggestion="请检查设备是否正常采集"
    ),
    ErrorCode.SPECTRUM_INVALID: ErrorInfo(
        code=ErrorCode.SPECTRUM_INVALID,
        message="光谱数据无效",
        level="warning",
        retryable=False,
        suggestion="请重新采集光谱数据"
    ),
    ErrorCode.SPECTRUM_EMPTY: ErrorInfo(
        code=ErrorCode.SPECTRUM_EMPTY,
        message="光谱数据为空",
        level="warning",
        retryable=False,
        suggestion="请先采集光谱数据"
    ),

    # ==================== 校准相关错误策略 ====================
    ErrorCode.CALIBRATION_FAILED: ErrorInfo(
        code=ErrorCode.CALIBRATION_FAILED,
        message="校准失败",
        level="error",
        retryable=True,
        suggestion="请检查参考物质和参数设置"
    ),
    ErrorCode.CALIBRATION_TIMEOUT: ErrorInfo(
        code=ErrorCode.CALIBRATION_TIMEOUT,
        message="校准超时",
        level="warning",
        retryable=True,
        suggestion="请重试或手动调节参数"
    ),
    ErrorCode.REFERENCE_PEAK_NOT_FOUND: ErrorInfo(
        code=ErrorCode.REFERENCE_PEAK_NOT_FOUND,
        message="未找到参考峰",
        level="error",
        retryable=True,
        suggestion="请检查参考物质是否正确放置"
    ),
    ErrorCode.CALIBRATION_DATA_INVALID: ErrorInfo(
        code=ErrorCode.CALIBRATION_DATA_INVALID,
        message="校准数据无效",
        level="error",
        retryable=True,
        suggestion="请检查校准数据格式"
    ),

    # 波长校准错误
    ErrorCode.WAVELENGTH_CALIBRATION_ERROR: ErrorInfo(
        code=ErrorCode.WAVELENGTH_CALIBRATION_ERROR,
        message="波长校准错误",
        level="error",
        retryable=True,
        suggestion="请使用标准物质重新校准"
    ),

    # 强度校准错误
    ErrorCode.INTENSITY_CALIBRATION_ERROR: ErrorInfo(
        code=ErrorCode.INTENSITY_CALIBRATION_ERROR,
        message="强度校准错误",
        level="error",
        retryable=True,
        suggestion="请检查标准光源谱图是否有效"
    ),
    ErrorCode.INTENSITY_REFERENCE_INVALID: ErrorInfo(
        code=ErrorCode.INTENSITY_REFERENCE_INVALID,
        message="强度参考谱图无效",
        level="error",
        retryable=True,
        suggestion="请检查参考谱图格式和维度"
    ),

    # 自动曝光错误
    ErrorCode.AUTO_EXPOSURE_TIMEOUT: ErrorInfo(
        code=ErrorCode.AUTO_EXPOSURE_TIMEOUT,
        message="自动曝光超时",
        level="warning",
        retryable=True,
        suggestion="请手动调节积分时间"
    ),
    ErrorCode.AUTO_EXPOSURE_FAILED: ErrorInfo(
        code=ErrorCode.AUTO_EXPOSURE_FAILED,
        message="自动曝光失败",
        level="error",
        retryable=True,
        suggestion="请检查设备状态后重试"
    ),

    # ==================== 数据处理错误策略 ====================
    ErrorCode.ALGORITHM_FAILED: ErrorInfo(
        code=ErrorCode.ALGORITHM_FAILED,
        message="算法执行失败",
        level="error",
        retryable=True,
        suggestion="请检查输入数据格式"
    ),
    ErrorCode.SMOOTHING_FAILED: ErrorInfo(
        code=ErrorCode.SMOOTHING_FAILED,
        message="平滑滤波失败",
        level="warning",
        retryable=True,
        suggestion="请调整平滑窗口大小"
    ),
    ErrorCode.BASELINE_CORRECTION_FAILED: ErrorInfo(
        code=ErrorCode.BASELINE_CORRECTION_FAILED,
        message="基线校正失败",
        level="warning",
        retryable=True,
        suggestion="请尝试其他基线校正方法"
    ),
    ErrorCode.PEAK_DETECTION_FAILED: ErrorInfo(
        code=ErrorCode.PEAK_DETECTION_FAILED,
        message="峰值检测失败",
        level="warning",
        retryable=True,
        suggestion="请调整峰值检测参数"
    ),
    ErrorCode.LIBRARY_MATCH_FAILED: ErrorInfo(
        code=ErrorCode.LIBRARY_MATCH_FAILED,
        message="谱库匹配失败",
        level="warning",
        retryable=False,
        suggestion="请检查谱库是否完整"
    ),
    ErrorCode.PEAK_AREA_CALCULATION_FAILED: ErrorInfo(
        code=ErrorCode.PEAK_AREA_CALCULATION_FAILED,
        message="峰面积计算失败",
        level="warning",
        retryable=True,
        suggestion="请检查峰值检测参数"
    ),

    # ==================== 谱图数据错误策略 ====================
    ErrorCode.INVALID_SPECTRUM_FORMAT: ErrorInfo(
        code=ErrorCode.INVALID_SPECTRUM_FORMAT,
        message="光谱数据格式无效",
        level="error",
        retryable=True,
        suggestion="请检查数据格式是否为 numpy array 或 list"
    ),
    ErrorCode.SPECTRUM_DIMENSION_MISMATCH: ErrorInfo(
        code=ErrorCode.SPECTRUM_DIMENSION_MISMATCH,
        message="光谱维度不匹配",
        level="error",
        retryable=True,
        suggestion="请确保输入光谱维度一致"
    ),
    ErrorCode.SPECTRUM_WAVELENGTH_RANGE_ERROR: ErrorInfo(
        code=ErrorCode.SPECTRUM_WAVELENGTH_RANGE_ERROR,
        message="光谱波长范围错误",
        level="error",
        retryable=True,
        suggestion="请检查波长范围是否在设备支持范围内"
    ),

    # ==================== 文件操作错误策略 ====================
    ErrorCode.FILE_NOT_FOUND: ErrorInfo(
        code=ErrorCode.FILE_NOT_FOUND,
        message="文件不存在",
        level="error",
        retryable=False,
        suggestion="请检查文件路径是否正确"
    ),
    ErrorCode.FILE_READ_FAILED: ErrorInfo(
        code=ErrorCode.FILE_READ_FAILED,
        message="文件读取失败",
        level="error",
        retryable=True,
        suggestion="请检查文件是否被占用"
    ),
    ErrorCode.FILE_WRITE_FAILED: ErrorInfo(
        code=ErrorCode.FILE_WRITE_FAILED,
        message="文件写入失败",
        level="error",
        retryable=True,
        suggestion="请检查磁盘空间是否充足"
    ),
    ErrorCode.FILE_FORMAT_UNSUPPORTED: ErrorInfo(
        code=ErrorCode.FILE_FORMAT_UNSUPPORTED,
        message="不支持的文件格式",
        level="warning",
        retryable=False,
        suggestion="请使用支持的格式：JSON, CSV, SPC"
    ),
    ErrorCode.FILE_PERMISSION_DENIED: ErrorInfo(
        code=ErrorCode.FILE_PERMISSION_DENIED,
        message="文件访问被拒绝",
        level="error",
        retryable=False,
        suggestion="请检查文件权限设置"
    ),
    
    # 网络/通信错误
    ErrorCode.NETWORK_ERROR: ErrorInfo(
        code=ErrorCode.NETWORK_ERROR,
        message="网络错误",
        level="error",
        retryable=True,
        suggestion="请检查网络连接"
    ),
    ErrorCode.CONNECTION_TIMEOUT: ErrorInfo(
        code=ErrorCode.CONNECTION_TIMEOUT,
        message="连接超时",
        level="warning",
        retryable=True,
        suggestion="请检查网络后重试"
    ),
    ErrorCode.BRIDGE_ERROR: ErrorInfo(
        code=ErrorCode.BRIDGE_ERROR,
        message="通信桥接错误",
        level="error",
        retryable=False,
        suggestion="请重启程序"
    ),
}


class ErrorHandler:
    """
    错误处理器
    
    提供统一的错误处理接口
    """
    
    def __init__(self):
        self._error_handlers: Dict[ErrorCode, Callable] = {}
        self._error_history: list = []
        self._max_history = 100
    
    def register_handler(self, code: ErrorCode, handler: Callable[[ErrorInfo], None]):
        """
        注册错误处理回调
        
        Args:
            code: 错误码
            handler: 处理函数
        """
        self._error_handlers[code] = handler
        logger.debug(f"注册错误处理器：{code.name}")
    
    def handle(self, code: ErrorCode, custom_message: Optional[str] = None, 
               extra_info: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """
        处理错误
        
        Args:
            code: 错误码
            custom_message: 自定义错误消息（可选）
            extra_info: 额外信息
            
        Returns:
            ErrorInfo 错误信息对象
        """
        # 获取错误信息
        error_info = ERROR_STRATEGIES.get(code)
        
        if error_info is None:
            # 未知错误码，使用默认
            error_info = ErrorInfo(
                code=ErrorCode.UNKNOWN_ERROR,
                message=f"未知错误码：{code}",
                level="error",
                retryable=False
            )
        
        # 使用自定义消息（如果有）
        if custom_message:
            error_info = ErrorInfo(
                code=error_info.code,
                message=custom_message,
                level=error_info.level,
                retryable=error_info.retryable,
                suggestion=error_info.suggestion
            )
        
        # 记录错误历史
        self._error_history.append({
            'code': code,
            'info': error_info,
            'extra': extra_info,
            'timestamp': __import__('time').time()
        })
        
        # 限制历史记录长度
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
        
        # 记录日志
        log_method = getattr(logger, error_info.level)
        log_method(f"[错误 {code.name}] {error_info.message}")
        if extra_info:
            log_method(f"额外信息：{extra_info}")
        
        # 调用注册的处理器
        if code in self._error_handlers:
            try:
                self._error_handlers[code](error_info)
            except Exception as e:
                logger.error(f"错误处理器执行失败：{e}")
        
        return error_info
    
    def get_user_message(self, code: ErrorCode) -> str:
        """
        获取用户友好消息
        
        Args:
            code: 错误码
            
        Returns:
            用户友好消息
        """
        error_info = ERROR_STRATEGIES.get(code)
        if error_info:
            msg = f"{error_info.message}"
            if error_info.suggestion:
                msg += f"。{error_info.suggestion}"
            return msg
        return f"发生错误：{code}"
    
    def get_error_history(self, limit: int = 10) -> list:
        """
        获取错误历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            错误历史列表
        """
        return self._error_history[-limit:]
    
    def clear_history(self):
        """清除错误历史"""
        self._error_history = []


# 全局错误处理器实例
global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return global_error_handler


def handle_error(code: ErrorCode, message: Optional[str] = None,
                 extra: Optional[Dict] = None) -> ErrorInfo:
    """
    便捷错误处理函数

    Args:
        code: 错误码
        message: 自定义消息
        extra: 额外信息

    Returns:
        ErrorInfo 错误信息
    """
    return global_error_handler.handle(code, message, extra)


def get_user_message(code: ErrorCode) -> str:
    """
    获取用户友好消息

    Args:
        code: 错误码

    Returns:
        用户友好消息
    """
    return global_error_handler.get_user_message(code)


# ==================== 日志格式规范 ====================

class LogFormat:
    """
    日志格式规范
    
    P11 统一日志格式:
    - 成功：log.info(f"[{module}] 操作成功：{detail}")
    - 失败：log.error(f"[{module}] 操作失败：{reason}, 错误码={code}")
    - 调试：log.debug(f"[{module}] 详细过程：{data}")
    - 警告：log.warning(f"[{module}] 警告信息：{reason}")
    
    模块前缀规范:
    - [Calibration]     - 校准模块（波长、强度）
    - [AutoExposure]    - 自动曝光模块
    - [Acquisition]     - 数据采集模块
    - [Processing]      - 数据处理模块（平滑、基线、峰值检测）
    - [Library]         - 谱库匹配模块
    - [Export]          - 数据导出模块
    - [Main]            - 主程序
    """
    
    # 模块前缀
    MODULE_CALIBRATION = "Calibration"
    MODULE_AUTO_EXPOSURE = "AutoExposure"
    MODULE_ACQUISITION = "Acquisition"
    MODULE_PROCESSING = "Processing"
    MODULE_LIBRARY = "Library"
    MODULE_EXPORT = "Export"
    MODULE_MAIN = "Main"
    
    @staticmethod
    def format_success(module: str, action: str, detail: str = "") -> str:
        """格式化成功日志"""
        if detail:
            return f"[{module}] {action}成功：{detail}"
        return f"[{module}] {action}成功"
    
    @staticmethod
    def format_error(module: str, action: str, reason: str, code: int = None) -> str:
        """格式化错误日志"""
        if code is not None:
            return f"[{module}] {action}失败：{reason}, 错误码={code}"
        return f"[{module}] {action}失败：{reason}"
    
    @staticmethod
    def format_debug(module: str, message: str) -> str:
        """格式化调试日志"""
        return f"[{module}] {message}"
    
    @staticmethod
    def format_warning(module: str, message: str) -> str:
        """格式化警告日志"""
        return f"[{module}] 警告：{message}"


class CalibrationLog(LogFormat):
    """校准模块日志格式"""
    MODULE = LogFormat.MODULE_CALIBRATION
    
    @classmethod
    def wavelength_calibration_success(cls, correction: float) -> str:
        return cls.format_success(cls.MODULE, "波长校准", f"校正值={correction:.3f} cm⁻¹")
    
    @classmethod
    def wavelength_calibration_failed(cls, reason: str, code: int = None) -> str:
        return cls.format_error(cls.MODULE, "波长校准", reason, code)
    
    @classmethod
    def intensity_calibration_success(cls, wavelength_range: tuple) -> str:
        return cls.format_success(cls.MODULE, "强度校准", f"校正范围={wavelength_range}")
    
    @classmethod
    def intensity_calibration_failed(cls, reason: str, code: int = None) -> str:
        return cls.format_error(cls.MODULE, "强度校准", reason, code)
    
    @classmethod
    def calibration_iteration(cls, iteration: int, value: float, target: float) -> str:
        return cls.format_debug(cls.MODULE, f"迭代 {iteration}: 当前值={value:.3f}, 目标={target:.3f}")


class AutoExposureLog(LogFormat):
    """自动曝光模块日志格式"""
    MODULE = LogFormat.MODULE_AUTO_EXPOSURE
    
    @classmethod
    def auto_exposure_success(cls, final_time: int, iterations: int) -> str:
        return cls.format_success(cls.MODULE, "自动曝光", f"最终积分时间={final_time}ms, 迭代次数={iterations}")
    
    @classmethod
    def auto_exposure_failed(cls, reason: str, code: int = None) -> str:
        return cls.format_error(cls.MODULE, "自动曝光", reason, code)
    
    @classmethod
    def auto_exposure_timeout(cls, iterations: int) -> str:
        return cls.format_warning(cls.MODULE, f"自动曝光超时：{iterations}次迭代内无法收敛")
    
    @classmethod
    def exposure_adjustment(cls, current_time: int, new_time: int, intensity: float) -> str:
        return cls.format_debug(cls.MODULE, f"调节积分时间：{current_time}ms → {new_time}ms, 强度={intensity:.3f}")
