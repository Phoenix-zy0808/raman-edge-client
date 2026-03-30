"""
启动脚本 - 用于开发和测试
"""
import sys
import os

# 确保使用虚拟环境
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"使用虚拟环境：{sys.prefix}")
else:
    print("警告：未使用虚拟环境")

# 启动应用
from main import main

if __name__ == '__main__':
    main()
