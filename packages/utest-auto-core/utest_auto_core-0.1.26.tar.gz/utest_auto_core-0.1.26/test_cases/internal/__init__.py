#!/usr/bin/env python3
"""
测试用例包初始化文件

提供测试用例装饰器注册的便捷接口
"""

import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from .loader import load_test_cases, create_test_collection, list_test_cases

# 导出主要功能
__all__ = [
    'load_test_cases',
    'create_test_collection', 
    'list_test_cases'
]