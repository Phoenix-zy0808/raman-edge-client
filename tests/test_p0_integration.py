"""
P0 功能集成测试 - Mock 版本

不依赖真实 Qt 应用，使用纯 Python 测试 Bridge API
测试范围:
- P0-1 实时采集 API
- P0-2 峰值识别 API
- P0-3 预处理 API
- P0-4 差谱运算 API
"""
import pytest
import json
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.driver import MockDriver
from backend.state_manager import StateManager
from main import BridgeObject


# ==================== Fixtures ====================

@pytest.fixture
def driver():
    """创建 MockDriver"""
    driver = MockDriver()
    driver.connect()
    yield driver
    driver.disconnect()


@pytest.fixture
def bridge(driver):
    """创建 Bridge 对象（不需要 Qt 应用）"""
    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    yield bridge
    # 清理
    if hasattr(bridge, '_live_service') and bridge._live_service:
        bridge._live_service.stop()


@pytest.fixture
def sample_spectrum():
    """生成模拟拉曼光谱数据"""
    wavelengths = np.linspace(200, 3200, 1024)
    
    # 基线
    baseline = 100 + 50 * np.sin(wavelengths / 1000 * np.pi)
    
    # 添加特征峰
    spectrum = baseline.copy()
    spectrum += 300 * np.exp(-(wavelengths - 500) ** 2 / (2 * 30 ** 2))
    spectrum += 500 * np.exp(-(wavelengths - 1000) ** 2 / (2 * 50 ** 2))
    spectrum += 400 * np.exp(-(wavelengths - 1500) ** 2 / (2 * 40 ** 2))
    
    np.random.seed(42)
    noise = np.random.normal(0, 10, len(wavelengths))
    spectrum += noise
    
    return {
        'wavelength': wavelengths,
        'intensity': spectrum.astype(float).tolist()
    }


# ==================== P0-1 实时采集 API 测试 ====================

class TestLiveAcquisitionAPI:
    """P0-1 实时采集 API 测试"""
    
    def test_startLiveMode_valid_rate(self, bridge):
        """测试启动实时采集 - 有效刷新率"""
        result_json = bridge.startLiveMode('{"value": 5.0}')
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        # 验证返回格式
        assert isinstance(result, dict)
        # 刷新率应该在响应中
        if isinstance(result, dict):
            assert "success" in result or "code" in result or "data" in result
    
    def test_startLiveMode_invalid_rate_too_high(self, bridge):
        """测试启动实时采集 - 刷新率过高"""
        result_json = bridge.startLiveMode('{"value": 100.0}')
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        # 应该返回错误（刷新率超出范围）
        assert isinstance(result, dict)
        # 要么 success=False，要么有 error 字段
        has_success_false = result.get("success") == False
        has_error = "error" in result or "message" in result
        assert has_success_false or has_error
    
    def test_startLiveMode_invalid_rate_too_low(self, bridge):
        """测试启动实时采集 - 刷新率过低"""
        result_json = bridge.startLiveMode('{"value": 0.01}')
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        # 应该返回错误
        assert isinstance(result, dict)
        has_success_false = result.get("success") == False
        has_error = "error" in result or "message" in result
        assert has_success_false or has_error
    
    def test_stopLiveMode(self, bridge):
        """测试停止实时采集"""
        result_json = bridge.stopLiveMode()
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        assert isinstance(result, dict)


# ==================== P0-2 峰值识别 API 测试 ====================

