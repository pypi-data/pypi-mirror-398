"""
UTest 核心包对外导出

该模块统一导出对用户友好的 API，方便在用例项目中直接导入：

示例：
    from core import (
        TestCase, TestSuite, TestRunner, run_test, run_suite, run_tests,
        TestStatus, StepStatus, FailureStrategy,
        ConfigManager, FrameworkConfig, ReportConfig, DeviceManager
    )

说明：
- 将常用类、枚举与便捷函数统一暴露，避免用户深入内部模块路径
- 所有导出的符号均带有类型注解与中文文档（见各源码文件）
"""

# 对外导出核心测试基类与结构
from .test_case import (
    TestCase,
    TestSuite,
    TestResult,
    StepResult,
    TestStatus,
    StepStatus,
    FailureStrategy,
)

# 对外导出测试运行器与便捷函数
from .test_runner import (
    TestRunner,
    run_test,
    run_suite,
    run_tests,
)

# 对外导出配置与配置管理
from .config_manager import (
    ConfigManager,
    FrameworkConfig,
    ReportConfig,
    TestConfig,
    TaskConfig,
    UBoxConfig,
    DeviceConfig,
)

# 对外导出设备管理
from .device_manager import DeviceManager

# 对外导出报告生成器（如需自定义报告路径/格式可直接使用）
from .report_generator import ReportGenerator

# 对外导出框架启动器
from .framework_launcher import run_framework

__all__ = [
    # test_case
    "TestCase", "TestSuite", "TestResult", "StepResult",
    "TestStatus", "StepStatus", "FailureStrategy",
    # test_runner
    "TestRunner", "run_test", "run_suite", "run_tests",
    # config
    "ConfigManager", "FrameworkConfig", "ReportConfig", "TestConfig",
    "TaskConfig", "UBoxConfig", "DeviceConfig",
    # device
    "DeviceManager",
    # report
    "ReportGenerator",
    # launcher
    "run_framework",
]

