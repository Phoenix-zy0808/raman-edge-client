"""
算法模块测试

测试范围:
1. 平滑滤波算法 (smoothing.py)
2. 基线校正算法 (baseline.py)
3. 峰值检测算法 (peak_detection.py)
4. 相似度计算算法 (similarity.py)
5. 谱库匹配算法 (library_match.py)
"""
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.algorithms.smoothing import savgol_smooth, moving_average_smooth, smooth_spectrum
from backend.algorithms.baseline import polyfit_baseline, airpls_baseline, correct_baseline
from backend.algorithms.peak_detection import find_peaks_auto, fit_peak_auto, calculate_fwhm, calculate_peak_area
from backend.algorithms.similarity import cosine_similarity, correlation_coefficient, calculate_similarity
from backend.algorithms.library_match import match_library, SpectralLibrary


# ==================== 测试数据生成 ====================
def generate_test_spectrum(n_points=1024, noise_level=0.01):
    """生成测试光谱数据"""
    x = np.linspace(200, 3200, n_points)
    # 生成一个模拟光谱，包含几个高斯峰
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
        
        # 测试平滑
        smoothed = savgol_smooth(spectrum, window_size=5, polyorder=2)
        
        assert len(smoothed) == len(spectrum)
        assert not np.isnan(smoothed).any()
        assert not np.isinf(smoothed).any()
        
        # 平滑后噪声应该减小
        assert np.std(smoothed) < np.std(spectrum)
        
        print("✓ Savitzky-Golay 平滑基本功能测试通过")
    
    def test_moving_average_smooth(self):
        """测试移动平均平滑"""
        spectrum, _ = generate_test_spectrum()
        
        smoothed = moving_average_smooth(spectrum, window_size=5)
        
        assert len(smoothed) == len(spectrum)
        assert not np.isnan(smoothed).any()
        
        print("✓ 移动平均平滑测试通过")
    
    def test_smooth_spectrum_invalid_window(self):
        """测试平滑窗口参数自动修正"""
        spectrum, _ = generate_test_spectrum()
        
        # 偶数窗口应自动转为奇数
        smoothed = savgol_smooth(spectrum, window_size=4)
        assert len(smoothed) == len(spectrum)
        
        print("✓ 平滑窗口参数修正测试通过")


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
        
        # 校正后的数据应该 mostly 非负
        assert np.sum(corrected < 0) < len(corrected) * 0.1
        
        print("✓ 多项式拟合基线校正测试通过")
    
    def test_airpls_baseline(self):
        """测试 airPLS 基线校正"""
        spectrum, _ = generate_test_spectrum()
        
        corrected, baseline = airpls_baseline(spectrum, max_iter=50)
        
        assert len(corrected) == len(spectrum)
        assert len(baseline) == len(spectrum)
        
        print("✓ airPLS 基线校正测试通过")
    
    def test_correct_baseline_invalid_method(self):
        """测试基线校正使用未知方法时的降级处理"""
        spectrum, _ = generate_test_spectrum()
        
        # 使用未知方法应降级为多项式拟合
        corrected, baseline = correct_baseline(spectrum, method='unknown_method')
        
        assert len(corrected) == len(spectrum)
        
        print("✓ 基线校正降级处理测试通过")


# ==================== 峰值检测测试 ====================
class TestPeakDetection:
    """峰值检测算法测试"""

    def test_find_peaks_basic(self):
        """测试基本峰值检测"""
        spectrum, wavenumbers = generate_test_spectrum()

        # 使用实际 API: find_peaks_auto 返回峰值列表
        from backend.algorithms.peak_detection import find_peaks_auto
        peaks = find_peaks_auto(spectrum, sensitivity=0.3, min_snr=3.0)

        assert isinstance(peaks, list)
        assert len(peaks) > 0

        # 检查峰位置
        for peak in peaks:
            assert "position" in peak
            assert "intensity" in peak
            assert 200 <= peak["position"] <= 3200

        print(f"✓ 峰值检测测试通过，检测到 {len(peaks)} 个峰")

    def test_find_peaks_with_known_positions(self):
        """测试已知峰位置的检测"""
        spectrum, wavenumbers = generate_test_spectrum()

        from backend.algorithms.peak_detection import find_peaks_auto
        peaks = find_peaks_auto(spectrum, sensitivity=0.2, min_snr=2.0)

        # 应该能检测到 520 cm⁻¹ 的主峰
        positions = [p["position"] for p in peaks]
        assert any(abs(pos - 520) < 50 for pos in positions)

        print("✓ 已知峰位置检测测试通过")

    def test_calculate_peak_area(self):
        """测试峰面积计算"""
        spectrum, wavenumbers = generate_test_spectrum()

        from backend.algorithms.peak_detection import find_peaks_auto, calculate_peak_area

        # 先找到峰值索引
        peaks = find_peaks_auto(spectrum, sensitivity=0.3)
        assert len(peaks) > 0, "未检测到峰值"

        # 使用最强峰的索引计算面积
        peak_idx = peaks[0]["index"]
        result = calculate_peak_area(spectrum, peak_idx, window=20)

        assert isinstance(result, float)
        assert result > 0

        print(f"✓ 峰面积计算测试通过，area={result:.2f}")


