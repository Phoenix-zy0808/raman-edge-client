"""
谱图预处理算法模块

提供归一化、平滑、求导、基线校正等预处理功能
"""

import numpy as np
from typing import Tuple, Optional
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d

from backend.logging_config import get_logger

log = get_logger(__name__)


def normalize_spectrum(
    spectrum: np.ndarray,
    method: str = "minmax",
    target_max: float = 1.0
) -> np.ndarray:
    """
    光谱归一化

    参数:
        spectrum: 光谱强度数组
        method: "minmax" | "area" | "vector"
        target_max: 目标最大值（minmax 法）

    返回:
        归一化后的光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)

    if method == "minmax":
        min_val = np.min(spectrum)
        max_val = np.max(spectrum)
        if max_val - min_val == 0:
            return np.zeros_like(spectrum)
        normalized = (spectrum - min_val) / (max_val - min_val) * target_max

    elif method == "area":
        # 面积归一化（积分归一化）
        # 使用 scipy.integrate.trapezoid 替代 np.trapz (NumPy 2.x 已移除)
        from scipy.integrate import trapezoid
        area = trapezoid(spectrum)
        if area == 0:
            return np.zeros_like(spectrum)
        normalized = spectrum / area

    elif method == "vector":
        # 矢量归一化
        norm = np.linalg.norm(spectrum)
        if norm == 0:
            return np.zeros_like(spectrum)
        normalized = spectrum / norm

    else:
        raise ValueError(f"不支持的归一化方法：{method}")

    log.debug(f"光谱归一化完成：method={method}")
    return normalized


def smooth_spectrum(
    spectrum: np.ndarray,
    method: str = "savitzky_golay",
    window_size: int = 5,
    poly_order: int = 2,
    sigma: float = 1.0
) -> np.ndarray:
    """
    光谱平滑

    参数:
        spectrum: 光谱强度数组
        method: "savitzky_golay" | "gaussian"
        window_size: 窗口大小（奇数，SG 法）
        poly_order: 多项式阶数（SG 法）
        sigma: 高斯标准差（高斯法）

    返回:
        平滑后的光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)

    if method == "savitzky_golay":
        # 确保窗口大小为奇数
        if window_size % 2 == 0:
            window_size += 1
        
        # 窗口大小不能超过数据长度
        window_size = min(window_size, len(spectrum))
        if window_size % 2 == 0:
            window_size -= 1
        
        # poly_order 不能超过 window_size - 1
        poly_order = min(poly_order, window_size - 1)
        
        if window_size < 3 or poly_order < 1:
            log.warning("SG 平滑参数无效，返回原始数据")
            return spectrum
        
        smoothed = savgol_filter(spectrum, window_size, poly_order)

    elif method == "gaussian":
        smoothed = gaussian_filter1d(spectrum, sigma=sigma)

    else:
        raise ValueError(f"不支持的平滑方法：{method}")

    log.debug(f"光谱平滑完成：method={method}, window_size={window_size}")
    return smoothed


def derivative_spectrum(
    spectrum: np.ndarray,
    order: int = 1,
    smooth_window: int = 5,
    delta_x: float = 1.0
) -> np.ndarray:
    """
    光谱求导

    参数:
        spectrum: 光谱强度数组
        order: 1 | 2（一阶或二阶导数）
        smooth_window: 平滑窗口大小
        delta_x: 自变量间隔

    返回:
        导数光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)

    # 先平滑
    smoothed = smooth_spectrum(spectrum, method="savitzky_golay", 
                               window_size=smooth_window, poly_order=2)

    if order == 1:
        # 一阶导数（中心差分）
        derivative = np.gradient(smoothed, delta_x)
    elif order == 2:
        # 二阶导数
        first_derivative = np.gradient(smoothed, delta_x)
        derivative = np.gradient(first_derivative, delta_x)
    else:
        raise ValueError(f"不支持的导数阶数：{order}")

    log.debug(f"光谱求导完成：order={order}")
    return derivative


def snv_transform(spectrum: np.ndarray) -> np.ndarray:
    """
    标准正态变量变换 (Standard Normal Variate, SNV)

    用于消除固体样品颗粒大小和表面散射的影响

    参数:
        spectrum: 光谱强度数组

    返回:
        SNV 变换后的光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)
    
    mean = np.mean(spectrum)
    std = np.std(spectrum)
    
    if std == 0:
        return np.zeros_like(spectrum)
    
    snv = (spectrum - mean) / std
    
    log.debug("SNV 变换完成")
    return snv


