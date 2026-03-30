"""
算法模块单元测试

测试范围:
1. 平滑滤波算法 (smoothing.py)
2. 基线校正算法 (baseline.py)
3. 峰值检测算法 (peak_detection.py)
4. 相似度计算算法 (similarity.py)
5. 谱库匹配算法 (library_match.py)
"""
import numpy as np
import pytest
from pathlib import Path

from backend.algorithms.smoothing import savgol_smooth, moving_average_smooth, smooth_spectrum
from backend.algorithms.baseline import polyfit_baseline, airpls_baseline, correct_baseline
from backend.algorithms.peak_detection import find_peaks_auto, fit_peak_auto, calculate_fwhm, calculate_peak_area
from backend.algorithms.similarity import cosine_similarity, correlation_coefficient, calculate_similarity
from backend.algorithms.library_match import match_library, SpectralLibrary


# ==================== 测试数据生成 ====================
def generate_test_spectrum(n_points=1024, noise_level=0.01):
    """生成测试光谱数据"""
    x = np.linspace(200, 3200, n_points)
    spectrum = np.zeros(n_points)

    # 添加硅峰 (520 cm⁻¹)
    spectrum += np.exp(-((x - 520) ** 2) / (2 * 10 ** 2))

    # 添加 G 峰 (1580 cm⁻¹)
    spectrum += 0.5 * np.exp(-((x - 1580) ** 2) / (2 * 15 ** 2))

    # 添加 2D 峰 (2700 cm⁻¹)
    spectrum += 0.3 * np.exp(-((x - 2700) ** 2) / (2 * 20 ** 2))

    # 添加噪声
    spectrum += np.random.normal(0, noise_level, n_points)

    # 添加基线漂移
    baseline = 0.1 * (x / 3200) ** 2
    spectrum += baseline

    return spectrum, x


# ==================== 平滑滤波测试 ====================
class TestSmoothing:
    """平滑滤波算法测试"""

    def test_savgol_smooth_basic(self):
        """测试 Savitzky-Golay 平滑基本功能"""
        spectrum, _ = generate_test_spectrum()
        smoothed = savgol_smooth(spectrum, window_size=5, polyorder=2)

        assert len(smoothed) == len(spectrum)
        assert not np.isnan(smoothed).any()
        assert not np.isinf(smoothed).any()
        assert np.std(smoothed) < np.std(spectrum)

    def test_moving_average_smooth(self):
        """测试移动平均平滑"""
        spectrum, _ = generate_test_spectrum()
        smoothed = moving_average_smooth(spectrum, window_size=5)

        assert len(smoothed) == len(spectrum)
        assert not np.isnan(smoothed).any()

    def test_smooth_spectrum_invalid_window(self):
        """测试平滑窗口参数自动修正"""
        spectrum, _ = generate_test_spectrum()
        smoothed = savgol_smooth(spectrum, window_size=4)
        assert len(smoothed) == len(spectrum)


# ==================== 基线校正测试 ====================
class TestBaseline:
    """基线校正算法测试"""

    def test_polyfit_baseline_basic(self):
        """测试多项式拟合基线校正"""
        spectrum, _ = generate_test_spectrum()
        corrected, baseline = polyfit_baseline(spectrum, degree=3)

        assert len(corrected) == len(spectrum)
        assert len(baseline) == len(spectrum)
        assert not np.isnan(corrected).any()
        assert not np.isnan(baseline).any()
        assert np.sum(corrected < 0) < len(corrected) * 0.1

    def test_airpls_baseline(self):
        """测试 airPLS 基线校正"""
        spectrum, _ = generate_test_spectrum()
        corrected, baseline = airpls_baseline(spectrum, max_iter=50)

        assert len(corrected) == len(spectrum)
        assert len(baseline) == len(spectrum)

    def test_correct_baseline_invalid_method(self):
        """测试基线校正使用未知方法时的降级处理"""
        spectrum, _ = generate_test_spectrum()
        corrected, baseline = correct_baseline(spectrum, method='unknown_method')
        assert len(corrected) == len(spectrum)