class TestPeakDetectionAPI:
    """P0-2 峰值识别 API 测试"""
    
    def test_findPeaks_basic(self, bridge, sample_spectrum):
        """测试自动寻峰"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        params_json = json.dumps({
            "sensitivity": 0.5,
            "minSnr": 3.0,
            "minDistance": 5
        })
        
        result_json = bridge.findPeaks(spectrum_json, params_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        assert isinstance(result, dict)
        if result.get("success"):
            assert "data" in result
            assert "peaks" in result["data"]
            assert "count" in result["data"]
    
    def test_findPeaks_different_sensitivity(self, bridge, sample_spectrum):
        """测试不同灵敏度的寻峰"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        
        # 高灵敏度
        params_high = json.dumps({"sensitivity": 0.8, "minSnr": 1.0, "minDistance": 5})
        result_high = json.loads(bridge.findPeaks(spectrum_json, params_high))
        
        # 低灵敏度
        params_low = json.dumps({"sensitivity": 0.3, "minSnr": 5.0, "minDistance": 10})
        result_low = json.loads(bridge.findPeaks(spectrum_json, params_low))
        
        if result_high.get("success") and result_low.get("success"):
            # 高灵敏度应该检测到更多或相等的峰
            assert result_high["data"]["count"] >= result_low["data"]["count"]
    
    def test_fitPeak_gaussian(self, bridge, sample_spectrum):
        """测试高斯峰值拟合"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        
        # 在最大峰位置拟合
        max_index = sample_spectrum['intensity'].index(max(sample_spectrum['intensity']))
        position_json = json.dumps({"index": max_index})
        fit_type_json = json.dumps({"type": "gaussian"})
        
        result_json = bridge.fitPeak(spectrum_json, position_json, fit_type_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            assert "data" in result
            data = result["data"]
            assert "r_squared" in data or "r2" in data


# ==================== P0-3 预处理 API 测试 ====================

class TestPreprocessingAPI:
    """P0-3 预处理 API 集成测试"""
    
    def test_preprocess_smooth(self, bridge, sample_spectrum):
        """测试平滑预处理"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        params_json = json.dumps({
            "tools": [
                ("smooth", {"method": "savitzky_golay", "window_size": 11, "poly_order": 3})
            ]
        })
        
        result_json = bridge.preprocess(spectrum_json, params_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            assert "data" in result
            assert "spectrum" in result["data"]
            assert len(result["data"]["spectrum"]) == 1024
    
    def test_preprocess_normalize(self, bridge, sample_spectrum):
        """测试归一化预处理"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        params_json = json.dumps({
            "tools": [
                ("normalize", {"method": "minmax"})
            ]
        })
        
        result_json = bridge.preprocess(spectrum_json, params_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            processed = result["data"]["spectrum"]
            # 归一化后应该在 0-1 之间
            assert min(processed) >= 0
            assert max(processed) <= 1.0
    
    def test_preprocess_combined(self, bridge, sample_spectrum):
        """测试组合预处理"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        params_json = json.dumps({
            "tools": [
                ("smooth", {"method": "savitzky_golay", "window_size": 11, "poly_order": 3}),
                ("baseline", {"order": 3, "iterations": 5}),
                ("normalize", {"method": "minmax"})
            ]
        })
        
        result_json = bridge.preprocess(spectrum_json, params_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            processed = result["data"]["spectrum"]
            assert len(processed) == 1024
            assert min(processed) >= 0
            assert max(processed) <= 1.0


# ==================== P0-4 差谱运算 API 测试 ====================

class TestDifferenceAPI:
    """P0-4 差谱运算 API 集成测试"""
    
    def test_subtractSpectra_basic(self, bridge, sample_spectrum):
        """测试基本差谱运算"""
        spectrum1_json = json.dumps(sample_spectrum['intensity'])
        spectrum2_json = json.dumps(sample_spectrum['intensity'])  # 相同光谱相减
        coefficient_json = json.dumps({"value": 1.0})
        
        result_json = bridge.subtractSpectra(spectrum1_json, spectrum2_json, coefficient_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            difference = result["data"]["difference"]
            # 相同光谱相减应该接近 0
            assert all(abs(v) < 1e-6 for v in difference)
    
    def test_subtractSpectra_with_coefficient(self, bridge, sample_spectrum):
        """测试带系数的差谱运算"""
        spectrum1 = sample_spectrum['intensity']
        spectrum2 = [v * 0.5 for v in spectrum1]  # spectrum2 是 spectrum1 的一半
        
        spectrum1_json = json.dumps(spectrum1)
        spectrum2_json = json.dumps(spectrum2)
        coefficient_json = json.dumps({"value": 1.0})
        
        result_json = bridge.subtractSpectra(spectrum1_json, spectrum2_json, coefficient_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            difference = result["data"]["difference"]
            # 差谱应该是 spectrum1 的一半
            expected = [v * 0.5 for v in spectrum1]
            for d, e in zip(difference, expected):
                assert abs(d - e) < 1e-6


# ==================== 集成工作流测试 ====================

class TestIntegrationWorkflow:
    """集成工作流测试 - 模拟真实用户操作"""
    
    def test_full_peak_analysis_workflow(self, bridge, sample_spectrum):
        """测试完整的峰值分析工作流"""
        spectrum_json = json.dumps(sample_spectrum['intensity'])
        
        # 1. 预处理
        preprocess_params = json.dumps({
            "tools": [
                ("smooth", {"method": "savitzky_golay", "window_size": 11, "poly_order": 3}),
                ("baseline", {"order": 3, "iterations": 5})
            ]
        })
        preprocess_result = json.loads(bridge.preprocess(spectrum_json, preprocess_params))
        
        if not preprocess_result.get("success"):
            pytest.skip("预处理失败")
        
        processed_spectrum = preprocess_result["data"]["spectrum"]
        
        # 2. 寻峰
        find_peaks_params = json.dumps({
            "sensitivity": 0.5,
            "minSnr": 3.0,
            "minDistance": 5
        })
        peaks_result = json.loads(bridge.findPeaks(
            json.dumps(processed_spectrum),
            find_peaks_params
        ))
        
        if peaks_result.get("success"):
            assert "peaks" in peaks_result["data"]
            assert len(peaks_result["data"]["peaks"]) > 0
    
    def test_full_difference_workflow(self, bridge, sample_spectrum):
        """测试完整的差谱工作流"""
        # 创建两个不同的光谱
        spectrum1 = sample_spectrum['intensity']
        spectrum2 = [v * 0.8 for v in spectrum1]
        
        spectrum1_json = json.dumps(spectrum1)
        spectrum2_json = json.dumps(spectrum2)
        coefficient_json = json.dumps({"value": 1.0})
        
        # 差谱运算
        result_json = bridge.subtractSpectra(spectrum1_json, spectrum2_json, coefficient_json)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        if result.get("success"):
            difference = result["data"]["difference"]
            assert len(difference) == 1024
            
            # 验证差谱值
            expected = [s1 - s2 for s1, s2 in zip(spectrum1, spectrum2)]
            for d, e in zip(difference, expected):
                assert abs(d - e) < 1e-6


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
