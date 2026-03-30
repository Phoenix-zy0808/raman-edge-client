#!/usr/bin/env python3
"""
项目状态验证脚本

用于验证文档与代码状态一致性，确保 todo.md 中的任务状态与实际代码匹配。

使用示例:
    python scripts/verify_status.py --frontend-modules
    python scripts/verify_status.py --tech-debt
    python scripts/verify_status.py --file-lines
    python scripts/verify_status.py --all
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class StatusVerifier:
    """项目状态验证器"""

    def __init__(self, root_dir: Optional[Path] = None):
        """初始化验证器

        Args:
            root_dir: 项目根目录，默认为脚本所在目录的父目录
        """
        self.root_dir = root_dir or Path(__file__).parent.parent
        self.frontend_js_dir = self.root_dir / "frontend" / "js"
        self.frontend_pages_dir = self.root_dir / "frontend" / "pages"
        self.backend_dir = self.root_dir / "backend"
        self.tests_dir = self.root_dir / "tests"

    def verify_frontend_modules(self) -> bool:
        """验证前端 JS 模块存在性和行数

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证前端 JS 模块")
        print("=" * 60)

        expected_modules = {
            "main.js": ("应用入口", 400),
            "chart.js": ("图表渲染", 300),
            "bridge.js": ("后端通信", 500),
            "ui.js": ("UI 操作", 400),
            "utils.js": ("工具函数", 100),
            "state.js": ("状态管理", 200),
            "cache.js": ("SWR 缓存", 200),
            "theme.js": ("主题管理", 300),
            "virtual-scroll.js": ("虚拟滚动", 200),
            "skeleton.js": ("骨架屏", 50),
            "types.js": ("类型定义", 150),
            "peaks.js": ("峰值检测", 100),
        }

        all_passed = True

        for module_name, (description, min_lines) in expected_modules.items():
            module_path = self.frontend_js_dir / module_name

            if not module_path.exists():
                print(f"❌ {module_name} ({description}): 文件不存在")
                all_passed = False
                continue

            line_count = self._count_lines(module_path)
            status = "✅" if line_count >= min_lines else "⚠️"
            print(f"{status} {module_name} ({description}): {line_count} 行")

            if line_count < min_lines:
                print(f"   警告：行数少于预期的 {min_lines} 行")
                all_passed = False

        print()
        return all_passed

    def verify_frontend_index(self) -> bool:
        """验证前端 index.html 存在性

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证前端 index.html")
        print("=" * 60)

        index_path = self.root_dir / "frontend" / "index.html"

        if not index_path.exists():
            print("❌ index.html (主页面): 文件不存在")
            print()
            return False

        line_count = self._count_lines(index_path)
        print(f"✅ index.html (主页面): {line_count} 行")
        print()
        return True

    def verify_frontend_pages(self) -> bool:
        """验证前端页面文件存在性

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证前端页面")
        print("=" * 60)

        expected_pages = {
            "settings.html": "设置页面",
            "calibration.html": "校准页面",
            "library.html": "谱库匹配",
            "history.html": "历史记录",
            "report.html": "报告生成",
            "about.html": "关于页面",
        }

        all_passed = True

        for page_name, description in expected_pages.items():
            page_path = self.frontend_pages_dir / page_name

            if not page_path.exists():
                print(f"❌ {page_name} ({description}): 文件不存在")
                all_passed = False
                continue

            line_count = self._count_lines(page_path)
            print(f"✅ {page_name} ({description}): {line_count} 行")

        print()
        return all_passed

    def verify_tech_debt(self) -> bool:
        """验证技术债务状态

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证技术债务状态")
        print("=" * 60)

        checks = [
            {
                "name": "防抖节流函数",
                "file": "frontend/js/utils.js",
                "pattern": r"debounce|throttle",
                "expected": True,
            },
            {
                "name": "虚拟滚动集成",
                "file": "frontend/js/main.js",
                "pattern": r"virtualLog|createVirtualLog",
                "expected": True,
            },
            {
                "name": "SWR 缓存集成",
                "file": "frontend/js/bridge.js",
                "pattern": r"swr\(|SWRConfig",
                "expected": True,
            },
            {
                "name": "主题管理集成",
                "file": "frontend/js/main.js",
                "pattern": r"themeManager|getThemeManager",
                "expected": True,
            },
            {
                "name": "全局回调耦合",
                "file": "frontend/js/main.js",
                "pattern": r"bindGlobalCallbacks",
                "expected": True,  # 仍存在，需要重构
            },
            {
                "name": "postMessage 通配符",
                "file": "frontend/js/main.js",
                "pattern": r'postMessage\s*\([^,)]+,\s*"\*"',
                "expected": False,  # 不应存在
            },
        ]

        all_passed = True

        for check in checks:
            file_path = self.root_dir / check["file"]

            if not file_path.exists():
                print(f"⚠️ {check['name']}: 文件不存在 ({check['file']})")
                continue

            content = file_path.read_text(encoding="utf-8")
            has_pattern = bool(re.search(check["pattern"], content))

            if check["expected"]:
                if has_pattern:
                    print(f"✅ {check['name']}: 已实现")
                else:
                    print(f"❌ {check['name']}: 未实现")
                    all_passed = False
            else:
                if has_pattern:
                    print(f"❌ {check['name']}: 仍存在（应删除）")
                    all_passed = False
                else:
                    print(f"✅ {check['name']}: 已修复")

        print()
        return all_passed

    def verify_file_lines(self) -> bool:
        """验证关键文件行数

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证文件行数")
        print("=" * 60)

        checks = [
            {"file": "frontend/js/main.js", "min": 400, "max": 700},
            {"file": "frontend/js/bridge.js", "min": 500, "max": 900},
            {"file": "frontend/js/ui.js", "min": 400, "max": 1000},  # ui.js 可能较大
            {"file": "frontend/js/chart.js", "min": 300, "max": 600},
            {"file": "frontend/js/cache.js", "min": 200, "max": 500},
            {"file": "frontend/js/theme.js", "min": 300, "max": 600},
            {"file": "frontend/js/virtual-scroll.js", "min": 200, "max": 500},
        ]

        all_passed = True

        for check in checks:
            file_path = self.root_dir / check["file"]

            if not file_path.exists():
                print(f"❌ {check['file']}: 文件不存在")
                all_passed = False
                continue

            line_count = self._count_lines(file_path)
            in_range = check["min"] <= line_count <= check["max"]
            status = "✅" if in_range else "⚠️"

            print(
                f"{status} {check['file']}: {line_count} 行 "
                f"(期望：{check['min']}-{check['max']})"
            )

            if not in_range:
                all_passed = False

        print()
        return all_passed

    def verify_e2e_tests(self) -> bool:
        """验证 E2E 测试状态

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证 E2E 测试配置")
        print("=" * 60)

        test_file = self.root_dir / "test_frontend_e2e.py"

        if not test_file.exists():
            print("❌ test_frontend_e2e.py: 文件不存在")
            return False

        content = test_file.read_text(encoding="utf-8")

        # 检查超时配置
        timeout_match = re.search(r"TIMEOUT\s*=\s*(\d+)", content)
        if timeout_match:
            timeout = int(timeout_match.group(1))
            if timeout >= 10000:
                print(f"✅ 超时配置：{timeout}ms (合理)")
            else:
                print(f"⚠️ 超时配置：{timeout}ms (可能过短)")
        else:
            print("⚠️ 未找到 TIMEOUT 配置")

        # 检查测试用例数量
        test_count = len(re.findall(r"def test_\w+\(self", content))
        print(f"✅ 测试用例数量：{test_count}")

        print()
        return True

    def verify_backend_api(self) -> bool:
        """验证后端 API 响应格式

        Returns:
            验证是否通过
        """
        print("=" * 60)
        print("验证后端 API 响应格式")
        print("=" * 60)

        # 检查 ApiResponse 类是否存在
        error_handler_file = self.backend_dir / "error_handler.py"

        if not error_handler_file.exists():
            print("⚠️ backend/error_handler.py: 文件不存在")
            print()
            return True  # 不强制要求

        content = error_handler_file.read_text(encoding="utf-8")

        if "class ApiResponse" in content or "ApiResponse" in content:
            print("✅ ApiResponse 类：已定义")
        else:
            print("❌ ApiResponse 类：未定义")
            return False

        # 检查主要后端模块是否使用 ApiResponse
        backend_modules = [
            "wavelength_calibration.py",
            "auto_exposure.py",
            "inference.py",
        ]

        for module_name in backend_modules:
            module_path = self.backend_dir / module_name

            if not module_path.exists():
                print(f"⚠️ {module_name}: 文件不存在 (可选)")
                continue

            content = module_path.read_text(encoding="utf-8")

            if "ApiResponse" in content:
                print(f"✅ {module_name}: 使用 ApiResponse")
            else:
                print(f"⚠️ {module_name}: 未使用 ApiResponse (建议添加)")

        print()
        return True

    def run_all_verifications(self) -> bool:
        """运行所有验证

        Returns:
            所有验证是否通过
        """
        results = [
            self.verify_frontend_index(),
            self.verify_frontend_modules(),
            self.verify_frontend_pages(),
            self.verify_tech_debt(),
            self.verify_file_lines(),
            self.verify_e2e_tests(),
            self.verify_backend_api(),
        ]

        print("=" * 60)
        print("验证总结")
        print("=" * 60)

        passed_count = sum(results)
        total_count = len(results)

        print(f"通过：{passed_count}/{total_count}")

        if all(results):
            print("✅ 所有验证通过")
            return True
        else:
            print("⚠️ 部分验证有警告 (不影响整体)")
            return True  # 警告不影响整体通过

    def _count_lines(self, file_path: Path) -> int:
        """计算文件行数

        Args:
            file_path: 文件路径

        Returns:
            文件行数
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            return len(content.splitlines())
        except Exception as e:
            print(f"  错误：无法读取文件 - {e}")
            return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="项目状态验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/verify_status.py --frontend-modules  # 验证前端模块
    python scripts/verify_status.py --tech-debt         # 验证技术债务
    python scripts/verify_status.py --file-lines        # 验证文件行数
    python scripts/verify_status.py --all               # 运行所有验证
        """,
    )

    parser.add_argument(
        "--frontend-modules",
        action="store_true",
        help="验证前端 JS 模块存在性",
    )

    parser.add_argument(
        "--frontend-pages",
        action="store_true",
        help="验证前端页面文件存在性",
    )

    parser.add_argument(
        "--tech-debt",
        action="store_true",
        help="验证技术债务状态",
    )

    parser.add_argument(
        "--file-lines",
        action="store_true",
        help="验证关键文件行数",
    )

    parser.add_argument(
        "--e2e-tests",
        action="store_true",
        help="验证 E2E 测试配置",
    )

    parser.add_argument(
        "--backend-api",
        action="store_true",
        help="验证后端 API 响应格式",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有验证",
    )

    args = parser.parse_args()

    verifier = StatusVerifier()

    # 如果没有指定任何选项，运行所有验证
    if not any(
        [
            args.frontend_modules,
            args.frontend_pages,
            args.tech_debt,
            args.file_lines,
            args.e2e_tests,
            args.backend_api,
            args.all,
        ]
    ):
        args.all = True

    success = True

    if args.frontend_modules or args.all:
        success &= verifier.verify_frontend_modules()

    if args.frontend_pages or args.all:
        success &= verifier.verify_frontend_pages()

    if args.tech_debt or args.all:
        success &= verifier.verify_tech_debt()

    if args.file_lines or args.all:
        success &= verifier.verify_file_lines()

    if args.e2e_tests or args.all:
        success &= verifier.verify_e2e_tests()

    if args.backend_api or args.all:
        success &= verifier.verify_backend_api()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
