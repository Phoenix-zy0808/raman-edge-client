"""
平滑滤波算法模块

提供 Savitzky-Golay 和移动平均平滑算法
"""
import numpy as np
from typing import Literal
import logging

logger = logging.getLogger(__name__)

try:
    from scipy.signal import savgol_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("scipy 未安装，Savitzky-Golay 平滑将不可用")


def savgol_smooth(
    spectrum: np.ndarray,
    window_size: int = 5,
    polyorder: int = 2
) -> np.ndarray:
    """
    Savitzky-Golay 平滑滤波

    Args:
        spectrum: 输入光谱数据
        window_size: 滑动窗口大小 (必须为奇数，范围 3-15)
        polyorder: 多项式拟合阶数

    Returns:
        平滑后的光谱数据
    """
    # 参数验证
    if window_size % 2 == 0:
        window_size += 1
    window_size = max(3, min(window_size, 15))
    
    # 确保窗口不超过数据长度
    if window_size >= len(spectrum):
        window_size = len(spectrum) - 1 if len(spectrum) % 2 == 0 else len(spectrum) - 2
        window_size = max(3, window_size)
    
    if polyorder >= window_size:
        polyorder = window_size - 1
    
    if not HAS_SCIPY:
        logger.warning("scipy 不可用，降级为移动平均平滑")
        return moving_average_smooth(spectrum, window_size)
    
    try:
        smoothed = savgol_filter(spectrum, window_size, polyorder, mode='mirror')
        logger.debug(f"Savitzky-Golay 平滑完成：window={window_size}, order={polyorder}")
        return smoothed
    except Exception as e:
        logger.error(f"Savitzky-Golay 平滑失败：{e}，降级为移动平均")
        return moving_average_smooth(spectrum, window_size)


def moving_average_smooth(
    spectrum: np.ndarray,
    window_size: int = 5
) -> np.ndarray:
    """
    移动平均平滑

    Args:
        spectrum: 输入光谱数据
        window_size: 滑动窗口大小

    Returns:
        平滑后的光谱数据
    """
    # 参数验证
    if window_size % 2 == 0:
        window_size += 1
    window_size = max(3, min(window_size, len(spectrum)))
    
    kernel = np.ones(window_size) / window_size
    smoothed = np.convolve(spectrum, kernel, mode='same')
    
    logger.debug(f"移动平均平滑完成：window={window_size}")
    return smoothed


def smooth_spectrum(
    spectrum: np.ndarray,
    method: Literal['sg', 'ma'] = 'sg',
    window_size: int = 5,
    polyorder: int = 2
) -> np.ndarray:
    """
    平滑滤波统一接口

    Args:
        spectrum: 输入光谱数据
        method: 平滑方法 ('sg'=Savitzky-Golay, 'ma'=移动平均)
        window_size: 窗口大小
        polyorder: 多项式阶数 (仅 sg 方法使用)

    Returns:
        平滑后的光谱数据
    """
    if method == 'sg':
        return savgol_smooth(spectrum, window_size, polyorder)
    elif method == 'ma':
        return moving_average_smooth(spectrum, window_size)
    else:
        logger.warning(f"未知平滑方法：{method}，使用 Savitzky-Golay")
        return savgol_smooth(spectrum, window_size, polyorder)
