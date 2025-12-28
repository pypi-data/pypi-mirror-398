#!/usr/bin/env python3
"""
测试执行入口

此文件作为框架启动的入口点，所有核心逻辑都在 core 模块中。
如需更新启动逻辑，只需升级 utest-core 库即可，此文件基本不需要修改。
"""
import os
import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent))

# 从 core 模块导入启动函数
from core import run_framework

if __name__ == '__main__':
    # 调用框架启动函数，所有逻辑都在库中
    exit_code = run_framework()
    os._exit(exit_code)
