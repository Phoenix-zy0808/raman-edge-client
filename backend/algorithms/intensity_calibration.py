"""
强度校准算法模块

提供强度校准功能，使用标准光源谱图校正光谱强度响应

P11 实现:
- 使用标准光源谱图计算校正曲线
- 支持维度验证
- 提供校正状态管理
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
import time
import logging

from ..error_handler import ApiResponse, ErrorCode, CalibrationLog

logger = logging.getLogger(__name__)


@dataclass
class IntensityCalibrationResult:
    """强度校准结果数据类"""
    success: bool
    correction_curve: np.ndarray
    wavelength_range: Tuple[float, float]
    message: str
    calibrated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "correction_curve": self.correction_curve.tolist() if isinstance(self.correction_curve, np.ndarray) else self.correction_curve,
            "wavelength_range": list(self.wavelength_range),
            "message": self.message,
            "calibrated_at": self.calibrated_at
        }


class IntensityCalibrator:
    """
    强度校准器
    
    使用标准光源谱图计算强度校正曲线，应用于后续测量
    
    校准原理:
    1. 采集标准光源的光谱
    2. 与标准光源的理论光谱比较
    3. 计算响应校正曲线 = 理论值 / 实测值
    4. 后续测量应用校正曲线：校正后 = 实测 × 校正曲线
    """
    
    def __init__(self):
        """初始化强度校准器"""
        self._calibrated = False
        self._correction_curve: Optional[np.ndarray] = None
        self._wavelength_range: Optional[Tuple[float, float]] = None
        self._calibration_time: Optional[float] = None
        self._reference_spectrum: Optional[np.ndarray] = None
    
    @property
    def is_calibrated(self) -> bool:
        """是否已校准"""
        return self._calibrated
    
    @property
    def correction_curve(self) -> Optional[np.ndarray]:
        """获取校正曲线"""
        return self._correction_curve
    
    @property
    def wavelength_range(self) -> Optional[Tuple[float, float]]:
        """获取波长范围"""
        return self._wavelength_range
    
    @property
    def calibration_time(self) -> Optional[float]:
        """获取校准时间"""
        return self._calibration_time
    
    def reset(self) -> None:
        """重置校准状态"""
        self._calibrated = False
        self._correction_curve = None
        self._wavelength_range = None
        self._calibration_time = None
        self._reference_spectrum = None
        logger.info("[Calibration] 强度校准已重置")
    
    def calibrate(
        self,
        reference_spectrum: np.ndarray,
        theoretical_spectrum: np.ndarray,
        wavenumbers: np.ndarray
    ) -> ApiResponse:
        """
        执行强度校准
        
        Args:
            reference_spectrum: 参考光源的实测光谱
            theoretical_spectrum: 参考光源的理论光谱（标准值）
            wavenumbers: 波数数据
        
        Returns:
            ApiResponse: 校准结果
        """
        # 参数验证
        if reference_spectrum is None or len(reference_spectrum) == 0:
            logger.error(CalibrationLog.intensity_calibration_failed(
                "参考光谱为空", ErrorCode.CALIBRATION_DATA_INVALID
            ))
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                "参考光谱不能为空"
            )
        
        if theoretical_spectrum is None or len(theoretical_spectrum) == 0:
            logger.error(CalibrationLog.intensity_calibration_failed(
                "理论光谱为空", ErrorCode.CALIBRATION_DATA_INVALID
            ))
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                "理论光谱不能为空"
            )
        
        if wavenumbers is None or len(wavenumbers) == 0:
            logger.error(CalibrationLog.intensity_calibration_failed(
                "波数数据为空", ErrorCode.CALIBRATION_DATA_INVALID
            ))
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                "波数数据不能为空"
            )
        
        # 维度验证
        if len(reference_spectrum) != len(theoretical_spectrum):
            logger.error(CalibrationLog.intensity_calibration_failed(
                f"光谱维度不匹配：{len(reference_spectrum)} != {len(theoretical_spectrum)}",
                ErrorCode.SPECTRUM_DIMENSION_MISMATCH
            ))
            return ApiResponse.error(
                ErrorCode.SPECTRUM_DIMENSION_MISMATCH,
                f"参考光谱和理论光谱维度不匹配：{len(reference_spectrum)} != {len(theoretical_spectrum)}"
            )
        
        if len(reference_spectrum) != len(wavenumbers):
            logger.error(CalibrationLog.intensity_calibration_failed(
                f"光谱与波数维度不匹配：{len(reference_spectrum)} != {len(wavenumbers)}",
                ErrorCode.SPECTRUM_DIMENSION_MISMATCH
            ))
            return ApiResponse.error(
                ErrorCode.SPECTRUM_DIMENSION_MISMATCH,
                f"光谱与波数维度不匹配：{len(reference_spectrum)} != {len(wavenumbers)}"
            )
        
        try:
            # 转换为 numpy 数组
            reference = np.array(reference_spectrum, dtype=np.float64)
            theoretical = np.array(theoretical_spectrum, dtype=np.float64)
            wavenumbers = np.array(wavenumbers, dtype=np.float64)
            
            # 检查数据有效性
            if np.any(reference <= 0):
                # 如果有零或负值，添加小偏移
                reference = reference + 1e-10
                logger.warning("[Calibration] 参考光谱包含零或负值，已添加小偏移")
            
            if np.any(theoretical <= 0):
                theoretical = theoretical + 1e-10
                logger.warning("[Calibration] 理论光谱包含零或负值，已添加小偏移")
            
            # 计算校正曲线 = 理论值 / 实测值
            correction_curve = theoretical / reference
            
            # 归一化校正曲线（使其平均值为 1）
            mean_correction = np.mean(correction_curve)
            correction_curve = correction_curve / mean_correction
            
            # 记录波长范围
            wavelength_range = (float(np.min(wavenumbers)), float(np.max(wavenumbers)))
            
            # 更新校准状态
            self._correction_curve = correction_curve
            self._wavelength_range = wavelength_range
            self._calibrated = True
            self._calibration_time = time.time()
            self._reference_spectrum = reference
            
            # 记录成功日志
            logger.info(CalibrationLog.intensity_calibration_success(wavelength_range))
            
            return ApiResponse.ok(
                data={
                    "correction_curve": correction_curve.tolist(),
                    "wavelength_range": list(wavelength_range),
                    "mean_correction": float(mean_correction),
                    "calibrated_at": self._calibration_time
                },
                message=f"强度校准成功，波长范围={wavelength_range}"
            )
            
        except Exception as e:
            logger.error(CalibrationLog.intensity_calibration_failed(str(e), ErrorCode.INTENSITY_CALIBRATION_ERROR))
            return ApiResponse.error(
                ErrorCode.INTENSITY_CALIBRATION_ERROR,
                f"强度校准异常：{str(e)}"
            )
    
    def apply_correction(self, spectrum: np.ndarray) -> ApiResponse:
        """
        应用强度校正
        
        Args:
            spectrum: 待校正的光谱数据
        
        Returns:
            ApiResponse: 校正结果，data 中包含 corrected_spectrum
        """
        if not self._calibrated:
            return ApiResponse.error(
                ErrorCode.CALIBRATION_FAILED,
                "强度校准未执行，请先进行校准"
            )
        
        if spectrum is None or len(spectrum) == 0:
            return ApiResponse.error(
                ErrorCode.SPECTRUM_EMPTY,
                "光谱数据为空"
            )
        
        try:
            spectrum_array = np.array(spectrum, dtype=np.float64)
            
            # 验证维度
            if len(spectrum_array) != len(self._correction_curve):
                return ApiResponse.error(
                    ErrorCode.SPECTRUM_DIMENSION_MISMATCH,
                    f"光谱维度与校正曲线不匹配：{len(spectrum_array)} != {len(self._correction_curve)}"
                )
            
            # 应用校正
            corrected_spectrum = spectrum_array * self._correction_curve
            
            return ApiResponse.ok(
                data={
                    "corrected_spectrum": corrected_spectrum.tolist(),
                    "original_spectrum": spectrum_array.tolist()
                },
                message="强度校正成功"
            )
            
        except Exception as e:
            logger.error(f"[Calibration] 强度校正失败：{e}")
            return ApiResponse.error(
                ErrorCode.INTENSITY_CALIBRATION_ERROR,
                f"强度校正异常：{str(e)}"
            )
    
    def get_status(self) -> ApiResponse:
        """
        获取校准状态
        
        Returns:
            ApiResponse: 校准状态信息
        """
        return ApiResponse.ok(
            data={
                "calibrated": self._calibrated,
                "wavelength_range": list(self._wavelength_range) if self._wavelength_range else None,
                "correction_curve_length": len(self._correction_curve) if self._correction_curve is not None else 0,
                "calibration_time": self._calibration_time
            }
        )
    
    def load_correction_curve(
        self,
        correction_curve: List[float],
        wavelength_range: Tuple[float, float]
    ) -> ApiResponse:
        """
        从外部加载校正曲线
        
        Args:
            correction_curve: 校正曲线数据
            wavelength_range: 波长范围
        
        Returns:
            ApiResponse: 加载结果
        """
        if not correction_curve or len(correction_curve) == 0:
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                "校正曲线不能为空"
            )
        
        try:
            self._correction_curve = np.array(correction_curve, dtype=np.float64)
            self._wavelength_range = wavelength_range
            self._calibrated = True
            self._calibration_time = time.time()
            
            logger.info(f"[Calibration] 校正曲线已加载，长度={len(correction_curve)}")
            
            return ApiResponse.ok(
                data={
                    "correction_curve_length": len(correction_curve),
                    "wavelength_range": list(wavelength_range)
                },
                message="校正曲线加载成功"
            )
            
        except Exception as e:
            logger.error(f"[Calibration] 校正曲线加载失败：{e}")
            return ApiResponse.error(
                ErrorCode.CALIBRATION_DATA_INVALID,
                f"校正曲线加载异常：{str(e)}"
            )
