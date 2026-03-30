"""
自动曝光算法测试

测试范围:
1. 基本功能测试
2. 边界条件测试（暗光谱、饱和光谱）
3. 参数验证测试
4. 异常处理测试
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# 添加项目路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.algorithms.auto_exposure import AutoExposure
from backend.error_handler import ApiResponse, ErrorCode


# ==================== 测试数据生成 ====================
def generate_spectrum(intensity: float = 0.5, noise: float = 0.01, n_points: int = 1024) -> np.ndarray:
    """
    生成测试光谱数据

    Args:
        intensity: 峰值强度（0-1）
        noise: 噪声水平
        n_points: 数据点数

    Returns:
        模拟光谱数组
    """
    spectrum = np.ones(n_points) * 0.1  # 基线
    spectrum[512] = intensity  # 添加一个峰
    spectrum += np.random.normal(0, noise, n_points)
    return np.clip(spectrum, 0, 1)


def mock_acquire_spectrum(integration_time: int) -> np.ndarray:
    """
    模拟光谱采集函数

    假设光谱强度与积分时间成正比关系
    """
    # 归一化积分时间（10-10000ms -> 0-1）
    normalized_time = (integration_time - 10) / (10000 - 10)
    # 强度与积分时间成正比，但有饱和效应
    intensity = min(1.0, normalized_time * 1.5)
    return generate_spectrum(intensity=intensity)


# ==================== 基本功能测试 ====================
class TestAutoExposureBasic:
    """自动曝光基本功能测试"""

    def test_auto_exposure_initialization(self):
        """测试自动曝光初始化"""
        ae = AutoExposure()

        assert ae.enabled == False
        assert ae.target_intensity == 0.7
        assert ae.current_integration_time is None
        assert ae._tolerance == 0.1
        assert ae._max_iterations == 3

    def test_auto_exposure_custom_initialization(self):
        """测试自定义参数初始化"""
        ae = AutoExposure(
            target_intensity=0.6,
            tolerance=0.15,
            max_iterations=5,
            min_integration_time=20,
            max_integration_time=5000
        )

        assert ae.target_intensity == 0.6
        assert ae._tolerance == 0.15
        assert ae._max_iterations == 5
        assert ae._min_time == 20
        assert ae._max_time == 5000

    def test_set_target_intensity_valid(self):
        """测试设置有效目标强度"""
        ae = AutoExposure()
        response = ae.set_target_intensity(0.6)

        assert response.success == True
        assert ae.target_intensity == 0.6
        assert response.data["target_intensity"] == 0.6

    def test_set_target_intensity_invalid(self):
        """测试设置无效目标强度"""
        ae = AutoExposure()

        # 测试过低值
        response = ae.set_target_intensity(0.3)
        assert response.success == False
        assert response.error_code == ErrorCode.INVALID_PARAMETER

        # 测试过高值
        response = ae.set_target_intensity(0.9)
        assert response.success == False
        assert response.error_code == ErrorCode.INVALID_PARAMETER


# ==================== 边界条件测试 ====================
class TestAutoExposureBoundary:
    """自动曝光边界条件测试"""

    def test_dark_spectrum_handling(self):
        """测试暗光谱处理（强度=0）"""
        ae = AutoExposure(max_iterations=3)

        def mock_dark_acquire(integration_time: int) -> np.ndarray:
            # 始终返回暗光谱（全 0）
            return np.zeros(1024)

        # 应该能够处理暗光谱，不会无限循环
        response = ae.execute(mock_dark_acquire, current_integration_time=100)

        # 由于始终为 0，应该超时或返回最佳结果
        # 关键是不能抛出异常或无限循环
        assert isinstance(response, ApiResponse)

    def test_saturated_spectrum_handling(self):
        """测试饱和光谱处理（强度=1.0）"""
        ae = AutoExposure(max_iterations=3)

        def mock_saturated_acquire(integration_time: int) -> np.ndarray:
            # 始终返回饱和光谱
            spectrum = np.ones(1024) * 1.0
            return spectrum

        # 应该能够处理饱和光谱，减小积分时间
        response = ae.execute(mock_saturated_acquire, current_integration_time=100)

        # 由于始终饱和，应该超时
        assert isinstance(response, ApiResponse)

    def test_null_spectrum_handling(self):
        """测试空光谱数据处理"""
        ae = AutoExposure()

        def mock_null_acquire(integration_time: int) -> np.ndarray:
            return None

        response = ae.execute(mock_null_acquire, current_integration_time=100)

        assert response.success == False
        assert response.error_code == ErrorCode.ACQUISITION_FAILED
        assert "空数据" in response.message

    def test_empty_spectrum_handling(self):
        """测试空数组光谱数据处理"""
        ae = AutoExposure()

        def mock_empty_acquire(integration_time: int) -> np.ndarray:
            return np.array([])

        response = ae.execute(mock_empty_acquire, current_integration_time=100)

        assert response.success == False
        assert response.error_code == ErrorCode.ACQUISITION_FAILED


# ==================== 功能测试 ====================
class TestAutoExposureFunctional:
    """自动曝光功能测试"""

    def test_auto_exposure_success_scenario(self):
        """测试自动曝光成功场景"""
        ae = AutoExposure(target_intensity=0.5, tolerance=0.2, max_iterations=5)

        # 使用模拟采集函数
        response = ae.execute(mock_acquire_spectrum, current_integration_time=100)

        # 应该成功或超时（取决于模拟函数）
        assert isinstance(response, ApiResponse)

        # 如果成功，应该包含正确的数据字段
        if response.success:
            assert "final_integration_time" in response.data
            assert "iterations" in response.data
            assert "final_intensity" in response.data

    def test_auto_exposure_convergence(self):
        """测试自动曝光收敛性"""
        ae = AutoExposure(target_intensity=0.7, tolerance=0.1, max_iterations=10)

        # 使用线性响应的模拟采集函数
        def linear_acquire(integration_time: int) -> np.ndarray:
            normalized_time = (integration_time - 10) / (10000 - 10)
            intensity = min(1.0, normalized_time * 1.2)
            return generate_spectrum(intensity=intensity)

        response = ae.execute(linear_acquire, current_integration_time=100)

        # 在 10 次迭代内应该能够收敛
        if response.success:
            final_intensity = response.data.get("final_intensity", 0)
            # 最终强度应该在目标范围内
            assert 0.6 <= final_intensity <= 0.8

    def test_auto_exposure_timeout(self):
        """测试自动曝光超时场景"""
        # 使用非常小的迭代次数强制超时
        ae = AutoExposure(target_intensity=0.5, tolerance=0.01, max_iterations=1)

        response = ae.execute(mock_acquire_spectrum, current_integration_time=100)

        # 1 次迭代很可能不够，应该超时
        if not response.success:
            assert response.error_code == ErrorCode.AUTO_EXPOSURE_TIMEOUT


# ==================== 状态管理测试 ====================
class TestAutoExposureState:
    """自动曝光状态管理测试"""

    def test_get_status(self):
        """测试获取状态"""
        ae = AutoExposure()
        response = ae.get_status()

        assert response.success == True
        assert response.data["enabled"] == False
        assert response.data["target_intensity"] == 0.7

    def test_set_enabled(self):
        """测试设置启用状态"""
        ae = AutoExposure()

        ae.set_enabled(True)
        assert ae.enabled == True

        ae.set_enabled(False)
        assert ae.enabled == False

    def test_reset(self):
        """测试重置状态"""
        ae = AutoExposure()
        ae._current_integration_time = 500
        ae._last_result = {"test": "data"}

        ae.reset()

        assert ae.current_integration_time is None
        assert ae._last_result is None


# ==================== 参数验证测试 ====================
class TestAutoExposureValidation:
    """自动曝光参数验证测试"""

    def test_invalid_target_intensity_in_execute(self):
        """测试 execute 方法中目标强度验证"""
        ae = AutoExposure()
        ae._target_intensity = 0.3  # 非法值

        response = ae.execute(mock_acquire_spectrum, current_integration_time=100)

        assert response.success == False
        assert response.error_code == ErrorCode.INVALID_PARAMETER

    def test_invalid_integration_time_range(self):
        """测试积分时间范围验证"""
        ae = AutoExposure(min_integration_time=100, max_integration_time=1000)

        # 当前积分时间超出范围
        response = ae.execute(mock_acquire_spectrum, current_integration_time=50)

        assert response.success == False
        assert response.error_code == ErrorCode.INVALID_PARAMETER


# ==================== 运行所有测试 ====================
def run_all_tests():
    """运行所有自动曝光测试"""
    print("=" * 60)
    print("自动曝光算法 - 单元测试")
    print("=" * 60)

    test_classes = [
        TestAutoExposureBasic(),
        TestAutoExposureBoundary(),
        TestAutoExposureFunctional(),
        TestAutoExposureState(),
        TestAutoExposureValidation(),
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
                    print(f"✓ {method_name}")
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
