#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
拉曼光谱边缘客户端 - 一键启动脚本

功能:
- 同时启动前端开发服务器和后端应用
- 支持前后端分离开发和联调
- 支持进程管理和优雅关闭

使用方法:
    # 一键启动前后端
    python scripts/start_all.py

    # 仅启动后端
    python scripts/start_all.py --backend-only

    # 仅启动前端
    python scripts/start_all.py --frontend-only

    # 指定前端端口
    python scripts/start_all.py --frontend-port 3000

    # 生产模式
    python scripts/start_all.py --prod
"""
import sys
import os
import argparse
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional, List

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


class ProcessManager:
    """进程管理器"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理"""
        print("\n👋 收到中断信号，正在关闭所有进程...")
        self.running = False
        self.shutdown()

    def start_process(self, cmd: List[str], name: str, env=None) -> bool:
        """启动进程"""
        try:
            print(f"\n🚀 启动 {name}...")
            print(f"   命令：{' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                env=env or os.environ.copy(),
                cwd=str(ROOT_DIR)
            )

            self.processes.append(process)
            print(f"✅ {name} 已启动 (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"❌ 启动 {name} 失败：{e}")
            return False

    def shutdown(self):
        """关闭所有进程"""
        print("\n" + "=" * 60)
        print("正在关闭所有服务...")
        print("=" * 60)

        for i, process in enumerate(self.processes, 1):
            if process.poll() is None:  # 进程仍在运行
                print(f"\n[{i}/{len(self.processes)}] 关闭进程 {process.pid}...")
                process.terminate()

                # 等待进程结束
                try:
                    process.wait(timeout=5)
                    print(f"✅ 进程 {process.pid} 已正常关闭")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ 进程 {process.pid} 未响应，强制终止...")
                    process.kill()
                    process.wait()

        print("\n✅ 所有服务已关闭\n")


def check_python_env():
    """检查 Python 环境"""
    print("=" * 60)
    print("检查 Python 环境")
    print("=" * 60)

    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"✅ 虚拟环境：{sys.prefix}")
    else:
        print("⚠️ 警告：未使用虚拟环境")

    # 检查 Python 版本
    print(f"✅ Python 版本：{sys.version}")

    # 检查关键依赖
    required_packages = ['PySide6', 'numpy', 'scipy']
    missing = []

    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package} 已安装")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} 未安装")

    if missing:
        print(f"\n请运行：pip install {' '.join(missing)}")
        return False

    print()
    return True


def check_node_env():
    """检查 Node.js 环境"""
    print("=" * 60)
    print("检查 Node.js 环境")
    print("=" * 60)

    try:
        # 检查 Node.js
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Node.js 版本：{result.stdout.strip()}")
        else:
            print("❌ Node.js 未安装或版本检查失败")
            return False

        # 检查 npm
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ npm 版本：{result.stdout.strip()}")
        else:
            print("⚠️ npm 版本检查失败")

        # 检查前端 node_modules
        node_modules_dir = ROOT_DIR / 'frontend' / 'node_modules'
        if node_modules_dir.exists():
            print("✅ frontend/node_modules 已安装")
        else:
            print("⚠️ frontend/node_modules 不存在")
            print("   请运行：cd frontend && npm install")

        print()
        return True

    except FileNotFoundError:
        print("❌ Node.js 未安装")
        print("   请从 https://nodejs.org/ 下载安装")
        return False
    except Exception as e:
        print(f"❌ 检查失败：{e}")
        return False


def start_backend(args, env):
    """启动后端"""
    backend_script = ROOT_DIR / 'scripts' / 'start_backend.py'

    cmd = [sys.executable, str(backend_script)]

    if args.prod:
        cmd.append('--prod')
    if args.debug:
        cmd.append('--debug')
    if args.log_level:
        cmd.extend(['--log-level', args.log_level])
    if args.no_splash:
        cmd.append('--no-splash')

    return cmd


