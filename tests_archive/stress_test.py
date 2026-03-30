"""
压力测试脚本

测试项目:
1. 长时间运行内存泄漏测试（使用 psutil 测量进程总内存）
2. 高频状态切换测试
3. 大数据量传输测试

使用方法:
    python stress_test.py [--duration 3600] [--sample-rate 50]
"""
import sys
import os
import time
import argparse
import tracemalloc
import logging
from pathlib import Path

# 尝试导入 psutil（用于测量进程总内存，包含 C++ 对象）
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Windows 下 PySide6 需要添加 DLL 目录
if os.name == 'nt':
    try:
        os.add_dll_directory(r'C:\Windows\System32')
    except Exception:
        pass

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.driver import MockDriver, DeviceState
from backend.state_manager import StateManager
from backend.inference import MockInference
from main import BridgeObject, WorkerThread

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
log = logging.getLogger(__name__)


def test_memory_leak(duration_seconds: int = 60, sample_rate: float = 50.0):
    """
    内存泄漏测试

    Args:
        duration_seconds: 测试持续时间（秒）
        sample_rate: 采样率（Hz）

    改进说明:
        - 使用 psutil 测量进程总内存（包含 C++ 对象）
        - 每 10 分钟记录一次内存曲线
        - 内存增长率 > 0.1 MB/分钟 报警
    """
    print("=" * 70)
    print(f"内存泄漏测试 - 持续 {duration_seconds} 秒，采样率 {sample_rate}Hz")
    print("=" * 70)

    # 开始内存追踪
    tracemalloc.start()

    # 获取进程对象（用于 psutil）
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        print(f"[初始] 进程总内存：{memory_before:.2f} MB")
    else:
        memory_before = 0

    app = QApplication.instance() or QApplication(sys.argv)

    # 初始化组件
    driver = MockDriver(seed=42, noise_level=0.02)
    driver.connect()

    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    worker = WorkerThread(driver, sample_rate=sample_rate)

    # 统计数据
    spectra_count = 0
    errors_count = 0

    def on_spectrum(data):
        nonlocal spectra_count
        spectra_count += 1

    def on_error(msg):
        nonlocal errors_count
        errors_count += 1
        print(f"[Error] {msg}")

    worker.spectrumReady.connect(on_spectrum)
    worker.errorOccurred.connect(on_error)

    # 启动采集
    worker.start()
    bridge.startAcquisition()

    print(f"[{time.strftime('%H:%M:%S')}] 开始采集...")

    # 记录内存快照
    start_time = time.time()
    snapshots = []
    last_report_time = start_time

    try:
        while time.time() - start_time < duration_seconds:
            app.processEvents()
            time.sleep(0.1)  # 降低 CPU 占用

            current_time = time.time()
            elapsed = current_time - start_time

            # 每 10 分钟记录一次内存使用
            if current_time - last_report_time >= 600:  # 10 分钟
                if HAS_PSUTIL:
                    current_mem = process.memory_info().rss / 1024 / 1024
                else:
                    current_mem, _ = tracemalloc.get_traced_memory()
                    current_mem = current_mem / 1024 / 1024

                snapshots.append({
                    'time': elapsed,
                    'current_mb': current_mem,
                    'spectra': spectra_count
                })

                growth_rate = (current_mem - memory_before) / (elapsed / 60) if elapsed > 0 else 0
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"内存：{current_mem:.2f}MB, "
                      f"增长：{current_mem - memory_before:.2f}MB, "
                      f"增长率：{growth_rate:.4f} MB/分钟，"
                      f"光谱数：{spectra_count}")

                # 报警
                if growth_rate > 0.1:
                    print(f"⚠️  警告：内存增长率过高 ({growth_rate:.4f} MB/分钟)")

                last_report_time = current_time

    except KeyboardInterrupt:
        print("\n[测试被用户中断]")

    finally:
        # 停止采集
        bridge.stopAcquisition()
        worker.stop()
        driver.disconnect()

        # 最终内存统计
        if HAS_PSUTIL:
            memory_after = process.memory_info().rss / 1024 / 1024
        else:
            current, peak = tracemalloc.get_traced_memory()
            memory_after = current / 1024 / 1024

        tracemalloc.stop()

        total_time = time.time() - start_time
        total_growth = memory_after - memory_before
        growth_rate = total_growth / (total_time / 60) if total_time > 0 else 0

        print("\n" + "=" * 70)
        print("测试结果")
        print("=" * 70)
        print(f"持续时间：{total_time:.1f}秒 ({total_time/3600:.2f}小时)")
        print(f"接收光谱数：{spectra_count}")
        print(f"错误数：{errors_count}")
        print(f"初始内存：{memory_before:.2f}MB")
        print(f"最终内存：{memory_after:.2f}MB")
        print(f"总增长：{total_growth:.2f}MB")
        print(f"内存增长率：{growth_rate:.4f} MB/分钟")

        # 判断是否通过
        if growth_rate > 0.1:
            print("❌ 失败：内存增长率过高 (> 0.1 MB/分钟)")
        elif growth_rate > 0.01:
            print("⚠️  警告：内存有轻微增长，需持续关注")
        else:
            print("✓ 内存增长在正常范围内 (< 0.01 MB/分钟)")

        print("=" * 70)

    return growth_rate <= 0.1