def iterative_polynomial_baseline(
    spectrum: np.ndarray,
    order: int = 5,
    iterations: int = 10,
    threshold: float = 0.01
) -> Tuple[np.ndarray, np.ndarray]:
    """
    迭代多项式拟合基线校正

    算法步骤:
    1. 用多项式拟合原始光谱
    2. 找出拟合值大于原始值的点（可能是峰）
    3. 将这些点权重降低
    4. 重复 1-3 直到收敛

    参数:
        spectrum: 光谱强度数组
        order: 多项式阶数
        iterations: 迭代次数
        threshold: 收敛阈值

    返回:
        (baseline, corrected) 基线和校正后光谱
    """
    x = np.arange(len(spectrum))
    weights = np.ones(len(spectrum))
    
    baseline = np.zeros_like(spectrum)
    
    for i in range(iterations):
        # 加权多项式拟合
        try:
            coeffs = np.polyfit(x, spectrum, order, w=weights)
            baseline = np.polyval(coeffs, x)
            
            # 更新权重：拟合值 > 原始值的点权重降低
            residual = spectrum - baseline
            weights = 1 / (1 + np.exp(100 * residual / (threshold * np.max(spectrum))))
        except Exception as e:
            log.warning(f"基线拟合迭代 {i} 失败：{e}")
            break
    
    corrected = spectrum - baseline
    
    log.info(f"迭代多项式基线校正完成：order={order}, iterations={iterations}")
    return baseline, corrected


def airpls_baseline(
    spectrum: np.ndarray,
    lambda_param: float = 100,
    max_iter: int = 20,
    tol: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray]:
    """
    AIRPLS 基线校正 (Adaptive Iteratively Reweighted Penalized Least Squares)

    更先进的基线校正算法，适合强荧光背景

    参数:
        spectrum: 光谱强度数组
        lambda_param: 平滑参数
        max_iter: 最大迭代次数
        tol: 收敛容差

    返回:
        (baseline, corrected) 基线和校正后光谱
    """
    n = len(spectrum)
    
    # 初始化
    baseline = np.zeros(n)
    w = np.ones(n)
    D = np.diff(np.eye(n), n=2, axis=0)  # 二阶差分矩阵
    
    for iteration in range(max_iter):
        # 构建加权最小二乘问题
        W = np.diag(w)
        
        # 求解 (W + lambda * D'D)z = Wy
        try:
            A = W + lambda_param * (D.T @ D)
            b = w * spectrum
            baseline = np.linalg.solve(A, b)
        except Exception as e:
            log.warning(f"AIRPLS 迭代 {iteration} 失败：{e}")
            break
        
        # 更新权重
        residual = spectrum - baseline
        w_new = 1 / (1 + np.exp(-residual / (tol * np.std(spectrum))))
        
        # 检查收敛
        if np.max(np.abs(w_new - w)) < tol:
            log.info(f"AIRPLS 基线校正收敛于迭代 {iteration}")
            break
        
        w = w_new
    
    corrected = spectrum - baseline
    
    log.info(f"AIRPLS 基线校正完成：lambda={lambda_param}, iterations={iteration+1}")
    return baseline, corrected


def multiplicative_scatter_correction(
    spectrum: np.ndarray,
    reference: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    多元散射校正 (Multiplicative Scatter Correction, MSC)

    用于消除散射效应

    参数:
        spectrum: 光谱强度数组
        reference: 参考光谱（如平均光谱），默认为输入光谱的均值

    返回:
        MSC 校正后的光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)
    
    if reference is None:
        reference = np.mean(spectrum)
    
    # 线性拟合：spectrum = a * reference + b
    A = np.vstack([reference, np.ones(len(reference))]).T
    try:
        m, c = np.linalg.lstsq(A, spectrum, rcond=None)[0]
        
        # 校正
        corrected = (spectrum - c) / m
        
        log.debug("MSC 校正完成")
        return corrected
    except Exception as e:
        log.error(f"MSC 校正失败：{e}")
        return spectrum


