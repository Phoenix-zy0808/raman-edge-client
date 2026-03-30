"""
算法推理模块 - 精简重构版

提供光谱分析推理功能，包括峰值检测、平滑滤波、基线校正、谱库匹配等

P11 重构说明:
- 删除了 LocalInference 空壳类
- 算法已拆分到 backend/algorithms/ 模块
- 本文件仅保留 InferenceResult 和 MockInference

P12 新增:
- Transformer 物质识别模型
- 不确定性量化 (MC Dropout)
- 可解释性分析
"""
import logging
import numpy as np
import json
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
import time
from pathlib import Path

from .algorithms.smoothing import smooth_spectrum
from .algorithms.baseline import correct_baseline
from .algorithms.peak_detection import find_peaks, calculate_peak_area
from .algorithms.library_match import match_library, LibraryMatchResult

# P12 新增：导入 AI 模型模块
try:
    from .models.transformer_model import SpectralTransformer, create_transformer_model
    from .models.uncertainty import UncertaintyQuantifier
    from .models.explainability import ExplainabilityAnalyzer
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI 模型模块导入失败：{e}，将使用 MockInference")
    MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


class InferenceResult:
    """推理结果数据类"""

    def __init__(
        self,
        class_name: str = "unknown",
        confidence: float = 0.0,
        peaks: Optional[List[Dict[str, float]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化推理结果

        Args:
            class_name: 分类结果名称
            confidence: 置信度 (0-1)
            peaks: 特征峰列表 [{"position": 520, "intensity": 0.8, "fwhm": 30}, ...]
            metadata: 其他元数据
        """
        self.class_name = class_name
        self.confidence = float(np.clip(confidence, 0.0, 1.0))
        self.peaks = peaks or []
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        """转换为字典格式，方便 JSON 序列化"""
        return {
            "class": self.class_name,
            "confidence": self.confidence,
            "peaks": self.peaks,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def __repr__(self) -> str:
        return f"InferenceResult(class={self.class_name}, confidence={self.confidence:.3f})"


class BaseInference(ABC):
    """推理基类"""

    @abstractmethod
    def predict(self, spectrum: np.ndarray, wavenumbers: np.ndarray) -> InferenceResult:
        """
        对光谱数据进行推理

        Args:
            spectrum: 光谱强度数组
            wavenumbers: 拉曼位移数组

        Returns:
            推理结果
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """
        加载模型

        Args:
            model_path: 模型文件路径

        Returns:
            是否加载成功
        """
        pass

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        pass


class MockInference(BaseInference):
    """
    模拟推理类 - 用于教学演示
    
    提供完整的光谱分析功能：
    - 峰值检测
    - 平滑滤波
    - 基线校正
    - 谱库匹配
    - 峰面积计算
    """

    # 模拟的物质分类
    SIMULATED_CLASSES = [
        "graphite",      # 石墨
        "diamond",       # 金刚石
        "silicon",       # 硅
        "benzene",       # 苯
        "carbon_nanotube",  # 碳纳米管
        "unknown"        # 未知
    ]

    def __init__(self, seed: int = 42):
        """
        初始化模拟推理

        Args:
            seed: 随机种子，确保结果可复现
        """
        self._rng = np.random.default_rng(seed)
        self._model_loaded = False
        self._model_path = ""
        self._log = logging.getLogger(__name__)

    @property
    def is_loaded(self) -> bool:
        return self._model_loaded

    def load_model(self, model_path: str) -> bool:
        """
        加载模型（模拟）

        Args:
            model_path: 模型文件路径

        Returns:
            是否加载成功（总是返回 True）
        """
        self._model_path = model_path
        self._model_loaded = True
        self._log.info(f"[MockInference] 模型加载成功（模拟）：{model_path}")
        return True

    def predict(
        self,
        spectrum: np.ndarray,
        wavenumbers: np.ndarray
    ) -> InferenceResult:
        """
        对光谱数据进行推理（模拟）

        Args:
            spectrum: 光谱强度数组
            wavenumbers: 拉曼位移数组

        Returns:
            推理结果
        """
        if not self._model_loaded:
            return InferenceResult(
                class_name="no_model",
                confidence=0.0,
                metadata={"error": "Model not loaded"}
            )

        # 模拟推理延迟
        time.sleep(0.01)  # 10ms

        # 检测峰值
        detected_peaks = self._detect_peaks(spectrum, wavenumbers)

        # 根据检测到的峰选择分类
        class_name = self._classify_by_peaks(detected_peaks)

        # 生成置信度
        confidence = self._rng.uniform(0.7, 0.99)

        result = InferenceResult(
            class_name=class_name,
            confidence=confidence,
            peaks=detected_peaks,
            metadata={
                "spectrum_mean": float(np.mean(spectrum)),
                "spectrum_std": float(np.std(spectrum)),
                "peak_count": len(detected_peaks),
                "inference_time_ms": 10.0
            }
        )

        return result

    def _detect_peaks(
        self,
        spectrum: np.ndarray,
        wavenumbers: np.ndarray,
        threshold: float = 0.1
    ) -> List[Dict[str, float]]:
        """
        检测特征峰

        Args:
            spectrum: 光谱强度数组
            wavenumbers: 拉曼位移数组
            threshold: 相对阈值 (相对于最大强度)

        Returns:
            特征峰列表
        """
        return find_peaks(
            spectrum,
            wavenumbers,
            threshold=threshold * np.max(spectrum),
            distance=10
        )

    def _classify_by_peaks(self, peaks: List[Dict[str, float]]) -> str:
        """
        根据特征峰位置进行分类

        Args:
            peaks: 特征峰列表

        Returns:
            分类结果
        """
        if not peaks:
            return "unknown"

        # 特征峰匹配规则
        peak_positions = [p["position"] for p in peaks]

        # 硅：520 cm⁻¹
        if any(abs(pos - 520) < 15 for pos in peak_positions):
            return "silicon"

        # 金刚石：1332 cm⁻¹
        if any(abs(pos - 1332) < 15 for pos in peak_positions):
            return "diamond"

        # 石墨/石墨烯：G 峰 ~1580 cm⁻¹, 2D 峰 ~2700 cm⁻¹
        has_g_peak = any(abs(pos - 1580) < 20 for pos in peak_positions)
        has_2d_peak = any(abs(pos - 2700) < 30 for pos in peak_positions)
        if has_g_peak and has_2d_peak:
            return "graphene"
        if has_g_peak:
            return "graphite"

        # 碳纳米管：RBM 模 < 300 cm⁻¹
        if any(pos < 300 for pos in peak_positions):
            return "carbon_nanotube"

        # 苯：992 cm⁻¹
        if any(abs(pos - 992) < 15 for pos in peak_positions):
            return "benzene"

        return self._rng.choice(self.SIMULATED_CLASSES)

    def smooth(
        self,
        spectrum: np.ndarray,
        window_size: int = 5,
        polyorder: int = 2,
        method: str = 'sg'
    ) -> np.ndarray:
        """
        平滑滤波

        Args:
            spectrum: 输入光谱
            window_size: 窗口大小（必须为奇数，3-15）
            polyorder: 多项式阶数（默认 2）
            method: 滤波方法（'sg'=Savitzky-Golay, 'ma'=移动平均）

        Returns:
            平滑后的光谱
        """
        return smooth_spectrum(spectrum, method=method, window_size=window_size, polyorder=polyorder)

    def baseline_correction(
        self,
        spectrum: np.ndarray,
        method: str = 'polyfit'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        基线校正

        Args:
            spectrum: 光谱强度数组
            method: 校正方法 ('polyfit' 多项式拟合，'airpls')

        Returns:
            (corrected_spectrum, baseline) 校正后的光谱和基线
        """
        return correct_baseline(spectrum, method=method)

    def calculate_peak_area(
        self,
        spectrum: np.ndarray,
        wavenumbers: np.ndarray,
        peak_center: float,
        peak_range: float = 20
    ) -> Dict[str, float]:
        """
        计算特征峰面积

        Args:
            spectrum: 光谱强度数组
            wavenumbers: 拉曼位移数组
            peak_center: 峰中心位置 (cm⁻¹)
            peak_range: 积分范围 (±cm⁻¹)

        Returns:
            峰面积计算结果
        """
        return calculate_peak_area(spectrum, wavenumbers, peak_center, peak_range)

    def match_library(
        self,
        spectrum: np.ndarray,
        wavenumbers: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        谱库匹配

        Args:
            spectrum: 光谱强度数组
            wavenumbers: 拉曼位移数组
            top_k: 返回前 K 个匹配结果

        Returns:
            匹配结果列表
        """
        results = match_library(spectrum, wavenumbers, top_k=top_k)
        return [r.to_dict() for r in results]


# 工厂函数
def create_inference(
    use_mock: bool = True,
    seed: int = 42
) -> BaseInference:
    """
    创建推理实例

    Args:
        use_mock: 是否使用模拟推理（推荐）
        seed: 模拟推理的随机种子

    Returns:
        推理实例
    """
    if use_mock:
        return MockInference(seed=seed)
    else:
        # P11 修复：删除 LocalInference 空壳
        # 如需真实 AI 模型，请实现 ONNX 推理类
        logger.warning("LocalInference 已移除，使用 MockInference 进行演示")
        return MockInference(seed=seed)