# ==================== 峰值检测测试 ====================
class TestPeakDetection:
    """峰值检测算法测试"""

    def test_find_peaks_basic(self):
        """测试基本峰值检测"""
        spectrum, wavenumbers = generate_test_spectrum()
        peaks = find_peaks_auto(spectrum, sensitivity=0.3, min_snr=3.0)

        assert isinstance(peaks, list)
        assert len(peaks) > 0

        for peak in peaks:
            assert "position" in peak
            assert "intensity" in peak
            assert 200 <= peak["position"] <= 3200

    def test_find_peaks_with_known_positions(self):
        """测试已知峰位置的检测"""
        spectrum, wavenumbers = generate_test_spectrum()
        peaks = find_peaks_auto(spectrum, sensitivity=0.2, min_snr=2.0)

        positions = [p["position"] for p in peaks]
        assert any(abs(pos - 520) < 50 for pos in positions)

    def test_calculate_peak_area(self):
        """测试峰面积计算"""
        spectrum, wavenumbers = generate_test_spectrum()
        peaks = find_peaks_auto(spectrum, sensitivity=0.3)
        assert len(peaks) > 0, "未检测到峰值"

        peak_idx = peaks[0]["index"]
        result = calculate_peak_area(spectrum, peak_idx, window=20)

        assert isinstance(result, float)
        assert result > 0


# ==================== 相似度计算测试 ====================
class TestSimilarity:
    """相似度计算算法测试"""

    def test_cosine_similarity_identical(self):
        """测试相同光谱的余弦相似度"""
        spectrum = np.random.rand(1024)
        similarity = cosine_similarity(spectrum, spectrum)
        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        """测试正交向量的余弦相似度"""
        spectrum1 = np.zeros(1024)
        spectrum1[0:512] = 1
        spectrum2 = np.zeros(1024)
        spectrum2[512:] = 1

        similarity = cosine_similarity(spectrum1, spectrum2)
        assert abs(similarity) < 1e-6

    def test_correlation_coefficient(self):
        """测试相关系数"""
        x = np.linspace(0, 10, 100)
        y1 = np.sin(x)
        y2 = np.sin(x + 0.1)

        corr = correlation_coefficient(y1, y2)
        assert corr > 0.9

    def test_calculate_similarity_methods(self):
        """测试不同相似度计算方法"""
        spectrum1 = np.random.rand(100)
        spectrum2 = np.random.rand(100)
        methods = ['cosine', 'correlation', 'euclidean', 'sam']

        for method in methods:
            sim = calculate_similarity(spectrum1, spectrum2, method=method)
            assert isinstance(sim, float)


# ==================== 谱库匹配测试 ====================
class TestLibraryMatch:
    """谱库匹配算法测试"""

    def test_spectral_library_load(self):
        """测试光谱库加载"""
        library_path = Path(__file__).parent.parent / "backend" / "library"
        library = SpectralLibrary(str(library_path))

        assert len(library.index) > 0
        spectrum_data = library.load_spectrum("silicon")
        assert spectrum_data is not None
        assert "peaks" in spectrum_data

    def test_match_library(self):
        """测试谱库匹配功能"""
        x = np.linspace(200, 3200, 1024)
        spectrum = np.exp(-((x - 520) ** 2) / (2 * 8 ** 2))
        spectrum += np.random.normal(0, 0.01, 1024)
        spectrum = np.maximum(spectrum, 0)

        library_path = Path(__file__).parent.parent / "backend" / "library"
        results = match_library(spectrum, x, str(library_path), top_k=3)

        assert len(results) > 0

        for result in results:
            has_id = hasattr(result, 'substance_id') or ('id' in result if isinstance(result, dict) else False)
            assert has_id
            has_sim = hasattr(result, 'similarity') or ('similarity' in result if isinstance(result, dict) else False)
            assert has_sim