def preprocess_spectrum(
    spectrum: np.ndarray,
    steps: list = None
) -> np.ndarray:
    """
    组合预处理流程

    参数:
        spectrum: 光谱强度数组
        steps: 预处理步骤列表，每项为 (method, params)
               例如：[("smooth", {"window_size": 5}), ("baseline", {"order": 5})]

    返回:
        预处理后的光谱
    """
    if steps is None:
        # 默认预处理流程
        steps = [
            ("smooth", {"method": "savitzky_golay", "window_size": 7, "poly_order": 2}),
            ("baseline", {"order": 5, "iterations": 10}),
            ("normalize", {"method": "minmax"})
        ]
    
    result = spectrum.copy()

    for method, params in steps:
        if method == "smooth":
            result = smooth_spectrum(result, **params)
        elif method == "baseline":
            _, result = iterative_polynomial_baseline(result, **params)
        elif method == "normalize":
            result = normalize_spectrum(result, **params)
        elif method == "snv":
            result = snv_transform(result)
        elif method == "derivative":
            result = derivative_spectrum(result, **params)
        elif method == "msc":
            result = multiplicative_scatter_correction(result, **params)
        else:
            log.warning(f"未知的预处理方法：{method}")

    log.info(f"组合预处理完成：{len(steps)} 个步骤")
    return result


# ==================== P0-4 差谱运算 ====================

def subtract_spectra(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray,
    coefficient: float = 1.0
) -> np.ndarray:
    """
    差谱运算 - 两个光谱相减
    
    公式：difference = spectrum1 - coefficient * spectrum2
    
    参数:
        spectrum1: 参考光谱（被减数）
        spectrum2: 待减光谱（减数）
        coefficient: 减数系数，默认为 1.0
        
    返回:
        差谱结果
        
    异常:
        ValueError: 当两个光谱维度不匹配时
    """
    spectrum1 = np.asarray(spectrum1, dtype=float)
    spectrum2 = np.asarray(spectrum2, dtype=float)
    
    if spectrum1.shape != spectrum2.shape:
        raise ValueError(
            f"光谱维度不匹配：{spectrum1.shape} vs {spectrum2.shape}"
        )
    
    difference = spectrum1 - coefficient * spectrum2
    
    log.info(f"差谱运算完成：系数={coefficient}, 范围=[{difference.min():.2f}, {difference.max():.2f}]")
    
    return difference


def scale_spectrum(
    spectrum: np.ndarray,
    coefficient: float = 1.0,
    offset: float = 0.0
) -> np.ndarray:
    """
    光谱缩放和平移
    
    公式：result = spectrum * coefficient + offset
    
    参数:
        spectrum: 输入光谱
        coefficient: 缩放系数
        offset: 平移偏移量
        
    返回:
        缩放和平移后的光谱
    """
    spectrum = np.asarray(spectrum, dtype=float)
    result = spectrum * coefficient + offset
    
    log.info(f"光谱缩放完成：系数={coefficient}, 偏移={offset}")
    
    return result


def add_spectra(
    spectrum1: np.ndarray,
    spectrum2: np.ndarray,
    coefficient1: float = 1.0,
    coefficient2: float = 1.0
) -> np.ndarray:
    """
    光谱相加运算
    
    公式：result = coefficient1 * spectrum1 + coefficient2 * spectrum2
    
    参数:
        spectrum1: 光谱 1
        spectrum2: 光谱 2
        coefficient1: 光谱 1 的系数
        coefficient2: 光谱 2 的系数
        
    返回:
        相加结果
        
    异常:
        ValueError: 当两个光谱维度不匹配时
    """
    spectrum1 = np.asarray(spectrum1, dtype=float)
    spectrum2 = np.asarray(spectrum2, dtype=float)
    
    if spectrum1.shape != spectrum2.shape:
        raise ValueError(
            f"光谱维度不匹配：{spectrum1.shape} vs {spectrum2.shape}"
        )
    
    result = coefficient1 * spectrum1 + coefficient2 * spectrum2
    
    log.info(f"光谱相加完成：系数 1={coefficient1}, 系数 2={coefficient2}")
    
    return result
