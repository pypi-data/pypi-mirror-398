#!/usr/bin/env python3
"""
QTAF风格的测试运行器

提供简洁易用的测试执行接口
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager, FrameworkConfig
from core.device_manager import DeviceManager
from core.test_case import TestCase, TestSuite, TestResult, TestStatus
from core.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class TestRunner:
    """测试运行器"""

    def __init__(self, config: Union[FrameworkConfig, str, None] = None, log_file_path: str = None):
        """
        初始化测试运行器
        
        Args:
            config: 配置对象、配置文件路径或None（使用默认配置）
            log_file_path: 日志文件路径，用于UBox日志输出
        """
        self.config_manager = ConfigManager()

        if isinstance(config, str):
            # 配置文件路径
            self.config = self.config_manager.load_config(config)
        elif isinstance(config, FrameworkConfig):
            # 配置对象
            self.config = config
        else:
            # 使用默认配置
            self.config = self.config_manager.load_config()

        self.device_manager: Optional[DeviceManager] = None
        self.device = None  # 直接存储UBox设备对象
        self.test_context = {}
        # 测试结果
        self.test_results: List[TestResult] = []
        # 全局监控结果（ANR/Crash监控等）
        self.global_monitor_result: Optional[Dict[str, Any]] = None
        # 报告生成器
        self.report_generator: Optional[ReportGenerator] = None
        # 执行开始时间（用于在test_results为空时也能获取执行时间范围）
        self.execution_start_time: Optional[datetime] = None
        # 日志文件路径
        self.log_file_path = log_file_path
        # 错误信息收集器（用于在报告中显示失败原因）
        self.error_summary: List[str] = []

    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()

    def initialize(self) -> None:
        """初始化测试运行器"""
        try:
            logger.info("初始化测试运行器...")

            # 记录执行开始时间
            self.execution_start_time = datetime.now()

            # 初始化设备管理器
            self.device_manager = DeviceManager(self.config.ubox.__dict__)

            # 使用传入的日志文件路径初始化UBox
            self.device_manager.initialize_ubox(self.log_file_path)

            # 获取UBox设备对象（直接暴露，不封装）
            self.device = self.device_manager.get_device(self.config.device)

            # 初始化报告生成器（使用默认配置，输出位置将在generate_report时设置）
            self.report_generator = None  # 延迟初始化

            logger.info("测试运行器初始化完成")

        except Exception as e:
            logger.error(f"测试运行器初始化失败: {e}\n{traceback.format_exc()}")
            raise

    def _create_test_case_directories(self, test_case: TestCase) -> Dict[str, str]:
        """为测试用例创建具体的目录结构"""
        # 直接使用测试用例名称
        case_name = test_case.name

        # 从测试上下文获取基础路径
        test_result_dir = self.test_context.get('test_result_dir', './test_result')
        case_base_dir = self.test_context.get('case_base_dir', os.path.join(test_result_dir, 'case'))
        log_base_dir = self.test_context.get('log_base_dir', os.path.join(test_result_dir, 'log'))

        # 创建用例特定的目录
        case_dir = os.path.join(case_base_dir, case_name)
        case_pic_dir = os.path.join(case_base_dir, case_name, 'pic')
        log_dir = os.path.join(log_base_dir, case_name)

        # 创建目录结构
        os.makedirs(case_dir, exist_ok=True)
        os.makedirs(case_pic_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        # 返回用例特定的目录信息，而不是更新全局context
        case_directories = {
            'case_dir': case_dir,
            'log_dir': log_dir,
            'pic_dir': case_pic_dir,
        }

        logger.info(f"为测试用例 {test_case.name} 创建目录: {case_dir}")
        return case_directories

    def cleanup(self) -> None:
        """清理资源"""
        try:
            logger.info("清理测试运行器资源...")

            # 停止设备的事件处理器（如果有）
            if self.device and hasattr(self.device, 'handler'):
                try:
                    event_handler = self.device.handler
                    if hasattr(event_handler, 'stop'):
                        event_handler.stop()
                        logger.info("事件处理器已停止")
                except Exception as handler_e:
                    logger.warning(f"停止事件处理器异常: {handler_e}")

            # 关闭设备
            if self.device:
                try:
                    if hasattr(self.device, 'release'):
                        self.device.release()
                    elif hasattr(self.device, 'close'):
                        self.device.close()
                    logger.info("设备已关闭")
                except Exception as device_e:
                    logger.warning(f"关闭设备异常: {device_e}")

            # 关闭设备管理器
            if self.device_manager:
                try:
                    self.device_manager.close()
                    logger.info("设备管理器已关闭")
                except Exception as mgr_e:
                    logger.warning(f"关闭设备管理器异常: {mgr_e}")

            logger.info("测试运行器资源清理完成")

        except Exception as e:
            logger.error(f"测试运行器资源清理失败: {e}\n{traceback.format_exc()}")

    def run_test_case(self, test_case: TestCase) -> TestResult:
        """
        运行单个测试用例
        
        Args:
            test_case: 测试用例
            
        Returns:
            TestResult: 测试结果
        """
        logger.info(f"开始运行测试用例: {test_case.name}")

        try:
            # 为当前测试用例创建独立的目录结构
            case_directories = self._create_test_case_directories(test_case)
            test_context = self.test_context.copy()
            test_context.update({
                'case_dir': case_directories['case_dir'],
                'log_dir': case_directories['log_dir'],
                'pic_dir': case_directories['pic_dir'],
            })

            # 应用截图配置
            test_case.apply_screenshot_config(
                screenshot_on_failure=self.config.test.screenshot_on_failure,
                screenshot_on_success=self.config.test.screenshot_on_success
            )

            # 执行测试用例
            result = test_case.execute(self.device, test_context)
            logger.info(f"测试用例执行完成: {test_case.name}, 状态: {result.status}")
            return result

        except Exception as e:
            logger.error(f"测试用例执行异常: {test_case.name}, 错误: {e}\n{traceback.format_exc()}")
            # 创建错误结果
            error_result = TestResult(
                test_name=test_case.name,
                status=TestStatus.ERROR,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            return error_result

    def run_test_suite(self, test_suite: TestSuite) -> List[TestResult]:
        """
        运行测试套件
        
        Args:
            test_suite: 测试套件
            
        Returns:
            List[TestResult]: 测试结果列表
        """
        if test_suite is None:
            logger.info("无匹配用例，结束任务")
            return []
        logger.info(f"开始运行测试套件: {test_suite.name}")

        results = []

        try:
            # 逐个执行测试用例，每个用例都会创建自己的目录
            for test_case in test_suite.test_cases:
                result = self.run_test_case(test_case)
                results.append(result)

            # 保存测试结果
            self.test_results.extend(results)

            logger.info(f"测试套件执行完成: {test_suite.name}, 共 {len(results)} 个测试用例")
            return results

        except Exception as e:
            logger.error(f"测试套件执行异常: {test_suite.name}, 错误: {e}\n{traceback.format_exc()}")
            raise

    def create_initial_report(self, output_path: Optional[str] = None) -> str:
        """
        创建初始状态的JSON报告文件
        
        Args:
            output_path: 输出路径，为None时使用配置中的路径
            
        Returns:
            str: 初始JSON报告文件路径
        """
        # 延迟初始化报告生成器
        if not self.report_generator:
            # 如果未指定输出路径，使用test_result的log_base目录
            if not output_path:
                log_base_dir = self.test_context.get('log_base_dir', './test_result/log')
                output_path = log_base_dir

            # 创建简化的报告配置
            from core.config_manager import ReportConfig
            report_config = ReportConfig(
                report_format=self.config.report.report_format,
                output_dir=output_path,
                insert_screenshots=self.config.report.insert_screenshots
            )

            # 创建报告生成器
            self.report_generator = ReportGenerator(report_config)
        
        # 获取设备信息
        device_info = None
        try:
            runtime_info = {}
            if self.device:
                try:
                    runtime_info = self.device.device_info() or {}
                except Exception as de:
                    logger.warning(f"获取设备运行时信息失败: {de}")

            # 从配置文件读取设备信息（优先）
            cfg_device = {}
            try:
                cfg_dev_obj = getattr(self.config, 'device', None)
                if isinstance(cfg_dev_obj, dict):
                    cfg_device = cfg_dev_obj
                elif cfg_dev_obj is not None:
                    # 兼容对象形式的配置，提取常见字段
                    for key in [
                        'udid', 'serial', 'os_type', 'os_version', 'model', 'brand',
                        'manufacturer', 'platform'
                    ]:
                        if hasattr(cfg_dev_obj, key):
                            cfg_device[key] = getattr(cfg_dev_obj, key)
            except Exception:
                cfg_device = {}

            # 统一取值：udid/os_type 从配置读取；其他字段从设备上报读取
            udid = cfg_device.get('udid') or cfg_device.get('serial')
            raw_os_type = cfg_device.get('os_type') or cfg_device.get('platform')
            os_version = runtime_info.get('os_version') or runtime_info.get('os_sdk')
            model = runtime_info.get('model')
            runtime_name = runtime_info.get('name')
            manufacturer = runtime_info.get('manufacturer')
            display = runtime_info.get('display') or {}
            width = display.get('width')
            height = display.get('height')
            resolution = f"{width}x{height}" if width and height else ""
            os_type = str(getattr(raw_os_type, 'value', raw_os_type) or "").lower()
            
            if os_type == "ios":
                name = (runtime_name or model or "")
            else:
                name = (model or runtime_name or "")

            device_info = {
                "udid": udid or "",
                "os_type": os_type,
                "os_version": os_version or "",
                "model": name or "",
                "manufacturer": manufacturer or "",
                "screen_width": width or 0,
                "screen_height": height or 0,
                "resolution": resolution
            }
        except Exception as e:
            logger.warning(f"获取设备信息失败: {e}")
            device_info = None
        
        # 创建初始JSON报告
        return self.report_generator.create_initial_json_report(
            device_info=device_info,
            execution_start_time=self.execution_start_time
        )
    
    def generate_report(self, output_path: Optional[str] = None, exit_code: Optional[int] = None) -> str:
        """
        生成测试报告（如果存在初始JSON文件则更新，否则创建新的）
        
        Args:
            output_path: 输出路径，为None时使用配置中的路径
            exit_code: 进程最终退出码（用于在无用例执行时也能记录失败原因）
            
        Returns:
            str: 报告文件路径
        """
        # 延迟初始化报告生成器
        if not self.report_generator:
            # 如果未指定输出路径，使用test_result的log_base目录
            if not output_path:
                log_base_dir = self.test_context.get('log_base_dir', './test_result/log')
                output_path = log_base_dir

            # 创建简化的报告配置
            from core.config_manager import ReportConfig
            report_config = ReportConfig(
                report_format=self.config.report.report_format,
                output_dir=output_path,
                insert_screenshots=self.config.report.insert_screenshots
            )

            # 创建报告生成器
            self.report_generator = ReportGenerator(report_config)

        # 即便测试结果为空也生成报告：
        # 1) 空结果通常意味着初始化/安装/设备连接阶段失败；
        # 2) 这些失败会通过全局退出码（final_exit_code）体现；
        # 3) 报告中仍需记录设备信息（如有）、全局监控结果与退出码，便于排查。
        if not self.test_results:
            logger.warning("没有测试用例执行结果，将仅依据退出码与全局信息生成报告")

        try:
            # 获取并标准化设备信息（优先使用config配置文件字段，再用设备上报补全，固定字段集）
            device_info = None
            try:
                runtime_info = {}
                if self.device:
                    try:
                        runtime_info = self.device.device_info() or {}
                    except Exception as de:
                        logger.warning(f"获取设备运行时信息失败: {de}")

                # 从配置文件读取设备信息（优先）
                cfg_device = {}
                try:
                    cfg_dev_obj = getattr(self.config, 'device', None)
                    if isinstance(cfg_dev_obj, dict):
                        cfg_device = cfg_dev_obj
                    elif cfg_dev_obj is not None:
                        # 兼容对象形式的配置，提取常见字段
                        for key in [
                            'udid', 'serial', 'os_type', 'os_version', 'model', 'brand',
                            'manufacturer', 'platform'
                        ]:
                            if hasattr(cfg_dev_obj, key):
                                cfg_device[key] = getattr(cfg_dev_obj, key)
                except Exception:
                    cfg_device = {}

                # 统一取值：udid/os_type 从配置读取；其他字段从设备上报读取
                udid = cfg_device.get('udid') or cfg_device.get('serial')
                raw_os_type = cfg_device.get('os_type') or cfg_device.get('platform')
                os_version = runtime_info.get('os_version') or runtime_info.get('os_sdk')
                # Android/HarmonyOS 设备通常上报 model；iOS 通常上报 name
                model = runtime_info.get('model')  # 安卓/鸿蒙常见字段
                runtime_name = runtime_info.get('name')  # iOS 常见字段
                manufacturer = runtime_info.get('manufacturer')
                # 分辨率来自 display 节点（width x height）
                display = runtime_info.get('display') or {}
                width = display.get('width')
                height = display.get('height')
                resolution = f"{width}x{height}" if width and height else ""

                # 固定字段输出
                # 直接输出配置枚举的字符串值（如 OSType.ANDROID -> "android"）
                os_type = str(getattr(raw_os_type, 'value', raw_os_type) or "").lower()

                # 业务要求：最终字段名使用 name
                # - Android/HarmonyOS：沿用 model 作为 name
                # - iOS：优先使用运行时上报的 name 字段，缺失时回退到 model
                if os_type == "ios":
                    name = (runtime_name or model or "")
                else:
                    name = (model or runtime_name or "")

                device_info = {
                    "udid": udid or "",
                    "os_type": os_type,
                    "os_version": os_version or "",
                    "name": name,  # 统一输出为 name 字段
                    "brand": manufacturer or "",
                    "resolution": resolution or "",
                }
            except Exception as e:
                logger.warning(f"标准化设备信息失败: {e}")
                device_info = device_info or {}

            # 生成报告，包含全局监控结果
            # 调用报告生成器：传递退出码，确保即便无用例结果也能在报告中显示失败原因
            report_path = self.report_generator.generate_report(
                test_results=self.test_results,
                device_info=device_info,
                global_monitor_result=self.global_monitor_result,
                exit_code=exit_code,
                execution_start_time=self.execution_start_time,  # 传递执行开始时间，用于test_results为空时
                error_summary=self.error_summary  # 传递错误摘要
            )
            logger.info(f"测试报告生成成功: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"测试报告生成失败: {e}\n{traceback.format_exc()}")
            raise

    def add_error_summary(self, error_msg: str) -> None:
        """
        添加错误信息到摘要中
        
        Args:
            error_msg: 错误信息
        """
        if error_msg and error_msg not in self.error_summary:
            self.error_summary.append(error_msg)
            logger.debug(f"添加错误摘要: {error_msg}")
    
    def set_global_monitor_result(self, monitor_result: Dict[str, Any]) -> None:
        """
        设置全局监控结果
        
        Args:
            monitor_result: 监控结果字典，包含ANR/Crash监控等信息
        """
        self.global_monitor_result = monitor_result
        logger.info(f"全局监控结果已设置: {monitor_result}")

    def get_global_monitor_result(self) -> Optional[Dict[str, Any]]:
        """
        获取全局监控结果
        
        Returns:
            Optional[Dict[str, Any]]: 全局监控结果，如果没有则返回None
        """
        return self.global_monitor_result

    def get_test_summary(self) -> Dict[str, Any]:
        """
        获取测试摘要
        
        Returns:
            Dict: 测试摘要信息
        """
        if not self.test_results:
            return {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0}

        total = len(self.test_results)
        passed = len([r for r in self.test_results if r.status == TestStatus.PASSED])
        failed = len([r for r in self.test_results if r.status == TestStatus.FAILED])
        error = len([r for r in self.test_results if r.status == TestStatus.ERROR])

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "pass_rate": (passed / total * 100) if total > 0 else 0
        }

        # 添加全局监控结果到摘要中
        if self.global_monitor_result:
            summary["global_monitor"] = self.global_monitor_result

        return summary


# 便捷的全局函数
def run_test(test_case: TestCase, config: Union[FrameworkConfig, str, None] = None) -> TestResult:
    """
    运行单个测试用例的便捷函数
    
    Args:
        test_case: 测试用例
        config: 配置
        
    Returns:
        TestResult: 测试结果
    """
    with TestRunner(config) as runner:
        return runner.run_test_case(test_case)


def run_suite(test_suite: TestSuite, config: Union[FrameworkConfig, str, None] = None) -> List[TestResult]:
    """
    运行测试套件的便捷函数
    
    Args:
        test_suite: 测试套件
        config: 配置
        
    Returns:
        List[TestResult]: 测试结果列表
    """
    with TestRunner(config) as runner:
        return runner.run_test_suite(test_suite)


def run_tests(test_cases: List[TestCase], config: Union[FrameworkConfig, str, None] = None) -> List[TestResult]:
    """
    运行多个测试用例的便捷函数
    
    Args:
        test_cases: 测试用例列表
        config: 配置
        
    Returns:
        List[TestResult]: 测试结果列表
    """
    with TestRunner(config) as runner:
        results = []
        for test_case in test_cases:
            result = runner.run_test_case(test_case)
            results.append(result)
        return results
