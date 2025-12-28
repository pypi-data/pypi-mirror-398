#!/usr/bin/env python3
"""
测试用例加载器

自动加载test_cases目录下的所有测试用例
"""

import os
import sys
import importlib
import logging
import traceback
from pathlib import Path
from typing import List, Type

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.test_case import TestCase, TestSuite

# 设置logger
logger = logging.getLogger(__name__)


def load_test_cases(test_names: List[str] = None, device=None) -> List[Type[TestCase]]:
    """
    自动加载test_cases目录下的所有测试用例
    
    Args:
        test_names: 指定要加载的测试用例名称列表，为None时加载所有
    
    Returns:
        List[Type[TestCase]]: 测试用例类列表
    """
    global traceback
    test_cases = []
    test_cases_dir = Path(__file__).parent.parent

    logger.info(f"正在扫描测试用例目录: {test_cases_dir}")

    # 遍历test_cases目录下的所有Python文件
    for file_path in test_cases_dir.glob("*.py"):
        if file_path.name.startswith("__") or file_path.name == "loader.py":
            continue

        logger.info(f"正在加载文件: {file_path.name}")

        try:
            # 动态导入模块
            module_name = file_path.stem
            module = importlib.import_module(f"test_cases.{module_name}")

            # 查找模块中的TestCase子类
            module_test_cases = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, TestCase) and
                        attr != TestCase):

                    # 如果指定了测试用例名称过滤，则检查是否匹配
                    if test_names is not None:
                        # 创建临时实例来获取测试用例名称
                        try:
                            temp_instance = attr(device=device)
                            test_case_name = temp_instance.name
                            if test_case_name not in test_names:
                                logger.info(f"  跳过测试用例: {attr.__name__} (名称: {test_case_name})")
                                continue
                        except Exception as e:
                            logger.warning(f"  无法创建测试用例实例 {attr.__name__}: {e}\n{traceback.format_exc()}")
                            continue

                    module_test_cases.append(attr)
                    logger.info(f"  找到测试用例: {attr.__name__}")

            if module_test_cases:
                test_cases.extend(module_test_cases)
                logger.info(f"  成功加载 {len(module_test_cases)} 个测试用例")
            else:
                logger.info(f"  未找到测试用例")

        except Exception as e:
            logger.error(f"  加载测试用例失败 {file_path.name}: {e}")
            import traceback
            logger.error(f"  错误详情: {traceback.format_exc()}")

    logger.info(f"总共加载了 {len(test_cases)} 个测试用例")
    return test_cases


def create_test_collection(test_names: List[str] = None, device=None) -> TestSuite:
    """
    创建测试用例集合，自动加载所有可用的测试用例
    
    Args:
        test_names: 指定要加载的测试用例名称列表，为None时加载所有
        
    Returns:
        TestSuite: 测试用例集合
        
    Raises:
        RuntimeError: 当没有找到任何测试用例时
    """
    logger.info("正在创建测试用例集合...")

    # 加载所有测试用例
    test_case_classes = load_test_cases(test_names, device)

    if not test_case_classes:
        logger.error("未找到任何测试用例，无法创建测试用例集合")
        raise RuntimeError("未找到任何测试用例，请检查test_cases目录下是否有有效的测试用例文件")

    # 创建测试用例集合
    collection = TestSuite(f"测试用例集合", f"包含 {len(test_case_classes)} 个测试用例的集合")

    # 为每个测试用例类创建实例
    for test_case_class in test_case_classes:
        try:
            # 检查测试用例构造函数是否支持device参数
            import inspect
            sig = inspect.signature(test_case_class.__init__)
            if 'device' in sig.parameters:
                test_case = test_case_class(device=device)
            else:
                test_case = test_case_class()
            collection.add_test_case(test_case)
            logger.info(f"添加测试用例: {test_case.name}")

        except Exception as e:
            logger.error(f"创建测试用例实例失败 {test_case_class.__name__}: {e}\n{traceback.format_exc()}")
            raise RuntimeError("创建测试用例实例失败")

    logger.info(f"测试用例集合创建完成，包含 {len(collection.test_cases)} 个测试用例")
    return collection


def list_test_cases() -> None:
    """列出所有可用的测试用例"""
    logger.info("=== 可用的测试用例 ===")
    test_cases = load_test_cases()

    if not test_cases:
        logger.warning("未找到任何测试用例")
        return

    for i, test_case_class in enumerate(test_cases, 1):
        logger.info(f"{i}. {test_case_class.__name__}")
        if hasattr(test_case_class, '__doc__') and test_case_class.__doc__:
            logger.info(f"   描述: {test_case_class.__doc__.strip()}")


if __name__ == '__main__':
    # 设置基本日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== 测试用例加载器 ===")
    list_test_cases()

    logger.info("\n=== 创建测试用例集合 ===")
    try:
        collection = create_test_collection("com.example.app")
        logger.info(f"测试用例集合创建完成，包含 {len(collection.test_cases)} 个测试用例")

        for test_case in collection.test_cases:
            logger.info(f"- {test_case.name}: {test_case.description}")
    except RuntimeError as e:
        logger.error(f"创建测试用例集合失败: {e}")
