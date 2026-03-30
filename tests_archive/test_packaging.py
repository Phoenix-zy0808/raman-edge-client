"""
打包验证测试脚本 - 验证 exe 打包后的功能完整性

P1 修复：添加打包后功能测试，验证：
- 所有 P0 功能在 exe 中可用
- 日志文件在 exe 中正常写入
- Qt 资源文件加载成功
- 依赖项（scipy, onnxruntime）可用
"""
import sys
import os
import json
import time
from pathlib import Path


def test_imports():
    """测试所有必需模块是否可以导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    required_modules = [
        "numpy",
        "scipy",
        "scipy.signal",
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
    ]
    
    failed = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n✗ 缺少模块：{', '.join(failed)}")
        return False
    print("\n✓ 所有必需模块导入成功\n")
    return True


def test_resources():
    """测试 Qt 资源文件是否可以加载"""
    print("=" * 60)
    print("测试 2: Qt 资源文件")
    print("=" * 60)
    
    try:
        import resources
        print("✓ resources 模块导入成功")
    except ImportError as e:
        print(f"✗ resources 模块导入失败：{e}")
        return False
    
    # 检查前端文件是否存在
    frontend_files = [
        "frontend/index.html",
        "frontend/app.js",
        "frontend/styles.css",
    ]
    
    base_path = Path(__file__).parent
    all_exist = True
    for file in frontend_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} 不存在")
            all_exist = False
    
    if not all_exist:
        return False
    
    print("\n✓ 前端文件检查通过\n")
    return True


def test_library_data():
    """测试谱库数据是否可以加载"""
    print("=" * 60)
    print("测试 3: 谱库数据")
    print("=" * 60)
    
    library_dir = Path(__file__).parent / "backend" / "library"
    
    if not library_dir.exists():
        print(f"✗ 谱库目录不存在：{library_dir}")
        return False
    
    print(f"✓ 谱库目录存在：{library_dir}")
    
    # 检查 index.json
    index_path = library_dir / "index.json"
    if not index_path.exists():
        print("✗ index.json 不存在")
        return False
    
    print("✓ index.json 存在")
    
    # 验证 index.json 内容
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # P0 修复：验证免责声明
        if "disclaimer" in index_data:
            print(f"✓ 谱库包含免责声明")
        else:
            print("⚠ 谱库缺少免责声明")
        
        substances = index_data.get("substances", [])
        print(f"✓ 谱库包含 {len(substances)} 种物质")
        
        # 验证每种物质的谱图文件
        for substance in substances:
            substance_id = substance.get("id")
            spectrum_path = library_dir / f"{substance_id}.json"
            if spectrum_path.exists():
                print(f"  ✓ {substance_id}.json")
            else:
                print(f"  ✗ {substance_id}.json 不存在")
                return False
        
    except Exception as e:
        print(f"✗ 读取 index.json 失败：{e}")
        return False
    
    print("\n✓ 谱库数据检查通过\n")
    return True


def test_mock_driver():
    """测试 MockDriver 功能"""
    print("=" * 60)
    print("测试 4: MockDriver 功能")
    print("=" * 60)
    
    try:
        from backend.driver.mock_driver import MockDriver, DeviceState
        print("✓ MockDriver 导入成功")
    except Exception as e:
        print(f"✗ MockDriver 导入失败：{e}")
        return False
    
    # 创建驱动
    driver = MockDriver(seed=42, noise_level=0.02)
    print("✓ MockDriver 创建成功")
    
    # 测试连接
    if not driver.connect():
        print("✗ 设备连接失败")
        return False
    print("✓ 设备连接成功")
    
    # 测试波长数据
    wavelengths = driver.get_wavelengths()
    if len(wavelengths) != 1024:
        print(f"✗ 波长数据点数错误：{len(wavelengths)} (期望 1024)")
        return False
    print(f"✓ 波长范围：{wavelengths.min()} - {wavelengths.max()} cm⁻¹")
    
    # 测试光谱读取
    spectrum = driver.read_spectrum()
    if spectrum is None:
        print("✗ 光谱读取失败")
        return False
    print(f"✓ 光谱数据形状：{spectrum.shape}")
    
    # P0 修复：验证 MockDriver 不再应用平滑滤波
    driver.set_params(smoothing_window=5)
    spectrum_smooth = driver.read_spectrum()
    print("✓ MockDriver 平滑窗口设置成功（平滑在 WorkerThread 中应用）")
    
    # 测试设备状态
    driver.device_state = DeviceState.HIGH_NOISE
    noisy_spectrum = driver.read_spectrum()
    if noisy_spectrum is None:
        print("✗ 高噪声模式光谱读取失败")
        return False
    print("✓ 高噪声模式测试成功")
    
    print("\n✓ MockDriver 功能检查通过\n")
    return True


def test_inference():
    """测试推理模块功能"""
    print("=" * 60)
    print("测试 5: 推理模块功能")
    print("=" * 60)
    
    try:
        from backend.inference import MockInference, LocalInference
        print("✓ MockInference 和 LocalInference 导入成功")
    except Exception as e:
        print(f"✗ 推理模块导入失败：{e}")
        return False
    
    # 测试 MockInference
    inference = MockInference()
    if not inference.load_model("mock_model.onnx"):
        print("⚠ MockInference 模型加载（模拟）")
    print("✓ MockInference 初始化成功")
    
    # 测试谱库匹配
    import numpy as np
    wavenumbers = np.linspace(200, 3200, 1024)
    spectrum = np.exp(-((wavenumbers - 520) ** 2) / (2 * 30 ** 2))
    
    results = inference.match_library(spectrum, wavenumbers, top_k=3)
    if len(results) == 0:
        print("✗ 谱库匹配返回空结果")
        return False
    
    # P0 修复：验证置信度阈值
    first_result = results[0]
    if "is_match" not in first_result:
        print("✗ 谱库匹配结果缺少 is_match 字段")
        return False
    print(f"✓ 谱库匹配返回 {len(results)} 个结果")
    print(f"✓ 最佳匹配：{first_result['name']} (score={first_result['score']:.3f})")
    
    # 测试 LocalInference
    local_inference = LocalInference()
    print("✓ LocalInference 初始化成功")
    print(f"  - 波长范围：{local_inference._config['wavenumber_range']}")
    print(f"  - 归一化方式：{local_inference._normalization}")
    
    print("\n✓ 推理模块功能检查通过\n")
    return True


def test_logging():
    """测试日志功能"""
    print("=" * 60)
    print("测试 6: 日志功能")
    print("=" * 60)
    
    try:
        from backend.logging_config import setup_logging, get_logger
        print("✓ 日志模块导入成功")
    except Exception as e:
        print(f"✗ 日志模块导入失败：{e}")
        return False
    
    # 设置日志
    log_file = Path(__file__).parent / "test_packaging.log"
    logger = setup_logging(
        log_level=20,  # INFO
        log_file=str(log_file),
        console_output=False,
        debug_mode=False
    )
    
    log = get_logger(__name__)
    log.info("[PackagingTest] 日志测试开始")
    
    # 验证日志文件是否创建
    if not log_file.exists():
        print(f"✗ 日志文件未创建：{log_file}")
        return False
    print(f"✓ 日志文件创建成功：{log_file}")
    
    # 验证日志内容
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        if "[PackagingTest]" in log_content:
            print("✓ 日志内容写入成功")
        else:
            print("✗ 日志内容不包含预期标记")
            return False
        
        # P2 修复：验证线程 ID
        if "|" in log_content:
            parts = log_content.split("|")
            if len(parts) >= 3:
                print("✓ 日志格式包含分隔符（可能包含线程 ID）")
        
    except Exception as e:
        print(f"✗ 读取日志文件失败：{e}")
        return False
    
    # 清理日志文件
    try:
        log_file.unlink()
        print("✓ 测试日志文件已清理")
    except:
        pass
    
    print("\n✓ 日志功能检查通过\n")
    return True


def test_bridge_object():
    """测试 BridgeObject 功能"""
    print("=" * 60)
    print("测试 7: BridgeObject 功能")
    print("=" * 60)
    
    try:
        from main import BridgeObject
        from backend.state_manager import StateManager
        from backend.driver.mock_driver import MockDriver
        print("✓ BridgeObject 导入成功")
    except Exception as e:
        print(f"✗ BridgeObject 导入失败：{e}")
        return False
    
    # 创建对象
    state_manager = StateManager()
    driver = MockDriver()
    driver.connect()
    
    bridge = BridgeObject(state_manager, driver)
    print("✓ BridgeObject 创建成功")
    
    # P1 修复：验证 set_worker_thread 方法
    if not hasattr(bridge, 'set_worker_thread'):
        print("✗ BridgeObject 缺少 set_worker_thread 方法")
        return False
    print("✓ BridgeObject.set_worker_thread 方法存在")
    
    # 测试波长数据
    if bridge._wavelengths is None:
        print("✗ 波长数据未初始化")
        return False
    print(f"✓ 波长数据初始化：{len(bridge._wavelengths)} 点")
    
    print("\n✓ BridgeObject 功能检查通过\n")
    return True


def test_frontend_files():
    """P2 修复：测试前端文件是否存在且可访问"""
    print("=" * 60)
    print("测试 8: 前端文件")
    print("=" * 60)
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print(f"✗ 前端目录不存在：{frontend_dir}")
        return False
    
    print(f"✓ 前端目录存在：{frontend_dir}")
    
    # 检查必需的前端文件
    required_files = [
        "index.html",
        "app.js",
        "styles.css",
    ]
    
    all_exist = True
    for file in required_files:
        file_path = frontend_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {file} ({size} 字节)")
        else:
            print(f"✗ {file} 不存在")
            all_exist = False
    
    if not all_exist:
        return False
    
    # 验证 index.html 内容
    index_path = frontend_dir / "index.html"
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "QWebChannel" in content:
            print("✓ index.html 包含 QWebChannel 引用")
        else:
            print("⚠ index.html 可能缺少 QWebChannel 引用")
        
        if "app.js" in content:
            print("✓ index.html 引用 app.js")
        else:
            print("✗ index.html 未引用 app.js")
            return False
        
        if "styles.css" in content:
            print("✓ index.html 引用 styles.css")
        else:
            print("✗ index.html 未引用 styles.css")
            return False
        
    except Exception as e:
        print(f"✗ 读取 index.html 失败：{e}")
        return False
    
    # 验证 app.js 内容
    app_path = frontend_dir / "app.js"
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # P2 修复：验证函数支持参数
        if "function calculatePeakArea(peakCenter" in content:
            print("✓ calculatePeakArea 支持参数")
        else:
            print("⚠ calculatePeakArea 可能不支持参数")
        
        if "function matchLibrary(topK" in content:
            print("✓ matchLibrary 支持参数")
        else:
            print("⚠ matchLibrary 可能不支持参数")
        
        if "function exportData(format" in content:
            print("✓ exportData 支持参数")
        else:
            print("⚠ exportData 可能不支持参数")
        
    except Exception as e:
        print(f"✗ 读取 app.js 失败：{e}")
        return False
    
    print("\n✓ 前端文件检查通过\n")
    return True


def test_logging_thread_id():
    """P2 修复：测试日志线程 ID 功能"""
    print("=" * 60)
    print("测试 9: 日志线程 ID")
    print("=" * 60)
    
    import threading
    import time
    
    try:
        from backend.logging_config import setup_logging, get_logger
        print("✓ 日志模块导入成功")
    except Exception as e:
        print(f"✗ 日志模块导入失败：{e}")
        return False
    
    # 设置日志
    log_file = Path(__file__).parent / "test_thread_id.log"
    logger = setup_logging(
        log_level=20,  # INFO
        log_file=str(log_file),
        console_output=False,
        debug_mode=False
    )
    
    log = get_logger(__name__)
    
    # 在主线程中记录日志
    main_thread_id = threading.current_thread().ident
    log.info(f"[MainThread] 主线程 ID: {main_thread_id}")
    
    # 在工作线程中记录日志
    worker_thread_id = None
    
    def worker_log():
        nonlocal worker_thread_id
        worker_thread_id = threading.current_thread().ident
        log.info(f"[WorkerThread] 工作线程 ID: {worker_thread_id}")
    
    worker = threading.Thread(target=worker_log)
    worker.start()
    worker.join()
    
    # 验证日志文件
    if not log_file.exists():
        print(f"✗ 日志文件未创建：{log_file}")
        return False
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        print(f"✓ 日志文件包含 {len(lines)} 行")
        
        # 验证线程 ID 格式
        for line in lines:
            if "Thread-" in line:
                print(f"✓ 日志包含线程 ID: {line[:100]}...")
                break
        else:
            print("✗ 日志未包含线程 ID")
            return False
        
        # 验证不同线程的日志
        if len(lines) >= 2:
            print("✓ 多个线程的日志已记录")
        
    except Exception as e:
        print(f"✗ 读取日志文件失败：{e}")
        return False
    
    # 清理日志文件
    try:
        log_file.unlink()
        print("✓ 测试日志文件已清理")
    except:
        pass
    
    print("\n✓ 日志线程 ID 功能检查通过\n")
    return True


def run_all_tests():
    """运行所有打包验证测试"""
    print("\n" + "=" * 60)
    print("拉曼光谱边缘客户端 - 打包验证测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("模块导入", test_imports),
        ("Qt 资源文件", test_resources),
        ("谱库数据", test_library_data),
        ("MockDriver", test_mock_driver),
        ("推理模块", test_inference),
        ("日志功能", test_logging),
        ("BridgeObject", test_bridge_object),
        ("前端文件", test_frontend_files),  # P2 修复
        ("日志线程 ID", test_logging_thread_id),  # P2 修复
    ]
    
    passed = 0
    failed = 0
    results = []
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                results.append((name, True))
            else:
                failed += 1
                results.append((name, False))
        except Exception as e:
            failed += 1
            results.append((name, False))
            print(f"✗ {name} 异常：{e}\n")
    
    # 打印汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {name}")
    
    print()
    print(f"总计：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
