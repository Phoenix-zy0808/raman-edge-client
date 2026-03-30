"""
测试脚本 - 验证后端功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.driver import MockDriver, BaseDriver, DeviceState

def test_mock_driver():
    """测试 MockDriver 功能"""
    print("=" * 50)
    print("测试 MockDriver")
    print("=" * 50)
    
    # 创建驱动
    driver = MockDriver(seed=42, noise_level=0.02)
    print(f"✓ MockDriver 创建成功")
    
    # 测试连接
    assert driver.connect() == True
    print(f"✓ 设备连接成功，状态：{driver.connected}")
    
    # 测试波长数据
    wavelengths = driver.get_wavelengths()
    assert len(wavelengths) == 1024
    assert wavelengths.min() == 200.0
    assert wavelengths.max() == 3200.0
    print(f"✓ 波长范围：{wavelengths.min()} - {wavelengths.max()} cm⁻¹")
    print(f"✓ 数据点数：{len(wavelengths)}")
    
    # 测试光谱读取
    spectrum = driver.read_spectrum()
    assert spectrum is not None
    assert len(spectrum) == 1024
    assert spectrum.min() >= 0
    print(f"✓ 光谱数据形状：{spectrum.shape}")
    print(f"✓ 光谱强度范围：{spectrum.min():.4f} - {spectrum.max():.4f}")
    
    # 测试不同设备状态 (使用 Enum)
    driver.device_state = DeviceState.HIGH_NOISE
    noisy_spectrum = driver.read_spectrum()
    assert noisy_spectrum is not None
    print(f"✓ 高噪声模式光谱强度范围：{noisy_spectrum.min():.4f} - {noisy_spectrum.max():.4f}")
    
    # 测试异常状态
    driver.device_state = DeviceState.ERROR
    error_spectrum = driver.read_spectrum()
    assert error_spectrum is None
    print(f"✓ 异常状态返回 None")
    
    # 测试参数设置
    driver.device_state = DeviceState.NORMAL
    driver.set_params(noise_level=0.05)
    print(f"✓ 噪声水平设置为 0.05")
    
    # 测试断开连接
    driver.disconnect()
    assert driver.connected == False
    disconnected_spectrum = driver.read_spectrum()
    assert disconnected_spectrum is None
    print(f"✓ 断开连接后返回 None")
    
    print("=" * 50)
    print("所有 MockDriver 测试通过！")
    print("=" * 50)
    return True


def test_base_driver_interface():
    """测试 BaseDriver 接口"""
    print("\n" + "=" * 50)
    print("测试 BaseDriver 接口")
    print("=" * 50)
    
    # BaseDriver 是抽象类，不能直接实例化
    try:
        driver = BaseDriver()
        print("✗ BaseDriver 不应直接实例化")
        return False
    except TypeError:
        print("✓ BaseDriver 是抽象类，不能直接实例化")
    
    # MockDriver 应该继承 BaseDriver
    mock_driver = MockDriver()
    assert isinstance(mock_driver, BaseDriver)
    print("✓ MockDriver 继承自 BaseDriver")
    
    # 验证接口方法
    assert hasattr(mock_driver, 'connect')
    assert hasattr(mock_driver, 'disconnect')
    assert hasattr(mock_driver, 'read_spectrum')
    assert hasattr(mock_driver, 'get_wavelengths')
    assert hasattr(mock_driver, 'set_params')
    print("✓ 所有必需方法已实现")
    
    print("=" * 50)
    print("BaseDriver 接口测试通过！")
    print("=" * 50)
    return True


if __name__ == '__main__':
    success = True
    success &= test_base_driver_interface()
    success &= test_mock_driver()
    
    if success:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败！")
        sys.exit(1)
