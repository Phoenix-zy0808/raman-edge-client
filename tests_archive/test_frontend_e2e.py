"""
前端 E2E 自动化测试 - 使用 Playwright

测试范围:
1. 页面加载和初始化
2. 设备连接/断开
3. 数据采集控制
4. 参数调节（积分时间、噪声水平、累加平均、平滑窗口）
5. 主题切换
6. 峰值标注
7. 数据导出
8. 谱库匹配
9. 基线校正
10. 峰面积计算

运行测试:
    pytest test_frontend_e2e.py -v

依赖:
    pip install pytest playwright
    playwright install chromium
    
注意:
    由于 ES6 模块在 file://协议下有 CORS 限制，
    部分 JavaScript 功能可能无法正常工作。
    本测试主要验证 HTML 结构和静态 UI 元素。
"""
import pytest
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright 未安装，请运行：pip install playwright && playwright install")


# 测试配置
TIMEOUT = 10000  # 10 秒超时（页面加载需要 5 秒 +）


@pytest.fixture(scope="function")
def browser_context():
    """创建浏览器上下文"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright 不可用")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()


def get_index_path():
    """获取 index.html 的绝对路径（file:// 协议）"""
    root_dir = Path(__file__).parent
    index_path = root_dir / "frontend" / "index.html"
    assert index_path.exists(), f"index.html 不存在：{index_path}"
    return f"file://{index_path}"


