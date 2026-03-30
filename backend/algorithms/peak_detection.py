"""
峰值检测算法模块

提供自动寻峰和峰值拟合功能
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from scipy.signal import find_peaks as scipy_find_peaks
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d

from backend.logging_config import get_logger

log = get_logger(__name__)


def gaussian(x, amplitude, center, sigma):
    """高斯函数"""
    return amplitude * np.exp(-(x - center)**2 / (2 * sigma**2))


def lorentzian(x, amplitude, center, gamma):
    """洛伦兹函数"""
    return amplitude * (gamma**2) / ((x - center)**2 + gamma**2)


def voigt(x, amplitude, center, sigma, gamma):
    """Voigt 函数（高斯和洛伦兹的卷积）"""
    from scipy.special import wofz
    z = ((x - center) + 1j * gamma) / (sigma * np.sqrt(2))
    return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2 * np.pi))


# ==================== 原有 API 兼容函数 ====================

def find_peaks_legacy(spectrum: np.ndarray, height: float = None, distance: int = 1) -> Tuple[np.ndarray, dict]:
    """
    寻峰函数（兼容原有 API）- 使用 legacy 后缀避免与 scipy 函数冲突

    参数:
        spectrum: 光谱强度数组
        height: 最小峰高
        distance: 最小峰间距

    返回:
        (peak_indices, properties)
    """
    return scipy_find_peaks(spectrum, height=height, distance=distance)


def calculate_fwhm(spectrum: np.ndarray, peak_idx: int) -> float:
    """
    计算半高宽 (FWHM)
    
    参数:
        spectrum: 光谱强度数组
        peak_idx: 峰值索引位置
    
    返回:
        FWHM 值（数据点数）
    """
    if peak_idx < 0 or peak_idx >= len(spectrum):
        return 0.0
    
    peak_height = spectrum[peak_idx]
    half_height = peak_height / 2
    
    # 向左查找半高点
    left_idx = peak_idx
    for i in range(peak_idx, -1, -1):
        if spectrum[i] <= half_height:
            left_idx = i
            break
    
    # 向右查找半高点
    right_idx = peak_idx
    for i in range(peak_idx, len(spectrum)):
        if spectrum[i] <= half_height:
            right_idx = i
            break
    
    return float(right_idx - left_idx)


def calculate_peak_area(spectrum: np.ndarray, peak_idx: int, window: int = 10) -> float:
    """
    计算峰面积

    参数:
        spectrum: 光谱强度数组
        peak_idx: 峰值索引位置
        window: 积分窗口大小（单侧）

    返回:
        峰面积
    """
    left = max(0, peak_idx - window)
    right = min(len(spectrum), peak_idx + window + 1)

    # 使用梯形积分 (NumPy 2.0+ 使用 trapezoid)
    area = np.trapezoid(spectrum[left:right]) if hasattr(np, 'trapezoid') else np.trapz(spectrum[left:right])
    return float(area)


# ==================== P0 新增函数 ====================

def find_peaks_auto(
    spectrum: np.ndarray,
    sensitivity: float = 0.5,
    min_snr: float = 3.0,
    min_distance: int = 5,
    wavelength_range: tuple = (200, 3200)
) -> List[Dict]:
    """
    自动寻峰算法

    步骤:
    1. 平滑降噪
    2. 计算基线和噪声
    3. 使用 scipy 的 find_peaks 检测
    4. 信噪比过滤
    5. 最小间距过滤

    参数:
        spectrum: 光谱强度数组
        sensitivity: 灵敏度 (0-1), 越高检测到越多峰
        min_snr: 最小信噪比
        min_distance: 最小峰间距 (数据点数)
        wavelength_range: 波长范围 (min, max)

    返回:
        [{"position": float, "intensity": float, "snr": float, "index": int}, ...]
    """
    if len(spectrum) < 10:
        log.warning("光谱数据过短，无法进行峰值检测")
        return []

    # 平滑处理
    smoothed = gaussian_filter1d(spectrum, sigma=2)

    # 计算基线和噪声
    baseline = np.percentile(smoothed, 10)

    # 估计噪声标准差（使用前 50 点或 5% 数据）
    noise_region_size = min(50, len(spectrum) // 20)
    if noise_region_size > 0:
        noise_std = np.std(spectrum[:noise_region_size])
    else:
        noise_std = np.std(spectrum) * 0.1

    if noise_std == 0:
        noise_std = np.max(smoothed) * 0.01  # 避免除零

    # sensitivity 转换为 height 和 threshold 参数
    height_threshold = baseline + sensitivity * (np.max(smoothed) - baseline)
    threshold_value = sensitivity * noise_std * min_snr

    # 使用 scipy 的 find_peaks (只使用 height 和 distance 参数)
    try:
        peak_indices, properties = scipy_find_peaks(
            smoothed,
            height=height_threshold,
            distance=min_distance
        )
    except Exception as e:
        log.error(f"find_peaks 失败：{e}")
        return []

    # 计算信噪比并转换为波长位置
    peaks = []
    wavelength_min, wavelength_max = wavelength_range
    wavelength_range_span = wavelength_max - wavelength_min

    for idx in peak_indices:
        peak_intensity = smoothed[idx] - baseline
        snr = peak_intensity / noise_std if noise_std > 0 else float('inf')

        if snr >= min_snr:
            # 转换为波长位置
            position = wavelength_min + wavelength_range_span * idx / (len(spectrum) - 1)

            peaks.append({
                "position": float(position),
                "intensity": float(smoothed[idx]),
                "snr": float(snr),
                "index": int(idx)
            })

    # 按强度排序
    peaks.sort(key=lambda x: x["intensity"], reverse=True)

    log.info(f"检测到 {len(peaks)} 个峰值")
    return peaks


def fit_peak_auto(
    spectrum: np.ndarray,
    peak_position: float,
    fit_type: str = "gaussian",
    window: int = 20,
    wavelength_range: tuple = (200, 3200)
) -> Dict:
    """
    峰值拟合

    在峰位置附近取窗口数据，进行曲线拟合

    参数:
        spectrum: 光谱强度数组
        peak_position: 峰位置 (cm⁻¹)
        fit_type: 拟合类型 ("gaussian" | "lorentzian" | "voigt")
        window: 拟合窗口大小（数据点数）
        wavelength_range: 波长范围 (min, max)

    返回:
        {"position": float, "intensity": float, "fwhm": float, "area": float, "r_squared": float}
    """
    wavelength_min, wavelength_max = wavelength_range
    wavelength_range_span = wavelength_max - wavelength_min

    # 转换为索引
    peak_idx = int((peak_position - wavelength_min) / wavelength_range_span * (len(spectrum) - 1))

    # 取窗口数据
    left = max(0, peak_idx - window)
    right = min(len(spectrum), peak_idx + window + 1)

    x_data = np.arange(left, right)
    y_data = spectrum[left:right]

    if len(y_data) < 5:
        raise ValueError("窗口数据过短，无法拟合")

    # 初始参数估计
    amplitude = np.max(y_data) - np.min(y_data)
    center = peak_idx - left  # 相对于窗口左边界
    sigma = window / 4  # 初始估计
    gamma = window / 4

    # 拟合函数选择
    if fit_type == "gaussian":
        fit_func = gaussian
        p0 = [amplitude, center, sigma]
    elif fit_type == "lorentzian":
        fit_func = lorentzian
        p0 = [amplitude, center, gamma]
    elif fit_type == "voigt":
        fit_func = voigt
        p0 = [amplitude, center, sigma, gamma]
    else:
        raise ValueError(f"不支持的拟合类型：{fit_type}")

    try:
        # 边界约束
        bounds = (
            [0, left, 0.1] if fit_type != "voigt" else [0, left, 0.1, 0.1],
            [amplitude * 2, right, window] if fit_type != "voigt" else [amplitude * 2, right, window, window]
        )

        popt, pcov = curve_fit(
            fit_func, x_data, y_data,
            p0=p0,
            bounds=bounds,
            maxfev=5000
        )

        # 计算 FWHM 和面积
        if fit_type == "gaussian":
            fwhm = 2 * np.sqrt(2 * np.log(2)) * abs(popt[2])
            area = popt[0] * popt[2] * np.sqrt(2 * np.pi)
        elif fit_type == "lorentzian":
            fwhm = 2 * abs(popt[2])
            area = np.pi * popt[0] * popt[2] / 2
        else:  # voigt
            fwhm = 0.5346 * 2 * abs(popt[3]) + np.sqrt(0.2166 * (2 * abs(popt[3]))**2 + (2 * np.sqrt(2 * np.log(2)) * abs(popt[2]))**2)
            area = popt[0] * fwhm * np.sqrt(np.pi / 2)

        # 计算 R²
        y_pred = fit_func(x_data, *popt)
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # 转换为波长位置
        position_cm = wavelength_min + wavelength_range_span * (left + popt[1]) / (len(spectrum) - 1)

        result = {
            "position": float(position_cm),
            "intensity": float(popt[0]),
            "fwhm": float(fwhm),
            "area": float(area),
            "r_squared": float(r_squared)
        }

        log.info(f"峰值拟合成功：position={position_cm:.2f}, R²={r_squared:.4f}")
        return result

    except Exception as e:
        log.error(f"峰值拟合失败：{e}")
        raise ValueError(f"拟合失败：{e}")


def calculate_peak_statistics(peaks: List[Dict]) -> Dict:
    """
    计算峰值统计信息

    参数:
        peaks: 峰值列表

    返回:
        {"count": int, "max_position": float, "max_intensity": float, "avg_snr": float}
    """
    # 修复：使用 len() 检查空数组，避免 numpy 数组的布尔值歧义
    if peaks is None or len(peaks) == 0:
        return {
            "count": 0,
            "max_position": None,
            "max_intensity": None,
            "avg_snr": None
        }

    return {
        "count": len(peaks),
        "max_position": max(peaks, key=lambda x: x["intensity"])["position"],
        "max_intensity": max(peaks, key=lambda x: x["intensity"])["intensity"],
        "avg_snr": sum(p["snr"] for p in peaks) / len(peaks)
    }
