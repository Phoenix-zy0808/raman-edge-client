"""
拉曼光谱算法模块

包含平滑滤波、基线校正、峰值检测、相似度计算等算法
P11 新增：波长校准、强度校准、自动曝光
P0 新增：预处理工具集、峰值自动识别、差谱运算
"""
from .smoothing import savgol_smooth, moving_average_smooth
from .baseline import polyfit_baseline, airpls_baseline
from .peak_detection import find_peaks_legacy as find_peaks, calculate_fwhm, calculate_peak_area
from .similarity import cosine_similarity, correlation_coefficient
from .library_match import match_library, LibraryMatchResult
from .wavelength_calibration import WavelengthCalibrator, WavelengthCalibrationResult
from .intensity_calibration import IntensityCalibrator, IntensityCalibrationResult
from .auto_exposure import AutoExposure

# P0 新增导入
from .peak_detection import find_peaks_auto, fit_peak_auto, calculate_peak_statistics
from .preprocessing import (
    normalize_spectrum,
    smooth_spectrum,
    derivative_spectrum,
    snv_transform,
    iterative_polynomial_baseline,
    multiplicative_scatter_correction,
    preprocess_spectrum,
    # P0-4 差谱运算
    subtract_spectra,
    scale_spectrum,
    add_spectra
)

__all__ = [
    # 原有算法
    'savgol_smooth',
    'moving_average_smooth',
    'polyfit_baseline',
    'airpls_baseline',
    'find_peaks',
    'calculate_fwhm',
    'calculate_peak_area',
    'cosine_similarity',
    'correlation_coefficient',
    'match_library',
    'LibraryMatchResult',
    # P11 新增校准算法
    'WavelengthCalibrator',
    'WavelengthCalibrationResult',
    'IntensityCalibrator',
    'IntensityCalibrationResult',
    'AutoExposure',
    # P0 新增
    'find_peaks_auto',
    'fit_peak_auto',
    'calculate_peak_statistics',
    'normalize_spectrum',
    'smooth_spectrum',
    'derivative_spectrum',
    'snv_transform',
    'iterative_polynomial_baseline',
    'multiplicative_scatter_correction',
    'preprocess_spectrum',
    # P0-4 差谱运算
    'subtract_spectra',
    'scale_spectrum',
    'add_spectra',
]
