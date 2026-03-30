#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
拉曼光谱边缘客户端 - 后端启动脚本

功能:
- 启动 PySide6 + QWebEngine 应用
- 支持开发模式和生产模式
- 支持日志配置
- 支持调试模式

使用方法:
    # 开发模式（默认）
    python scripts/start_backend.py

    # 生产模式（禁用日志）
    python scripts/start_backend.py --prod

    # 调试模式
    python scripts/start_backend.py --debug

    # 指定日志级别
    python scripts/start_backend.py --log-level DEBUG

    # 直接运行主程序
    python run.py
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


def check_virtualenv():
    """检查是否在虚拟环境中运行"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"✅ 虚拟环境：{sys.prefix}")
        return True
    else:
        print("⚠️ 警告：未使用虚拟环境")
        return False


def check_dependencies():
    """检查依赖是否已安装"""
    required_packages = ['PySide6', 'numpy', 'scipy']
    missing = []

    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ 缺少依赖包：{', '.join(missing)}")
        print(f"   请运行：pip install {' '.join(missing)}")
        return False

    print("✅ 依赖检查通过")
    return True


def setup_environment(args):
    """设置环境变量"""
    # 日志配置
    if args.log_level:
        os.environ['RAMAN_LOG_LEVEL'] = args.log_level.upper()

    if args.log_file:
        os.environ['RAMAN_LOG_FILE'] = str(args.log_file)
    elif args.log_enabled:
        os.environ['RAMAN_LOG_ENABLED'] = 'true'

    if not args.console:
        os.environ['RAMAN_LOG_CONSOLE'] = 'false'

    if args.debug:
        os.environ['RAMAN_DEBUG'] = 'true'

    # 生产模式
    if args.prod:
        os.environ['RAMAN_LOG_ENABLED'] = 'false'
        os.environ['RAMAN_DEBUG'] = 'false'

    print("环境变量配置:")
    print(f"  - 日志级别：{os.environ.get('RAMAN_LOG_LEVEL', 'INFO')}")
    print(f"  - 日志文件：{os.environ.get('RAMAN_LOG_FILE', '自动')}")
    print(f"  - 控制台输出：{os.environ.get('RAMAN_LOG_CONSOLE', 'true')}")
    print(f"  - 调试模式：{os.environ.get('RAMAN_DEBUG', 'false')}")


def run_backend(args):
    """运行后端应用"""
    print("\n" + "=" * 60)
    print("🚀 启动拉曼光谱边缘客户端 - 后端服务")
    print("=" * 60 + "\n")

    # 设置环境变量
    setup_environment(args)

    # 切换到项目根目录
    os.chdir(ROOT_DIR)

    # 运行主程序
    main_script = ROOT_DIR / "run.py"

    if not main_script.exists():
        print(f"❌ 主程序不存在：{main_script}")
        return False

    # 使用 subprocess 运行，便于控制
    cmd = [sys.executable, str(main_script)]

    if args.no_splash:
        cmd.append("--no-splash")

    print(f"执行命令：{' '.join(cmd)}\n")

    try:
        process = subprocess.Popen(cmd, env=os.environ.copy())
        process.wait()
        return process.returncode == 0
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在关闭...")
        return True
    except Exception as e:
        print(f"❌ 启动失败：{e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='🔬 拉曼光谱边缘客户端 - 后端启动工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 开发模式（默认）
    python scripts/start_backend.py

    # 生产模式（禁用日志）
    python scripts/start_backend.py --prod

    # 调试模式
    python scripts/start_backend.py --debug

    # 指定日志级别
    python scripts/start_backend.py --log-level DEBUG

    # 禁用控制台日志
    python scripts/start_backend.py --no-console

    # 直接运行主程序（快捷方式）
    python run.py
        """
    )

    # 运行模式
    mode_group = parser.add_argument_group('运行模式')
    mode_group.add_argument('--prod', action='store_true',
                            help='生产模式（禁用日志和调试）')
    mode_group.add_argument('--debug', action='store_true',
                            help='调试模式（启用详细日志）')

    # 日志配置
    log_group = parser.add_argument_group('日志配置')
    log_group.add_argument('--log-level', type=str,
                           choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                           help='日志级别（默认：INFO）')
    log_group.add_argument('--log-file', type=str,
                           help='日志文件路径（默认：logs/raman_时间戳.log）')
    log_group.add_argument('--log-enabled', action='store_true', default=True,
                           help='启用日志文件')
    log_group.add_argument('--no-log', action='store_false', dest='log_enabled',
                           help='禁用日志文件')
    log_group.add_argument('--no-console', action='store_true',
                           help='禁用控制台日志输出')

    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('--no-splash', action='store_true',
                             help='禁用启动画面')
    other_group.add_argument('--check', action='store_true',
                             help='仅检查环境，不启动应用')

    args = parser.parse_args()

    # 检查虚拟环境
    check_virtualenv()

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 仅检查环境
    if args.check:
        print("\n✅ 环境检查通过，可以启动应用")
        sys.exit(0)

    # 运行后端
    success = run_backend(args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
