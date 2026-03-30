"""
自动曝光算法模块

提供自动曝光功能，通过迭代调节积分时间获得合适的光谱强度

P11 实现:
- 使用二分查找算法
- 最大迭代次数可配置
- 提供详细的迭代日志
"""
import numpy as np
from typing import Optional, Dict, Any, Callable
import time
import logging

from ..error_handler import ApiResponse, ErrorCode, AutoExposureLog

logger = logging.getLogger(__name__)


class AutoExposure:
    """
    自动曝光控制器
    
    通过迭代调节积分时间，使光谱强度达到目标范围
    
    算法:
    1. 使用二分查找在积分时间范围内搜索
    2. 每次迭代采集光谱并评估强度
    3. 根据强度与目标的差距调整积分时间
    4. 达到目标范围或最大迭代次数后停止
    """
    
    # 默认参数
    DEFAULT_TARGET_INTENSITY = 0.7  # 目标强度（70% 满量程）
    DEFAULT_TOLERANCE = 0.1  # 容忍度（±10%）
    DEFAULT_MAX_ITERATIONS = 3  # 最大迭代次数
    DEFAULT_MIN_TIME = 10  # 最小积分时间 (ms)
    DEFAULT_MAX_TIME = 10000  # 最大积分时间 (ms)
    
    def __init__(
        self,
        target_intensity: float = DEFAULT_TARGET_INTENSITY,
        tolerance: float = DEFAULT_TOLERANCE,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        min_integration_time: int = DEFAULT_MIN_TIME,
        max_integration_time: int = DEFAULT_MAX_TIME
    ):
        """
        初始化自动曝光控制器
        
        Args:
            target_intensity: 目标强度（0.5-0.8）
            tolerance: 容忍度（默认±10%）
            max_iterations: 最大迭代次数
            min_integration_time: 最小积分时间 (ms)
            max_integration_time: 最大积分时间 (ms)
        """
        self._target_intensity = target_intensity
        self._tolerance = tolerance
        self._max_iterations = max_iterations
        self._min_time = min_integration_time
        self._max_time = max_integration_time
        
        self._enabled = False
        self._current_integration_time: Optional[int] = None
        self._last_result: Optional[Dict[str, Any]] = None
    
    @property
    def enabled(self) -> bool:
        """是否启用自动曝光"""
        return self._enabled
    
    @property
    def target_intensity(self) -> float:
        """目标强度"""
        return self._target_intensity
    
    @property
    def current_integration_time(self) -> Optional[int]:
        """当前积分时间"""
        return self._current_integration_time
    
    def set_target_intensity(self, intensity: float) -> ApiResponse:
        """
        设置目标强度
        
        Args:
            intensity: 目标强度（0.5-0.8）
        
        Returns:
            ApiResponse: 设置结果
        """
        if not 0.5 <= intensity <= 0.8:
            return ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"目标强度必须在 0.5-0.8 范围内，当前值：{intensity}"
            )
        
        self._target_intensity = intensity
        logger.info(f"[AutoExposure] 目标强度已设置为 {intensity:.2f}")
        
        return ApiResponse.ok(
            data={"target_intensity": intensity},
            message=f"目标强度已设置为 {intensity:.2f}"
        )
    
    def set_enabled(self, enabled: bool) -> None:
        """
        设置自动曝光启用状态
        
        Args:
            enabled: 是否启用
        """
        self._enabled = enabled
        logger.info(f"[AutoExposure] 自动曝光已{'启用' if enabled else '禁用'}")
    
    def get_status(self) -> ApiResponse:
        """
        获取自动曝光状态
        
        Returns:
            ApiResponse: 状态信息
        """
        return ApiResponse.ok(
            data={
                "enabled": self._enabled,
                "target_intensity": self._target_intensity,
                "current_integration_time": self._current_integration_time,
                "last_result": self._last_result
            }
        )
    
    def execute(
        self,
        acquire_spectrum: Callable[[int], np.ndarray],
        current_integration_time: int,
        max_iterations: Optional[int] = None
    ) -> ApiResponse:
        """
        执行自动曝光
        
        Args:
            acquire_spectrum: 采集光谱的函数，签名：(integration_time_ms) -> spectrum
            current_integration_time: 当前积分时间 (ms)
            max_iterations: 最大迭代次数（可选，覆盖默认值）
        
        Returns:
            ApiResponse: 自动曝光结果
        """
        if max_iterations is None:
            max_iterations = self._max_iterations
        
        # 验证目标强度
        if not 0.5 <= self._target_intensity <= 0.8:
            return ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"目标强度必须在 0.5-0.8 范围内"
            )
        
        # 验证积分时间范围
        if not self._min_time <= current_integration_time <= self._max_time:
            return ApiResponse.error(
                ErrorCode.INVALID_PARAMETER,
                f"当前积分时间必须在 {self._min_time}-{self._max_time} ms 范围内"
            )
        
        logger.info(AutoExposureLog.auto_exposure_success(
            current_integration_time, 0  # 初始值，仅用于日志格式
        ))
        logger.info(f"[AutoExposure] 开始自动曝光，目标强度={self._target_intensity:.2f}")
        
        try:
            # 二分查找参数
            low = self._min_time
            high = self._max_time
            best_time = current_integration_time
            best_intensity = 0.0
            
            target_min = self._target_intensity - self._tolerance
            target_max = self._target_intensity + self._tolerance
            
            iterations = 0
            
            for iteration in range(max_iterations):
                iterations = iteration + 1

                # 采集当前积分时间的光谱
                try:
                    spectrum = acquire_spectrum(current_integration_time)
                except Exception as e:
                    logger.error(AutoExposureLog.auto_exposure_failed(
                        f"光谱采集失败：{e}", ErrorCode.ACQUISITION_FAILED
                    ))
                    return ApiResponse.error(
                        ErrorCode.ACQUISITION_FAILED,
                        f"光谱采集失败：{e}"
                    )

                # ✅ 检查光谱有效性
                if spectrum is None or len(spectrum) == 0:
                    logger.error(AutoExposureLog.auto_exposure_failed(
                        "光谱数据为空", ErrorCode.ACQUISITION_FAILED
                    ))
                    return ApiResponse.error(
                        ErrorCode.ACQUISITION_FAILED,
                        "光谱采集失败：返回空数据"
                    )

                # 计算归一化强度（0-1）
                max_intensity = np.max(spectrum)
                min_intensity = np.min(spectrum)
                intensity_range = max_intensity - min_intensity

                if intensity_range == 0:
                    normalized_intensity = 0.0
                else:
                    # 使用峰值强度作为评估指标
                    normalized_intensity = float(max_intensity)
                    # 假设光谱已经归一化到 0-1 范围
                    normalized_intensity = min(1.0, max(0.0, normalized_intensity))

                logger.debug(AutoExposureLog.exposure_adjustment(
                    current_integration_time,
                    current_integration_time,  # 新值待计算
                    normalized_intensity
                ))
                logger.debug(f"[AutoExposure] 迭代 {iteration}: 积分时间={current_integration_time}ms, 强度={normalized_intensity:.3f}")

                # ✅ 检查光谱饱和情况（intensity = 1.0）
                if normalized_intensity >= 1.0 or np.any(spectrum >= 1.0):
                    logger.warning(f"[AutoExposure] 光谱饱和，强度={normalized_intensity:.3f}")
                    # 饱和时减小积分时间
                    high = current_integration_time
                    current_integration_time = int((low + high) / 2)
                    current_integration_time = max(self._min_time, min(self._max_time, current_integration_time))
                    continue

                # 记录最佳结果
                if abs(normalized_intensity - self._target_intensity) < abs(best_intensity - self._target_intensity):
                    best_time = current_integration_time
                    best_intensity = normalized_intensity

                # ✅ 检查暗光谱情况（intensity = 0）
                if normalized_intensity == 0:
                    logger.warning(f"[AutoExposure] 检测到暗光谱，强度=0，增加积分时间")
                    # 暗光谱时增加积分时间
                    low = current_integration_time
                    current_integration_time = int((low + high) / 2)
                    current_integration_time = max(self._min_time, min(self._max_time, current_integration_time))
                    continue

                # 检查是否在目标范围内
                if target_min <= normalized_intensity <= target_max:
                    logger.info(AutoExposureLog.auto_exposure_success(current_integration_time, iterations))
                    self._current_integration_time = current_integration_time
                    self._last_result = {
                        "final_integration_time": current_integration_time,
                        "iterations": iterations,
                        "final_intensity": normalized_intensity
                    }

                    return ApiResponse.ok(
                        data=self._last_result,
                        message=f"自动曝光成功，最终积分时间={current_integration_time}ms"
                    )

                # 二分查找调整
                if normalized_intensity < target_min:
                    # 强度太低，增加积分时间
                    low = current_integration_time
                    current_integration_time = int((low + high) / 2)
                else:
                    # 强度太高，减小积分时间
                    high = current_integration_time
                    current_integration_time = int((low + high) / 2)

                # 确保积分时间在有效范围内
                current_integration_time = max(self._min_time, min(self._max_time, current_integration_time))

                # 如果积分时间变化太小，提前结束
                if abs(current_integration_time - best_time) < 5:
                    logger.debug(f"[AutoExposure] 积分时间变化太小，提前结束")
                    break
            
            # 达到最大迭代次数，返回最佳结果
            if iterations >= max_iterations:
                logger.warning(AutoExposureLog.auto_exposure_timeout(iterations))
                self._current_integration_time = best_time
                self._last_result = {
                    "final_integration_time": best_time,
                    "iterations": iterations,
                    "final_intensity": best_intensity,
                    "timeout": True
                }
                
                return ApiResponse.error(
                    ErrorCode.AUTO_EXPOSURE_TIMEOUT,
                    f"自动曝光超时：{iterations}次迭代内无法收敛，建议使用积分时间={best_time}ms"
                )
            
            # 不应该到达这里
            self._current_integration_time = best_time
            self._last_result = {
                "final_integration_time": best_time,
                "iterations": iterations,
                "final_intensity": best_intensity
            }
            
            return ApiResponse.ok(
                data=self._last_result,
                message=f"自动曝光完成，最终积分时间={best_time}ms"
            )
            
        except Exception as e:
            logger.error(AutoExposureLog.auto_exposure_failed(str(e), ErrorCode.AUTO_EXPOSURE_FAILED))
            return ApiResponse.error(
                ErrorCode.AUTO_EXPOSURE_FAILED,
                f"自动曝光异常：{str(e)}"
            )
    
    def reset(self) -> None:
        """重置自动曝光状态"""
        self._current_integration_time = None
        self._last_result = None
        logger.info("[AutoExposure] 自动曝光已重置")