# ==================== 相似度计算测试 ====================
class TestSimilarity:
    """相似度计算算法测试"""
    
    def test_cosine_similarity_identical(self):
        """测试相同光谱的余弦相似度"""
        spectrum = np.random.rand(1024)
        
        similarity = cosine_similarity(spectrum, spectrum)
        
        # 相同向量的余弦相似度应为 1
        assert abs(similarity - 1.0) < 1e-6
        
        print("✓ 相同光谱余弦相似度测试通过")
    
    def test_cosine_similarity_orthogonal(self):
        """测试正交向量的余弦相似度"""
        spectrum1 = np.zeros(1024)
        spectrum1[0:512] = 1
        spectrum2 = np.zeros(1024)
        spectrum2[512:] = 1
        
        similarity = cosine_similarity(spectrum1, spectrum2)
        
        # 正交向量的余弦相似度应为 0
        assert abs(similarity) < 1e-6
        
        print("✓ 正交向量余弦相似度测试通过")
    
    def test_correlation_coefficient(self):
        """测试相关系数"""
        x = np.linspace(0, 10, 100)
        y1 = np.sin(x)
        y2 = np.sin(x + 0.1)  # 稍有相移
        
        corr = correlation_coefficient(y1, y2)
        
        # 应该有较高的正相关
        assert corr > 0.9
        
        print(f"✓ 相关系数测试通过，corr={corr:.4f}")
    
    def test_calculate_similarity_methods(self):
        """测试不同相似度计算方法"""
        spectrum1 = np.random.rand(100)
        spectrum2 = np.random.rand(100)
        
        methods = ['cosine', 'correlation', 'euclidean', 'sam']
        
        for method in methods:
            sim = calculate_similarity(spectrum1, spectrum2, method=method)
            assert isinstance(sim, float)
        
        print("✓ 不同相似度计算方法测试通过")


# ==================== 谱库匹配测试 ====================
class TestLibraryMatch:
    """谱库匹配算法测试"""
    
    def test_spectral_library_load(self):
        """测试光谱库加载"""
        root_dir = Path(__file__).parent
        library_path = root_dir / "backend" / "library"
        
        library = SpectralLibrary(str(library_path))
        
        assert len(library.index) > 0
        
        # 测试加载具体物质
        spectrum_data = library.load_spectrum("silicon")
        assert spectrum_data is not None
        assert "peaks" in spectrum_data
        
        print(f"✓ 光谱库加载测试通过，共 {len(library.index)} 种物质")
    
    def test_match_library(self):
        """测试谱库匹配功能"""
        # 生成一个类似硅的光谱
        x = np.linspace(200, 3200, 1024)
        # 在 520 cm⁻¹ 处添加强峰
        spectrum = np.exp(-((x - 520) ** 2) / (2 * 8 ** 2))
        spectrum += np.random.normal(0, 0.01, 1024)
        spectrum = np.maximum(spectrum, 0)
        
        root_dir = Path(__file__).parent
        library_path = root_dir / "backend" / "library"
        
        results = match_library(spectrum, x, str(library_path), top_k=3)
        
        assert len(results) > 0
        
        # 检查返回结果格式 (支持 LibraryMatchResult 和 dict)
        for result in results:
            # 检查是否有 substance_id 属性或 id 键
            has_id = hasattr(result, 'substance_id') or ('id' in result if isinstance(result, dict) else False)
            assert has_id
            # 检查是否有 similarity 属性或键
            has_sim = hasattr(result, 'similarity') or ('similarity' in result if isinstance(result, dict) else False)
            assert has_sim
        
        # 获取第一个结果的 substance_id
        first_result = results[0]
        if hasattr(first_result, 'substance_id'):
            substance_id = first_result.substance_id
        else:
            substance_id = first_result.get('id', 'unknown')
        
        print(f"✓ 谱库匹配测试通过，Top 匹配：{substance_id}")


# ==================== 运行所有测试 ====================
def run_all_tests():
    """运行所有算法测试"""
    print("=" * 60)
    print("拉曼光谱算法模块 - 单元测试")
    print("=" * 60)
    
    # 创建测试实例
    test_classes = [
        TestSmoothing(),
        TestBaseline(),
        TestPeakDetection(),
        TestSimilarity(),
        TestLibraryMatch()
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n运行 {test_class.__class__.__name__} 测试...")
        print("-" * 40)
        
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                try:
                    method = getattr(test_class, method_name)
                    method()
                    passed += 1
                except Exception as e:
                    print(f"✗ {method_name} 失败：{e}")
                    failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
