"""
基线校正算法模块

提供多项式拟合基线校正和 airPLS 算法
"""
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def polyfit_baseline(
    spectrum: np.ndarray,
    degree: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    多项式拟合基线校正

    Args:
        spectrum: 输入光谱数据
        degree: 多项式拟合阶数

    Returns:
        (corrected_spectrum, baseline) 校正后的光谱和基线
    """
    x = np.arange(len(spectrum))
    
    try:
        coeffs = np.polyfit(x, spectrum, deg=degree)
        baseline = np.polyval(coeffs, x)
        corrected = spectrum - baseline
        
        # 归一化到非负
        min_val = np.min(corrected)
        if min_val < 0:
            corrected = corrected - min_val
        
        logger.debug(f"多项式基线校正完成：degree={degree}")
        return corrected, baseline
        
    except Exception as e:
        logger.error(f"多项式基线校正失败：{e}，返回原始光谱")
        return spectrum, np.zeros_like(spectrum)


def airpls_baseline(
    spectrum: np.ndarray,
    max_iter: int = 100,
    threshold: float = 1e-4,
    lam: float = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    airPLS (adaptive iteratively reweighted Penalized Least Squares) 基线校正

    自适应迭代加权惩罚最小二乘法基线校正算法

    Args:
        spectrum: 输入光谱数据
        max_iter: 最大迭代次数
        threshold: 收敛阈值
        lam: 平滑参数

    Returns:
        (corrected_spectrum, baseline) 校正后的光谱和基线
    """
    n = len(spectrum)
    
    try:
        # 初始化权重
        w = np.ones(n)
        baseline = np.zeros(n)
        
        for iteration in range(max_iter):
            # 加权最小二乘拟合
            W = np.diag(w)
            
            # 简化实现：使用加权移动平均近似
            baseline = np.convolve(spectrum * w, np.ones(51)/51, mode='same')
            
            # 更新权重：信号点权重小，基线点权重大
            diff = spectrum - baseline
            w = np.exp(diff / (np.std(diff) + 1e-10))
            
            # 检查收敛
            if np.sum(np.abs(baseline - np.convolve(spectrum * w, np.ones(51)/51, mode='same'))) < threshold:
                break
        
        corrected = spectrum - baseline
        
        # 归一化到非负
        min_val = np.min(corrected)
        if min_val < 0:
            corrected = corrected - min_val
        
        logger.debug(f"airPLS 基线校正完成：iter={iteration+1}")
        return corrected, baseline
        
    except Exception as e:
        logger.error(f"airPLS 基线校正失败：{e}，使用多项式拟合")
        return polyfit_baseline(spectrum)


def correct_baseline(
    spectrum: np.ndarray,
    method: str = 'polyfit',
    **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    """
    基线校正统一接口

    Args:
        spectrum: 输入光谱数据
        method: 校正方法 ('polyfit'=多项式拟合，'airpls'=airPLS)
        **kwargs: 方法相关参数

    Returns:
        (corrected_spectrum, baseline) 校正后的光谱和基线
    """
    if method == 'polyfit':
        degree = kwargs.get('degree', 3)
        return polyfit_baseline(spectrum, degree)
    elif method == 'airpls':
        max_iter = kwargs.get('max_iter', 100)
        return airpls_baseline(spectrum, max_iter)
    else:
        logger.warning(f"未知基线校正方法：{method}，使用多项式拟合")
        return polyfit_baseline(spectrum)