def start_frontend(args):
    """启动前端"""
    frontend_script = ROOT_DIR / 'scripts' / 'start_frontend.js'

    cmd = ['node', str(frontend_script)]

    if args.frontend_port:
        cmd.extend(['--port', str(args.frontend_port)])
    if args.prod:
        cmd.append('--prod')
    if args.open:
        cmd.append('--open')

    return cmd


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='🔬 拉曼光谱边缘客户端 - 一键启动工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 一键启动前后端
    python scripts/start_all.py

    # 仅启动后端
    python scripts/start_all.py --backend-only

    # 仅启动前端
    python scripts/start_all.py --frontend-only

    # 指定前端端口
    python scripts/start_all.py --frontend-port 3000

    # 生产模式
    python scripts/start_all.py --prod

    # 调试模式
    python scripts/start_all.py --debug
        """
    )

    # 运行模式
    mode_group = parser.add_argument_group('运行模式')
    mode_group.add_argument('--backend-only', action='store_true',
                            help='仅启动后端')
    mode_group.add_argument('--frontend-only', action='store_true',
                            help='仅启动前端')
    mode_group.add_argument('--prod', action='store_true',
                            help='生产模式')
    mode_group.add_argument('--debug', action='store_true',
                            help='调试模式')

    # 前端配置
    frontend_group = parser.add_argument_group('前端配置')
    frontend_group.add_argument('--frontend-port', type=int, default=8080,
                                help='前端端口（默认：8080）')
    frontend_group.add_argument('--open', action='store_true',
                                help='启动后自动打开浏览器')

    # 后端配置
    backend_group = parser.add_argument_group('后端配置')
    backend_group.add_argument('--log-level', type=str,
                               choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                               help='日志级别')
    backend_group.add_argument('--no-splash', action='store_true',
                               help='禁用启动画面')

    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('--check-only', action='store_true',
                             help='仅检查环境，不启动应用')

    args = parser.parse_args()

    # 打印横幅
    print("\n" + "=" * 60)
    print("🔬 拉曼光谱边缘客户端 - 启动工具")
    print("=" * 60 + "\n")

    # 检查环境
    python_ok = check_python_env()
    node_ok = check_node_env()

    if args.check_only:
        print("\n✅ 环境检查完成")
        sys.exit(0 if (python_ok and node_ok) else 1)

    if not python_ok:
        print("\n❌ Python 环境检查失败")
        sys.exit(1)

    # 创建进程管理器
    manager = ProcessManager()

    # 设置环境变量
    env = os.environ.copy()

    # 启动服务
    try:
        # 仅前端模式
        if args.frontend_only:
            if not node_ok:
                print("\n❌ Node.js 环境检查失败")
                sys.exit(1)

            cmd = start_frontend(args)
            if not manager.start_process(cmd, "前端开发服务器", env):
                sys.exit(1)

        # 仅后端模式
        elif args.backend_only:
            if not python_ok:
                print("\n❌ Python 环境检查失败")
                sys.exit(1)

            cmd = start_backend(args, env)
            if not manager.start_process(cmd, "后端应用", env):
                sys.exit(1)

        # 前后端同时启动
        else:
            if not node_ok:
                print("\n⚠️ Node.js 环境不可用，仅启动后端")
                cmd = start_backend(args, env)
                if not manager.start_process(cmd, "后端应用", env):
                    sys.exit(1)
            else:
                # 先启动前端
                cmd = start_frontend(args)
                if not manager.start_process(cmd, "前端开发服务器", env):
                    sys.exit(1)

                # 等待前端启动
                time.sleep(2)

                # 启动后端
                cmd = start_backend(args, env)
                if not manager.start_process(cmd, "后端应用", env):
                    sys.exit(1)

        # 等待进程结束
        print("\n" + "=" * 60)
        print("✅ 所有服务已启动")
        print("=" * 60)
        print("\n按 Ctrl+C 停止所有服务\n")

        # 主循环
        while manager.running:
            time.sleep(1)

            # 检查进程状态
            all_stopped = True
            for process in manager.processes:
                if process.poll() is None:
                    all_stopped = False
                    break

            if all_stopped:
                print("\n⚠️ 所有进程已停止")
                break

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ 启动失败：{e}")
        manager.shutdown()
        sys.exit(1)

    # 关闭所有进程
    manager.shutdown()


if __name__ == '__main__':
    main()
