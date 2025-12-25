# -*- coding: utf-8 -*-
"""
用例收集器

静态分析测试用例文件，提取用例信息和步骤信息，无需执行代码
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class TestCaseCollector:
    """测试用例收集器 - 使用AST静态分析提取用例信息"""

    def __init__(self, test_cases_dir: str = "test_cases", exclude_files: List[str] = None):
        """
        初始化用例收集器
        
        Args:
            test_cases_dir: 测试用例目录路径
            exclude_files: 要排除的文件名列表（如 ["user_tests_0.py", "user_tests_1.py"]）
        """
        self.test_cases_dir = Path(test_cases_dir)
        # 默认排除的文件列表
        default_exclude = ["user_tests_0.py", "user_tests_1.py", "video_test_demo.py", "test_demo_simple.py"]
        self.exclude_files = exclude_files if exclude_files is not None else default_exclude
        self.test_cases: List[Dict[str, Any]] = []

    def collect(self) -> List[Dict[str, Any]]:
        """
        收集所有测试用例信息
        
        Returns:
            List[Dict[str, Any]]: 用例信息列表，每个用例包含：
                - name: 用例名称
                - description: 用例描述
                - class_name: 类名
                - file_path: 文件路径
                - steps: 步骤列表，每个步骤包含 step_name 和 description
        """
        self.test_cases = []

        if not self.test_cases_dir.exists():
            return self.test_cases

        # 遍历test_cases目录下的所有Python文件
        for file_path in self.test_cases_dir.glob("*.py"):
            # 跳过特殊文件和排除的文件
            if (file_path.name.startswith("__") or
                    file_path.name == "loader.py" or
                    file_path.name in self.exclude_files):
                continue

            try:
                # 解析文件中的测试用例
                test_cases_in_file = self._parse_file(file_path)
                self.test_cases.extend(test_cases_in_file)
            except Exception as e:
                print(f"⚠️ 解析文件失败 {file_path.name}: {e}")
                continue

        return self.test_cases

    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析单个文件，提取测试用例信息
        
        Args:
            file_path: Python文件路径
            
        Returns:
            List[Dict[str, Any]]: 该文件中的用例信息列表
        """
        test_cases = []

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content, filename=str(file_path))

            # 查找所有TestCase子类
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 检查是否是TestCase的子类
                    if self._is_test_case_class(node):
                        # 提取用例信息
                        test_case_info = self._extract_test_case_info(node, file_path, content)
                        if test_case_info:
                            test_cases.append(test_case_info)

        except SyntaxError as e:
            print(f"⚠️ 文件语法错误 {file_path.name}: {e}")
        except Exception as e:
            print(f"⚠️ 解析文件异常 {file_path.name}: {e}")

        return test_cases

    def _is_test_case_class(self, node: ast.ClassDef) -> bool:
        """
        判断类是否是TestCase的子类
        
        Args:
            node: 类定义节点
            
        Returns:
            bool: 是否是TestCase子类
        """
        # 检查基类
        for base in node.bases:
            # 检查是否是直接继承TestCase
            if isinstance(base, ast.Name) and base.id == "TestCase":
                return True
            # 检查是否是继承自core.test_case.TestCase
            if isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Attribute):
                    # core.test_case.TestCase
                    if (base.value.attr == "test_case" and
                            isinstance(base.value.value, ast.Name) and
                            base.value.value.id == "core" and
                            base.attr == "TestCase"):
                        return True
                elif isinstance(base.value, ast.Name):
                    # test_case.TestCase
                    if base.value.id == "test_case" and base.attr == "TestCase":
                        return True

        return False

    def _extract_test_case_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Optional[Dict[str, Any]]:
        """
        提取测试用例信息
        
        Args:
            node: 类定义节点
            file_path: 文件路径
            content: 文件内容（用于提取步骤信息）
            
        Returns:
            Dict[str, Any]: 用例信息，如果提取失败返回None
        """
        test_case_info = {
            "class_name": node.name,
            "file_path": str(file_path),
            "file_name": file_path.name,
            "name": None,
            "description": "",
            "steps": []
        }

        # 提取__init__方法中的用例名称和描述
        init_info = self._extract_init_info(node)
        if init_info:
            test_case_info["name"] = init_info.get("name")
            test_case_info["description"] = init_info.get("description", "")

        # 提取run_test方法中的步骤信息
        steps = self._extract_steps(node, content)
        test_case_info["steps"] = steps

        # 如果没有名称，使用类名
        if not test_case_info["name"]:
            test_case_info["name"] = node.name

        return test_case_info

    def _extract_init_info(self, node: ast.ClassDef) -> Optional[Dict[str, str]]:
        """
        从__init__方法中提取用例名称和描述
        
        Args:
            node: 类定义节点
            
        Returns:
            Dict[str, str]: 包含name和description的字典
        """
        init_info = {"name": None, "description": ""}

        # 查找__init__方法
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                # 查找super().__init__调用
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Call):
                        # 检查是否是super().__init__调用
                        # 支持 super().__init__(...) 和 super(ClassName, self).__init__(...)
                        is_super_init = False

                        if isinstance(stmt.func, ast.Attribute) and stmt.func.attr == "__init__":
                            # 检查是否是super()调用
                            if isinstance(stmt.func.value, ast.Call):
                                if isinstance(stmt.func.value.func, ast.Name) and stmt.func.value.func.id == "super":
                                    is_super_init = True
                                elif isinstance(stmt.func.value.func, ast.Call):
                                    # super(ClassName, self)的情况
                                    if (isinstance(stmt.func.value.func.func, ast.Name) and
                                            stmt.func.value.func.func.id == "super"):
                                        is_super_init = True

                        if is_super_init:
                            # 提取参数
                            for i, arg in enumerate(stmt.args):
                                if i == 0:
                                    # 第一个参数通常是name
                                    if isinstance(arg, ast.Constant):
                                        init_info["name"] = arg.value
                                    elif hasattr(ast, 'Str') and isinstance(arg, ast.Str):  # Python < 3.8兼容
                                        init_info["name"] = arg.s
                                elif i == 1:
                                    # 第二个参数通常是description
                                    if isinstance(arg, ast.Constant):
                                        init_info["description"] = arg.value
                                    elif hasattr(ast, 'Str') and isinstance(arg, ast.Str):  # Python < 3.8兼容
                                        init_info["description"] = arg.s

                            # 检查关键字参数
                            for keyword in stmt.keywords:
                                if keyword.arg == "name":
                                    if isinstance(keyword.value, ast.Constant):
                                        init_info["name"] = keyword.value.value
                                    elif hasattr(ast, 'Str') and isinstance(keyword.value, ast.Str):  # Python < 3.8兼容
                                        init_info["name"] = keyword.value.s
                                elif keyword.arg == "description":
                                    if isinstance(keyword.value, ast.Constant):
                                        init_info["description"] = keyword.value.value
                                    elif hasattr(ast, 'Str') and isinstance(keyword.value, ast.Str):  # Python < 3.8兼容
                                        init_info["description"] = keyword.value.s

                break

        return init_info

    def _extract_steps(self, node: ast.ClassDef, content: str) -> List[Dict[str, str]]:
        """
        从类中提取步骤信息（从所有方法中查找，优先run_test方法）
        
        Args:
            node: 类定义节点
            content: 文件内容（用于更精确地提取步骤描述）
            
        Returns:
            List[Dict[str, str]]: 步骤列表，每个步骤包含step_name和description
        """
        steps = []

        # 优先从run_test方法中提取步骤
        run_test_steps = self._extract_steps_from_method(node, "run_test")
        if run_test_steps:
            steps.extend(run_test_steps)
        else:
            # 如果run_test中没有步骤，从所有方法中提取（排除特殊方法）
            excluded_methods = {"__init__", "setup", "teardown", "run_test"}
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name not in excluded_methods:
                    method_steps = self._extract_steps_from_method(node, item.name)
                    steps.extend(method_steps)

        return steps

    def _extract_steps_from_method(self, node: ast.ClassDef, method_name: str) -> List[Dict[str, str]]:
        """
        从指定方法中提取步骤信息
        
        Args:
            node: 类定义节点
            method_name: 方法名称
            
        Returns:
            List[Dict[str, str]]: 步骤列表
        """
        steps = []

        # 查找指定方法
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                # 查找所有start_step调用
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Call):
                        # 检查是否是self.start_step调用
                        if (isinstance(stmt.func, ast.Attribute) and
                                stmt.func.attr == "start_step"):
                            step_info = {"step_name": "", "description": ""}

                            # 提取参数
                            if len(stmt.args) >= 1:
                                # 第一个参数是step_name
                                if isinstance(stmt.args[0], ast.Constant):
                                    step_info["step_name"] = str(stmt.args[0].value)
                                elif hasattr(ast, 'Str') and isinstance(stmt.args[0], ast.Str):  # Python < 3.8兼容
                                    step_info["step_name"] = str(stmt.args[0].s)

                            if len(stmt.args) >= 2:
                                # 第二个参数是description
                                if isinstance(stmt.args[1], ast.Constant):
                                    step_info["description"] = str(stmt.args[1].value)
                                elif hasattr(ast, 'Str') and isinstance(stmt.args[1], ast.Str):  # Python < 3.8兼容
                                    step_info["description"] = str(stmt.args[1].s)

                            # 检查关键字参数
                            for keyword in stmt.keywords:
                                if keyword.arg == "step_name":
                                    if isinstance(keyword.value, ast.Constant):
                                        step_info["step_name"] = str(keyword.value.value)
                                    elif hasattr(ast, 'Str') and isinstance(keyword.value, ast.Str):  # Python < 3.8兼容
                                        step_info["step_name"] = str(keyword.value.s)
                                elif keyword.arg == "description":
                                    if isinstance(keyword.value, ast.Constant):
                                        step_info["description"] = str(keyword.value.value)
                                    elif hasattr(ast, 'Str') and isinstance(keyword.value, ast.Str):  # Python < 3.8兼容
                                        step_info["description"] = str(keyword.value.s)

                            if step_info["step_name"]:
                                steps.append(step_info)

                break

        return steps

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 包含所有用例信息的字典
        """
        return {
            "total": len(self.test_cases),
            "test_cases": self.test_cases
        }

    def to_json(self, output_path: Optional[str] = None) -> str:
        """
        输出为JSON格式
        
        Args:
            output_path: 输出文件路径，如果为None则返回JSON字符串
            
        Returns:
            str: JSON字符串或文件路径
        """
        data = self.to_dict()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return output_path
        else:
            return json_str

    def print_summary(self):
        """打印用例汇总信息"""
        print(f"\n{'=' * 60}")
        print(f"测试用例汇总")
        print(f"{'=' * 60}")
        print(f"总计: {len(self.test_cases)} 个用例\n")

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"{i}. {test_case['name']}")
            print(f"   类名: {test_case['class_name']}")
            print(f"   文件: {test_case['file_name']}")
            if test_case['description']:
                print(f"   描述: {test_case['description']}")
            print(f"   步骤数: {len(test_case['steps'])}")
            if test_case['steps']:
                print(f"   步骤列表:")
                for j, step in enumerate(test_case['steps'], 1):
                    print(f"     {j}. {step['step_name']}")
                    if step['description']:
                        print(f"        描述: {step['description']}")
            print()

    def print_detailed(self):
        """打印详细用例信息"""
        self.print_summary()

        print(f"\n{'=' * 60}")
        print(f"详细用例信息")
        print(f"{'=' * 60}\n")

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"{'=' * 60}")
            print(f"用例 {i}: {test_case['name']}")
            print(f"{'=' * 60}")
            print(f"类名: {test_case['class_name']}")
            print(f"文件: {test_case['file_path']}")
            if test_case['description']:
                print(f"描述: {test_case['description']}")
            print(f"\n步骤信息 ({len(test_case['steps'])} 个步骤):")

            if test_case['steps']:
                for j, step in enumerate(test_case['steps'], 1):
                    print(f"\n  步骤 {j}: {step['step_name']}")
                    if step['description']:
                        print(f"    描述: {step['description']}")
            else:
                print("  (未找到步骤信息)")
            print()


def collect_test_cases(test_cases_dir: str = "test_cases", exclude_files: List[str] = None) -> TestCaseCollector:
    """
    收集测试用例的便捷函数
    
    Args:
        test_cases_dir: 测试用例目录路径
        exclude_files: 要排除的文件名列表（如 ["user_tests_0.py", "user_tests_1.py"]）
        
    Returns:
        TestCaseCollector: 用例收集器实例
    """
    collector = TestCaseCollector(test_cases_dir, exclude_files)
    collector.collect()
    return collector


if __name__ == "__main__":
    # 测试用例收集器
    collector = collect_test_cases()
    collector.print_detailed()
