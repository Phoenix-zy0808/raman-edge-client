"""
拉曼光谱边缘客户端 - 统一测试套件

使用方法:
    # 运行所有测试
    python -m pytest tests/ -v

    # 运行特定类型测试
    python -m pytest tests/unit/ -v       # 单元测试
    python -m pytest tests/integration/ -v  # 集成测试
    python -m pytest tests/e2e/ -v        # E2E 测试

    # 运行覆盖率
    python -m pytest tests/ --cov=backend --cov=frontend --cov-report=html

    # 快速测试（不含 E2E）
    python -m pytest tests/unit tests/integration -v

测试分类:
- unit/         : 单元测试，测试单个函数/类
- integration/  : 集成测试，测试模块间交互
- e2e/          : 端到端测试，测试完整用户流程
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 测试配置
PYTEST_CONFIG = {
    'testpaths': ['tests'],
    'addopts': [
        '-v',
        '--tb=short',
        '--strict-markers',
        '-ra',
    ],
    'markers': [
        'slow: 慢速测试',
        'integration: 集成测试',
        'e2e: 端到端测试',
        'backend: 后端测试',
        'frontend: 前端测试',
    ],
    'python_files': ['test_*.py'],
    'python_classes': ['Test*'],
    'python_functions': ['test_*'],
}


def run_tests(test_type: str = 'all', verbose: bool = True) -> bool:
    """
    运行测试套件

    Args:
        test_type: 测试类型 ('all', 'unit', 'integration', 'e2e')
        verbose: 是否显示详细输出

    Returns:
        bool: 测试是否全部通过
    """
    import pytest

    test_paths = {
        'all': ['tests/'],
        'unit': ['tests/unit/'],
        'integration': ['tests/integration/'],
        'e2e': ['tests/e2e/'],
    }

    if test_type not in test_paths:
        print(f"❌ 未知的测试类型：{test_type}")
        print(f"可用类型：{', '.join(test_paths.keys())}")
        return False

    args = PYTEST_CONFIG['addopts'].copy()
    if not verbose:
        args.remove('-v')

    args.extend(test_paths[test_type])

    print("=" * 60)
    print(f"拉曼光谱边缘客户端 - 测试套件")
    print("=" * 60)
    print(f"测试类型：{test_type}")
    print(f"测试路径：{', '.join(test_paths[test_type])}")
    print("=" * 60)

    exit_code = pytest.main(args)
    return exit_code == 0


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='运行测试套件')
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration', 'e2e'],
        default='all',
        help='测试类型'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式'
    )

    args = parser.parse_args()

    success = run_tests(test_type=args.type, verbose=not args.quiet)
    sys.exit(0 if success else 1)
