"""
波长校准算法模块

提供波长校准功能，使用标准物质的已知特征峰位置校正光谱波长

P11 实现:
- 使用硅片 520 cm⁻¹ 特征峰作为参考
- 支持多点校准
- 提供校准状态管理
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import time
import logging

from ..error_handler import ApiResponse, ErrorCode, CalibrationLog

logger = logging.getLogger(__name__)


@dataclass
class WavelengthCalibrationResult:
    """波长校准结果数据类"""
    success: bool
    correction: float  # 波长校正值 (cm⁻¹)
    r_squared: float  # 拟合优度
    message: str
    calibrated_at: float = None
    
    def __post_init__(self):
        if self.calibrated_at is None:
            self.calibrated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "correction": self.correction,
            "r_squared": self.r_squared,
            "message": self.message,
            "calibrated_at": self.calibrated_at
        }


class WavelengthCalibrator:
    """
    波长校准器
    
    使用标准物质的已知特征峰位置进行波长校准
    
    支持的参考物质:
    - 硅片 (Si): 520.0 cm⁻¹
    - 金刚石 (Diamond): 1332.0 cm⁻¹
    - 石墨 (Graphite G 峰): 1580.0 cm⁻¹
    """
    
    # 标准物质特征峰位置 (cm⁻¹)
    REFERENCE_MATERIALS = {
        'silicon': 520.0,      # 硅片
        'diamond': 1332.0,     # 金刚石
        'graphite': 1580.0,    # 石墨 G 峰
    }
    
    # 校准容忍度 (cm⁻¹)
    TOLERANCE = 5.0
    
    def __init__(self):
        """初始化波长校准器"""
        self._calibrated = False
        self._correction = 0.0
        self._calibration_time: Optional[float] = None
        self._r_squared: float = 0.0
    
    @property
    def is_calibrated(self) -> bool:
        """是否已校准"""
        return self._calibrated
    
    @property
    def correction(self) -> float:
        """获取当前校正值"""
        return self._correction
    
    @property
    def calibration_time(self) -> Optional[float]:
        """获取校准时间"""
        return self._calibration_time
    
    def reset(self) -> None:
        """重置校准状态"""
        self._calibrated = False
        self._correction = 0.0
        self._calibration_time = None
        self._r_squared = 0.0
        logger.info("[Calibration] 波长校准已重置")
    
    def calibrate(
        self,
        reference_peaks: List[float],
        expected_positions: Optional[List[float]] = None,
        tolerance: Optional[float] = None
    ) -> ApiResponse:
        """
        执行波长校准
        
        Args:
            reference_peaks: 检测到的参考峰位置列表
            expected_positions: 期望的峰位置列表（默认使用硅片 520 cm⁻¹）
            tolerance: 容忍度（cm⁻¹），默认 5.0
        
        Returns:
            ApiResponse: 校准结果
        """
        # 参数验证
        if not reference_peaks:
            logger.error(CalibrationLog.wavelength_calibration_failed("参考峰位置为空", ErrorCode.CALIBRATION_DATA_INVALID))
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                "参考峰位置不能为空"
            )
        
        # 使用默认期望位置（硅片 520 cm⁻¹）
        if expected_positions is None:
            expected_positions = [self.REFERENCE_MATERIALS['silicon']]
        
        # 验证输入长度
        if len(reference_peaks) != len(expected_positions):
            logger.error(CalibrationLog.wavelength_calibration_failed(
                f"参考峰数量不匹配：{len(reference_peaks)} != {len(expected_positions)}",
                ErrorCode.INVALID_PARAMETER
            ))
            return ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"参考峰数量不匹配：{len(reference_peaks)} != {len(expected_positions)}"
            )
        
        # 使用自定义容忍度
        if tolerance is None:
            tolerance = self.TOLERANCE
        
        # 计算校正值
        try:
            reference_peaks = np.array(reference_peaks)
            expected_positions = np.array(expected_positions)
            
            # 计算每个峰的偏差
            deviations = reference_peaks - expected_positions
            
            # 检查偏差是否在容忍范围内
            max_deviation = np.max(np.abs(deviations))
            if max_deviation > tolerance:
                logger.error(CalibrationLog.wavelength_calibration_failed(
                    f"最大偏差 {max_deviation:.2f} cm⁻¹ 超出容忍范围 {tolerance} cm⁻¹",
                    ErrorCode.CALIBRATION_FAILED
                ))
                return ApiResponse.error(
                    ErrorCode.CALIBRATION_FAILED,
                    f"最大偏差 {max_deviation:.2f} cm⁻¹ 超出容忍范围 {tolerance} cm⁻¹"
                )
            
            # 计算平均校正值（取负，因为校正是要减去偏差）
            correction = -np.mean(deviations)
            
            # 计算拟合优度（R²）
            if len(deviations) > 1:
                r_squared = 1 - np.var(deviations) / (np.var(reference_peaks) + 1e-10)
            else:
                r_squared = 1.0
            
            # 更新校准状态
            self._correction = correction
            self._calibrated = True
            self._calibration_time = time.time()
            self._r_squared = r_squared
            
            # 记录成功日志
            logger.info(CalibrationLog.wavelength_calibration_success(correction))
            
            return ApiResponse.ok(
                data={
                    "correction": float(correction),
                    "r_squared": float(r_squared),
                    "max_deviation": float(max_deviation),
                    "calibrated_at": self._calibration_time
                },
                message=f"波长校准成功，校正值={correction:.3f} cm⁻¹"
            )
            
        except Exception as e:
            logger.error(CalibrationLog.wavelength_calibration_failed(str(e), ErrorCode.CALIBRATION_FAILED))
            return ApiResponse.error(
                ErrorCode.CALIBRATION_FAILED,
                f"波长校准异常：{str(e)}"
            )
    
    def find_peak_position(
        self,
        spectrum: np.ndarray,
        wavenumbers: np.ndarray,
        expected_position: float,
        search_range: float = 20.0
    ) -> Optional[float]:
        """
        在光谱中查找特征峰位置
        
        Args:
            spectrum: 光谱强度数据
            wavenumbers: 波数数据
            expected_position: 期望的峰位置
            search_range: 搜索范围（cm⁻¹）
        
        Returns:
            检测到的峰位置，如果未找到则返回 None
        """
        try:
            # 确定搜索范围
            min_wavenumber = expected_position - search_range
            max_wavenumber = expected_position + search_range
            
            # 找到搜索范围内的索引
            mask = (wavenumbers >= min_wavenumber) & (wavenumbers <= max_wavenumber)
            if not np.any(mask):
                return None
            
            search_spectrum = spectrum[mask]
            search_wavenumbers = wavenumbers[mask]
            
            # 找到最大强度的位置
            max_index = np.argmax(search_spectrum)
            peak_position = search_wavenumbers[max_index]
            
            logger.debug(f"[Calibration] 检测到峰位置：{peak_position:.2f} cm⁻¹ (期望：{expected_position:.2f} cm⁻¹)")
            
            return float(peak_position)
            
        except Exception as e:
            logger.error(f"[Calibration] 峰值检测失败：{e}")
            return None
    
    def apply_correction(self, wavenumbers: np.ndarray) -> np.ndarray:
        """
        应用波长校正
        
        Args:
            wavenumbers: 原始波数数据
        
        Returns:
            校正后的波数数据
        """
        if not self._calibrated:
            logger.warning("[Calibration] 警告：未校准状态下应用校正")
            return wavenumbers.copy()
        
        return wavenumbers + self._correction
    
    def get_status(self) -> ApiResponse:
        """
        获取校准状态
        
        Returns:
            ApiResponse: 校准状态信息
        """
        return ApiResponse.ok(
            data={
                "calibrated": self._calibrated,
                "correction": self._correction if self._calibrated else 0.0,
                "calibration_time": self._calibration_time,
                "r_squared": self._r_squared if self._calibrated else 0.0
            }
        )