class TestFrontendE2E:
    """前端 E2E 测试类"""

    def test_page_loads(self, browser_context):
        """测试 1: 页面正常加载"""
        page = browser_context
        page.set_default_timeout(TIMEOUT)

        # 加载页面
        page.goto(get_index_path())

        # 检查标题
        expect(page).to_have_title("拉曼光谱边缘客户端")

        # 检查主标题
        expect(page.locator("h1")).to_contain_text("拉曼光谱边缘客户端")

        # 等待加载动画消失（index.html 中的 fallback 脚本会在 5 秒后隐藏它，但测试使用更短的超时）
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查图表容器
        expect(page.locator("#spectrum-chart")).to_be_visible()

        # 检查控制面板
        expect(page.locator(".control-panel")).to_be_visible()

        # 检查日志面板
        expect(page.locator("#log-panel")).to_be_visible()

        print("✓ 页面加载测试通过")

    def test_ui_elements_present(self, browser_context):
        """测试 2: 所有 UI 元素存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查按钮
        buttons = [
            "#btn-connect",
            "#btn-start",
            "#btn-export",
            "#btn-export-batch",
            "#btn-peak-label",
            "#btn-theme",
            "#btn-baseline",
            "#btn-peak-area",
            "#btn-library-match",
            "#btn-import",
            "#btn-history-add",
            "#btn-history-clear",
            "#btn-multi-spectrum"
        ]

        for btn_selector in buttons:
            expect(page.locator(btn_selector)).to_be_visible()

        # 检查状态栏
        expect(page.locator("#device-status")).to_be_visible()
        expect(page.locator("#acquisition-status")).to_be_visible()
        expect(page.locator("#fps-counter")).to_be_visible()

        # 检查参数输入控件
        expect(page.locator("#integration-time")).to_be_visible()
        expect(page.locator("#noise-slider")).to_be_visible()
        expect(page.locator("#accumulation-count")).to_be_visible()
        expect(page.locator("#smoothing-window")).to_be_visible()
        expect(page.locator("#device-state")).to_be_visible()

        print("✓ UI 元素存在性测试通过")

    def test_theme_toggle_button_exists(self, browser_context):
        """测试 3: 主题切换按钮存在（功能测试需要完整后端）"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查按钮存在
        btn_theme = page.locator("#btn-theme")
        expect(btn_theme).to_be_visible()
        expect(btn_theme).to_contain_text("主题")

        print("✓ 主题切换按钮存在性测试通过")

    def test_peak_labels_button_exists(self, browser_context):
        """测试 4: 峰值标注按钮存在（功能测试需要完整后端）"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查按钮存在
        btn_peak = page.locator("#btn-peak-label")
        expect(btn_peak).to_be_visible()
        expect(btn_peak).to_contain_text("峰值标注")

        print("✓ 峰值标注按钮存在性测试通过")

    def test_integration_time_input_exists(self, browser_context):
        """测试 5: 积分时间输入框存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        integration_input = page.locator("#integration-time")
        expect(integration_input).to_be_visible()

        # 检查属性
        expect(integration_input).to_have_attribute("min", "10")
        expect(integration_input).to_have_attribute("max", "10000")

        print("✓ 积分时间输入框存在性测试通过")

    def test_noise_level_slider_exists(self, browser_context):
        """测试 6: 噪声水平滑块存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        noise_slider = page.locator("#noise-slider")
        expect(noise_slider).to_be_visible()

        # 检查属性
        expect(noise_slider).to_have_attribute("min", "0")
        expect(noise_slider).to_have_attribute("max", "0.1")

        print("✓ 噪声水平滑块存在性测试通过")

    def test_log_panel_exists(self, browser_context):
        """测试 7: 日志面板存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        log_panel = page.locator("#log-panel")
        expect(log_panel).to_be_visible()

        # 检查初始日志存在
        log_entries = log_panel.locator(".log-entry")
        expect(log_entries.first).to_be_visible()

        print("✓ 日志面板存在性测试通过")

    def test_status_bar_exists(self, browser_context):
        """测试 8: 状态栏存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查设备状态
        device_status = page.locator("#device-status")
        expect(device_status).to_be_visible()
        expect(device_status).to_have_class("status-indicator disconnected")

        # 检查采集状态
        acquisition_status = page.locator("#acquisition-status")
        expect(acquisition_status).to_be_visible()
        expect(acquisition_status).to_have_class("status-indicator disconnected")

        # 检查 FPS 计数器
        fps_counter = page.locator("#fps-counter")
        expect(fps_counter).to_be_visible()
        expect(fps_counter).to_contain_text("FPS:")

        print("✓ 状态栏存在性测试通过")

    def test_multi_spectrum_button_exists(self, browser_context):
        """测试 9: 多光谱对比按钮存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查按钮存在
        btn_multi = page.locator("#btn-multi-spectrum")
        expect(btn_multi).to_be_visible()
        expect(btn_multi).to_contain_text("多谱对比")

        print("✓ 多光谱对比按钮存在性测试通过")

    def test_library_panel_exists(self, browser_context):
        """测试 10: 谱库匹配面板存在"""
        page = browser_context
        page.goto(get_index_path())
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=3500)

        # 检查谱库面板存在（默认隐藏）
        library_panel = page.locator("#library-panel")
        expect(library_panel).to_be_attached()  # 面板存在于 DOM 中

        # 检查免责声明存在
        disclaimer = page.locator(".library-disclaimer")
        expect(disclaimer).to_be_attached()
        expect(disclaimer).to_contain_text("演示数据")

        print("✓ 谱库匹配面板存在性测试通过")


def run_tests():
    """运行测试的便捷函数"""
    import subprocess
    import sys
    
    print("=" * 60)
    print("拉曼光谱边缘客户端 - 前端 E2E 测试")
    print("=" * 60)
    
    # 检查 Playwright 是否安装
    try:
        import playwright
        print("✓ Playwright 已安装")
    except ImportError:
        print("✗ Playwright 未安装")
        print("  请运行：pip install playwright")
        print("  然后运行：playwright install chromium")
        return False
    
    # 运行 pytest
    root_dir = Path(__file__).parent
    test_file = root_dir / "test_frontend_e2e.py"
    
    if not test_file.exists():
        print(f"✗ 测试文件不存在：{test_file}")
        return False
    
    print(f"\n运行测试：{test_file}")
    print("-" * 60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        cwd=str(root_dir)
    )
    
    print("-" * 60)
    if result.returncode == 0:
        print("✅ 所有前端测试通过!")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
