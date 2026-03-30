"""
P0 修复验证测试
"""
import sys
from PySide6.QtCore import QCoreApplication

# 创建全局应用实例
app = QCoreApplication(sys.argv)

def test_state_manager_parameter_signals():
    """测试 StateManager 参数变化信号"""
    from backend.state_manager import StateManager
    
    sm = StateManager()
    signals_received = []
    
    def on_integration_time_changed(value):
        signals_received.append(('integration', value))
    
    def on_accumulation_changed(value):
        signals_received.append(('accumulation', value))
    
    def on_smoothing_changed(value):
        signals_received.append(('smoothing', value))
    
    sm.integrationTimeChanged.connect(on_integration_time_changed)
    sm.accumulationCountChanged.connect(on_accumulation_changed)
    sm.smoothingWindowChanged.connect(on_smoothing_changed)
    
    # 测试参数变化信号
    sm.set_integration_time(500)
    sm.set_accumulation_count(10)
    sm.set_smoothing_window(15)
    
    # 处理事件
    app.processEvents()
    
    print(f'StateManager 参数信号测试：{signals_received}')
    assert len(signals_received) == 3, f'应该收到 3 个信号，实际收到{len(signals_received)}个'
    assert signals_received[0] == ('integration', 500)
    assert signals_received[1] == ('accumulation', 10)
    assert signals_received[2] == ('smoothing', 15)
    print('✓ StateManager 参数信号测试通过')
    return True


def test_error_code_constants():
    """测试错误码常量"""
    from main import ErrorCode
    
    # 通用错误
    assert ErrorCode.UNKNOWN_ERROR == 0
    assert ErrorCode.INVALID_PARAMETER == 1
    
    # 采集相关错误
    assert ErrorCode.ACQUISITION_ERROR == 100
    assert ErrorCode.DEVICE_NOT_CONNECTED == 101
    assert ErrorCode.SPECTRUM_READ_FAILED == 102
    
    # 数据处理错误
    assert ErrorCode.BASELINE_CORRECTION_FAILED == 200
    assert ErrorCode.PEAK_AREA_CALCULATION_FAILED == 202
    assert ErrorCode.LIBRARY_MATCH_FAILED == 203
    
    # 文件操作错误
    assert ErrorCode.DATA_EXPORT_FAILED == 300
    assert ErrorCode.DATA_IMPORT_FAILED == 301
    
    print('✓ ErrorCode 常量测试通过')
    return True


def test_bridge_object_error_signal():
    """测试 BridgeObject 错误信号"""
    from main import BridgeObject, ErrorCode
    from backend.state_manager import StateManager
    from backend.driver import MockDriver
    
    sm = StateManager()
    driver = MockDriver()
    driver.connect()
    
    bridge = BridgeObject(sm, driver)
    errors_received = []
    
    def on_error(code, msg):
        errors_received.append((code, msg))
    
    bridge.errorSignal.connect(on_error)
    
    # 测试：没有光谱数据时导出
    bridge.exportData('json')
    app.processEvents()
    
    print(f'错误信号测试：{errors_received}')
    assert len(errors_received) > 0, "应该收到错误信号"
    assert errors_received[0][0] == ErrorCode.SPECTRUM_READ_FAILED, \
        f"错误码应该是 SPECTRUM_READ_FAILED: {errors_received[0][0]}"
    print('✓ BridgeObject 错误信号测试通过')
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("P0 修复验证测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if not test_state_manager_parameter_signals():
            all_passed = False
    except Exception as e:
        print(f'✗ StateManager 参数信号测试失败：{e}')
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_error_code_constants():
            all_passed = False
    except Exception as e:
        print(f'✗ ErrorCode 常量测试失败：{e}')
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_bridge_object_error_signal():
            all_passed = False
    except Exception as e:
        print(f'✗ BridgeObject 错误信号测试失败：{e}')
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("所有 P0 修复验证通过!")
        sys.exit(0)
    else:
        print("部分测试失败")
        sys.exit(1)