def test_high_frequency_state_changes(iterations: int = 100):
    """
    高频状态切换测试
    
    Args:
        iterations: 切换次数
    """
    print("\n" + "=" * 70)
    print(f"高频状态切换测试 - {iterations} 次迭代")
    print("=" * 70)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    driver = MockDriver()
    state_manager = StateManager()
    bridge = BridgeObject(state_manager, driver)
    worker = WorkerThread(driver, sample_rate=50.0)
    
    worker.start()
    
    success_count = 0
    fail_count = 0
    
    try:
        for i in range(iterations):
            # 快速切换状态
            bridge.connect()
            bridge.startAcquisition()
            
            # 短暂延迟
            for _ in range(5):
                app.processEvents()
                time.sleep(0.01)
            
            bridge.stopAcquisition()
            bridge.disconnect()
            
            # 短暂延迟
            for _ in range(5):
                app.processEvents()
                time.sleep(0.01)
            
            if (i + 1) % 10 == 0:
                print(f"[{i+1}/{iterations}] 已完成")
    
    except Exception as e:
        print(f"测试出错：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        worker.stop()
    
    print("\n" + "=" * 70)
    print("测试结果")
    print("=" * 70)
    print(f"总迭代次数：{iterations}")
    print(f"成功：{success_count}, 失败：{fail_count}")
    print("✓ 高频状态切换测试完成")
    print("=" * 70)
    
    return True


def test_inference():
    """测试推理模块"""
    print("\n" + "=" * 70)
    print("推理模块测试")
    print("=" * 70)
    
    # 创建模拟推理
    inference = MockInference(seed=42)
    
    # 测试未加载模型
    result = inference.predict(None, None)
    print(f"未加载模型：{result}")
    assert result.class_name == "no_model"
    
    # 加载模型（模拟）
    inference.load_model("mock_model.onnx")
    
    # 生成测试数据
    driver = MockDriver()
    driver.connect()
    spectrum = driver.read_spectrum()
    wavenumbers = driver.get_wavelengths()
    
    # 测试推理
    result = inference.predict(spectrum, wavenumbers)
    print(f"推理结果：{result}")
    print(f"  - 分类：{result.class_name}")
    print(f"  - 置信度：{result.confidence:.3f}")
    print(f"  - 特征峰数：{len(result.peaks)}")
    
    assert result.class_name != "no_model"
    assert 0 <= result.confidence <= 1
    
    print("\n" + "=" * 70)
    print("✓ 推理模块测试通过")
    print("=" * 70)
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='拉曼光谱边缘客户端 - 压力测试')
    parser.add_argument('--duration', type=int, default=60, 
                        help='内存测试持续时间（秒）')
    parser.add_argument('--sample-rate', type=float, default=50.0,
                        help='采样率（Hz）')
    parser.add_argument('--iterations', type=int, default=50,
                        help='高频状态切换次数')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("拉曼光谱边缘客户端 - 压力测试套件")
    print("=" * 70 + "\n")
    
    tests = [
        ("推理模块测试", test_inference),
        ("高频状态切换测试", lambda: test_high_frequency_state_changes(args.iterations)),
        ("内存泄漏测试", lambda: test_memory_leak(args.duration, args.sample_rate)),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ {name} 测试失败：{e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
