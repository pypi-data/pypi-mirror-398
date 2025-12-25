#!/usr/bin/env python3
"""
简洁的QTAF风格测试框架

参考腾讯QTAF的设计理念，提供简洁清晰的测试步骤和断言管理
"""
import os
import re
import time
import traceback
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import logging
from ubox_py_sdk import Device, LogcatTask, OSType

from core import utils
from core.utils.stability_ci import OperationRecord, save_operation_records, save_activity_records
from core.utils.traversal_ci import TraversalCI
from core.utils.traversal_util import paint_res_on_screenshot
from core.utils.file_utils import make_dir, del_dir

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """测试状态枚举"""
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class StepStatus(str, Enum):
    """步骤状态枚举"""
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class FailureStrategy(str, Enum):
    """步骤失败策略枚举"""
    STOP_ON_FAILURE = "stop"  # 失败时停止执行后续步骤
    CONTINUE_ON_FAILURE = "continue"  # 失败时继续执行后续步骤


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    description: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    logcat_data: Dict[str, Any] = field(default_factory=dict)  # logcat监控数据
    recording_data: Dict[str, Any] = field(default_factory=dict)  # 录制数据
    steps: List['StepResult'] = field(default_factory=list)

    def __post_init__(self):
        """计算测试持续时间"""
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class StepResult:
    """步骤结果"""
    step_name: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self):
        """计算步骤持续时间"""
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()


class TestCase(ABC):
    """测试用例基类"""

    def __init__(self, name: str, description: str = "", device: Device = None):
        self.test_context = None
        self.name = name
        self.description = description
        self.device: Device = device
        self.steps: List[StepResult] = []
        self.current_step: Optional[StepResult] = None
        self.context: Dict[str, Any] = {}

        # 测试用例级别的配置
        self.screenshot_on_failure: bool = True
        self.screenshot_on_success: bool = False
        self.failure_strategy: FailureStrategy = FailureStrategy.STOP_ON_FAILURE  # 断言失败策略

    def start_step(self, step_name: str, description: str = "") -> None:
        """
        开始一个测试步骤
        
        Args:
            step_name: 步骤名称
            description: 步骤描述
        """
        # 结束上一个步骤（如果存在）
        if self.current_step:
            self.end_step()

        # 开始新步骤
        self.current_step = StepResult(
            step_name=step_name,
            description=description,
            status=StepStatus.RUNNING,
            start_time=datetime.now()
        )

        logger.info(f"🚀 开始步骤: {step_name} - {description}")

    def end_step(self, status: StepStatus = None, wait_time: int = 1) -> None:
        """
        结束当前步骤
        
        Args:
            status: 步骤状态，如果为None则根据当前状态自动判断
            wait_time: 步骤：失败时/成功时截图前延时，例如一些步骤是操作完等一会才有执行后的效果，所以可能需要个延时
        """
        if not self.current_step:
            return

        # 设置步骤结束时间
        self.current_step.end_time = datetime.now()

        # 计算步骤持续时间
        if self.current_step.end_time and self.current_step.start_time:
            self.current_step.duration = (self.current_step.end_time - self.current_step.start_time).total_seconds()

        # 设置步骤状态
        if status is not None:
            self.current_step.status = status
        elif self.current_step.status == StepStatus.RUNNING:
            # 如果还是运行状态，说明没有发生错误，标记为通过
            self.current_step.status = StepStatus.PASSED

        # 根据步骤状态决定是否截图
        if self.current_step.status == StepStatus.FAILED and self.screenshot_on_failure:
            time.sleep(wait_time)
            self.take_screenshot_on_step_failure()
        elif self.current_step.status == StepStatus.PASSED and self.screenshot_on_success:
            time.sleep(wait_time)
            self.take_screenshot_on_step_success()
        elif self.current_step.status == StepStatus.ERROR and self.screenshot_on_failure:
            time.sleep(wait_time)
            self.take_screenshot_on_step_error()

        # 将步骤添加到步骤列表
        self.steps.append(self.current_step)
        self.current_step = None

    def assert_(self, message: str, condition: bool) -> None:
        """
        断言验证
        
        Args:
            message: 断言消息
            condition: 断言条件
        """
        if not self.current_step:
            raise RuntimeError("必须在start_step之后才能使用assert_")

        if not condition:
            error_msg = f"断言失败: {message}"
            logger.error(f"❌ {error_msg}")

            # 失败时截图
            if self.screenshot_on_failure:
                self.take_screenshot("assertion_failed")

            # 设置步骤失败
            self.current_step.status = StepStatus.FAILED
            self.current_step.error_message = error_msg

            # 根据失败策略处理
            if self.failure_strategy == FailureStrategy.STOP_ON_FAILURE:
                raise AssertionError(error_msg)
            # CONTINUE_ON_FAILURE 继续执行，不抛出异常
        else:
            logger.info(f"✅ 断言通过: {message}")

            # 成功时截图
            if self.screenshot_on_success:
                self.take_screenshot("assertion_passed")

    def assert_equal(self, message: str, actual: Any, expected: Any) -> None:
        """断言相等"""
        self.assert_(message, actual == expected)

    def assert_not_equal(self, message: str, actual: Any, expected: Any) -> None:
        """断言不相等"""
        self.assert_(message, actual != expected)

    def assert_contains(self, message: str, actual: Any, expected: Any) -> None:
        """断言包含"""
        self.assert_(message, expected in str(actual))

    def assert_not_contains(self, message: str, actual: Any, expected: Any) -> None:
        """断言不包含"""
        self.assert_(message, expected not in str(actual))

    def assert_true(self, message: str, condition: Any) -> None:
        """断言为真"""
        self.assert_(message, bool(condition))

    def assert_false(self, message: str, condition: Any) -> None:
        """断言为假"""
        self.assert_(message, not bool(condition))

    def assert_none(self, message: str, value: Any) -> None:
        """断言为空"""
        self.assert_(message, value is None)

    def assert_not_none(self, message: str, value: Any) -> None:
        """断言非空"""
        self.assert_(message, value is not None)

    def assert_greater_than(self, message: str, actual: Any, expected: Any) -> None:
        """断言大于"""
        self.assert_(message, actual > expected)

    def assert_less_than(self, message: str, actual: Any, expected: Any) -> None:
        """断言小于"""
        self.assert_(message, actual < expected)

    def log_info(self, message: str) -> None:
        """记录信息日志"""
        logger.info(f"📝 {message}")
        if self.current_step:
            self.current_step.logs.append(f"[INFO] {message}")

    def log_warning(self, message: str) -> None:
        """记录警告日志"""
        logger.warning(f"⚠️ {message}")
        if self.current_step:
            self.current_step.logs.append(f"[WARNING] {message}")

    def log_error(self, message: str) -> None:
        """记录错误日志"""
        logger.error(f"❌ {message}")
        if self.current_step:
            self.current_step.logs.append(f"[ERROR] {message}")

    def setup(self) -> None:
        """测试前置操作，子类可重写"""
        pass

    def teardown(self) -> None:
        """测试后置操作，子类可重写"""
        # 注意：监控任务的停止需要用户在测试用例中手动调用
        # 例如：self.stop_perf(), self.stop_record()
        # logcat和录制文件路径会在启动时自动记录到测试结果中
        pass

    def stability_test_ci(self, timeout: int = 60 * 15) -> None:
        """
        安卓稳定性CI测试
        
        通过自动化UI遍历进行应用的稳定性测试。
        所有日志和截图都会记录到用例步骤中。
        操作记录和Activity信息单独保存到文件。
        注意：CI内部的step是"轮次"概念，不是测试用例的"步骤"。
        
        Args:
            timeout: 测试超时时间（秒），默认15分钟（900秒）
        """
        import datetime
        import shutil
        from time import sleep
        from ubox_py_sdk import DeviceButton

        if self.current_step is None:
            self.start_step("开始稳定性测试", "基于应用的UI控件树进行全局遍历测试")

        self.log_info("开始执行稳定性测试CI")

        # 获取参数
        pkg_name = self.get_package_name()
        screenshot_dir = self.get_case_pic_dir()
        log_dir = self.get_log_dir()

        # screenshot_dir 是图片目录，用于保存最终截图
        # 在图片目录下创建 rounds_src 子目录用于临时截图
        round_case_screenshot_path_dst = screenshot_dir
        round_case_screenshot_path_src = os.path.join(screenshot_dir, 'rounds_src')

        # 只清理和创建临时截图目录
        del_dir(round_case_screenshot_path_src)
        make_dir(round_case_screenshot_path_src)

        # log_dir 是日志目录，直接使用
        case_log_file_path = log_dir

        # 初始化遍历器
        i_kp_traversal = TraversalCI(self.device)

        # 操作记录列表
        operation_records: List[OperationRecord] = []

        # Activity记录字典（去重，记录访问次数）
        activity_records: Dict[str, Dict[str, Any]] = {}

        # 记录超时配置
        self.log_info(f'稳定性测试超时配置: {timeout}秒 ({timeout / 60:.1f}分钟)')

        # 初始化计数器
        round_num = 0  # 轮次编号
        no_click = 0
        all_click = 0
        black_screen = 0

        # 记录开始时间
        start_time = datetime.datetime.now()
        self.log_info(f'稳定性测试开始 - 开始时间: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

        # 主循环
        while True:
            try:
                round_num += 1
                self.log_info('=' * 60)

                # 检查应用是否还在运行
                current_package = self.device.current_app()
                if current_package != pkg_name:
                    self.log_warning(f'应用已退出，当前包名: {current_package}，期望包名: {pkg_name}')
                    # 重启应用
                    current_activity = self.device.current_activity() or "未知"
                    self.log_info(f'重启应用: {pkg_name}')
                    self.device.stop_app(pkg_name)
                    sleep(3)
                    self.device.start_app(pkg_name)

                    # 记录操作
                    operation_records.append(OperationRecord(
                        round_num=round_num,
                        operation="重启应用",
                        activity=current_activity,
                        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                # 记录当前Activity
                current_activity = self.device.current_activity()
                if current_activity:
                    # 记录Activity到字典（统计访问次数）
                    if current_activity not in activity_records:
                        activity_records[current_activity] = {
                            'first_visit': datetime.datetime.now().isoformat(),
                            'visit_count': 1,
                            'last_visit': datetime.datetime.now().isoformat()
                        }
                    else:
                        activity_records[current_activity]['visit_count'] += 1
                        activity_records[current_activity]['last_visit'] = datetime.datetime.now().isoformat()

                # 获取UI层次结构
                dump_str = self.device.get_uitree(xml=True)

                # 截图
                screenshot_src_dir_filename = self.device.screenshot(str(round_num), round_case_screenshot_path_src)
                screenshot_filename = os.path.basename(screenshot_src_dir_filename)

                # 自动遍历分析
                x, y, flag, match_file, element_info = i_kp_traversal.automatic_traversal(
                    dump_str, pkg_name, screenshot_filename,
                    round_case_screenshot_path_src, None
                )

                # 根据遍历结果处理不同状态
                if flag == 'black_screen':
                    # 黑屏处理
                    black_screen += 1
                    if black_screen >= 5:
                        # 保存黑屏截图
                        screenshot_dst = os.path.join(round_case_screenshot_path_dst, f'black_screen_{round_num}.jpg')
                        shutil.copy(screenshot_src_dir_filename, screenshot_dst)
                        self.log_warning(f'检测到黑屏（第{black_screen}次），已保存截图: {screenshot_dst}')
                        # 记录截图到用例步骤
                        if self.current_step and screenshot_dst not in self.current_step.screenshots:
                            self.current_step.screenshots.append(screenshot_dst)
                    else:
                        self.log_warning(f'检测到黑屏（第{black_screen}次）')
                    os.remove(screenshot_src_dir_filename)

                elif flag == 'no_click':
                    # 无点击元素处理
                    black_screen = 0
                    all_click = 0
                    no_click += 1

                    if no_click == 5:
                        # 重启应用
                        self.log_info(f'无点击元素达到5次，重启应用')
                        self.device.stop_app(pkg_name)
                        sleep(3)
                        self.device.start_app(pkg_name)
                        no_click = 0

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="重启应用",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    elif no_click >= 3:
                        # 返回键
                        self.log_info(f'无点击元素达到{no_click}次，执行返回键')
                        os.remove(screenshot_src_dir_filename)
                        self.device.press(DeviceButton.BACK)  # type: ignore

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="按返回键",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    else:
                        # 上滑
                        self.log_info(f'无点击元素（第{no_click}次），执行上滑操作')
                        os.remove(screenshot_src_dir_filename)
                        self.device.slide_pos([0.5, 0.7], [0.5, 0.2])

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="上滑",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))

                elif flag == 'all_click':
                    # 所有元素都已点击处理
                    black_screen = 0
                    no_click = 0
                    all_click += 1

                    if all_click == 5:
                        # 重启应用
                        self.log_info(f'所有元素已点击达到5次，重启应用')
                        self.device.stop_app(pkg_name)
                        sleep(3)
                        self.device.start_app(pkg_name)
                        all_click = 0

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="重启应用",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    elif all_click >= 3:
                        # 返回键
                        self.log_info(f'所有元素已点击达到{all_click}次，执行返回键')
                        os.remove(screenshot_src_dir_filename)
                        self.device.press(DeviceButton.BACK)  # type: ignore

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="按返回键",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    else:
                        # 上滑
                        self.log_info(f'所有元素已点击（第{all_click}次），执行上滑操作')
                        os.remove(screenshot_src_dir_filename)
                        self.device.slide_pos([0.5, 0.7], [0.5, 0.2])

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="上滑",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))

                else:
                    # 正常点击处理
                    black_screen = 0
                    no_click = 0
                    all_click = 0

                    if x and y:
                        # 执行点击
                        # 构建位置描述：优先显示元素信息，如果没有则只显示坐标
                        position_desc = f"({x}, {y})"
                        if element_info:
                            # 优先使用text，其次content-desc，最后resource-id
                            element_text = element_info.get('text', '') or element_info.get('content_desc',
                                                                                            '') or element_info.get(
                                'resource_id', '')
                            if element_text:
                                position_desc = f"{element_text} ({x}, {y})"

                        self.log_info(f'点击: {position_desc}, Activity: {current_activity}')
                        self.device.click_pos(pos=(x, y))

                        screenshot_path = None
                        if not match_file:
                            # 保存截图并标记点击位置（直接保存到传入的截图目录）
                            screenshot_dst_filename = os.path.join(
                                round_case_screenshot_path_dst,
                                screenshot_filename
                            )
                            shutil.copy(screenshot_src_dir_filename, screenshot_dst_filename)
                            # 在截图上标记点击位置
                            paint_res_on_screenshot((x, y), 'circle', screenshot_dst_filename)
                            # 标记完成后删除原图
                            os.remove(screenshot_src_dir_filename)
                            screenshot_path = screenshot_dst_filename
                            # 记录截图到用例步骤
                            if self.current_step and screenshot_path not in self.current_step.screenshots:
                                self.current_step.screenshots.append(screenshot_path)
                        else:
                            # 删除当前截图（匹配的文件已存在，不需要保存）
                            os.remove(screenshot_src_dir_filename)
                            screenshot_path = match_file
                            self.log_info(f'检测到相似页面，使用已有截图: {match_file}')

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="点击",
                            position=position_desc,
                            activity=current_activity or "未知",
                            screenshot=screenshot_path,
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            element_info=element_info
                        ))
                    else:
                        # 无坐标，返回键
                        self.log_info('未找到可点击坐标，执行返回键')
                        os.remove(screenshot_src_dir_filename)
                        self.device.press(DeviceButton.BACK)  # type: ignore

                        # 记录操作
                        operation_records.append(OperationRecord(
                            round_num=round_num,
                            operation="按返回键",
                            activity=current_activity or "未知",
                            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))

                # 等待一段时间
                sleep(3)

            except Exception as e:
                self.log_error(f'稳定性测试异常: {e}')
                if 'Black Screen' in str(e):
                    raise e
            finally:
                # 检查是否超时
                end_time = datetime.datetime.now()
                total_duration = (end_time - start_time).total_seconds()
                if total_duration > timeout:
                    self.log_info(f'稳定性测试结束 - 结束时间: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
                    self.log_info(f'总耗时: {total_duration:.2f}秒 ({total_duration / 60:.1f}分钟)')
                    self.log_info(f'总轮次数: {round_num}')
                    self.log_info(f'统计信息: 黑屏={black_screen}次, 无点击={no_click}次, 全点击={all_click}次')

                    # 保存操作记录到文件
                    save_operation_records(operation_records, case_log_file_path)

                    # 保存Activity记录到文件
                    save_activity_records(activity_records, case_log_file_path)

                    break

    def start_record(self) -> bool:
        """启动录制"""
        video_path = os.path.join(self.get_case_dir(), f"video_{time.strftime('%Y%m%d%H%M%S')}.mp4")
        res = self.device.record_start(video_path)
        if res:
            # 直接记录录制文件路径到测试结果中
            self.record_recording_data({'file_path': video_path})
            logger.info(f"测试用例 {self.name} 启动录制成功")
            return True
        else:
            logger.info(f"测试用例 {self.name} 启动录制失败")
            return False

    def start_perf(self, sub_process_name: str = '',
                   sub_window: str = '', case_name: str = '',
                   log_output_file: str = 'perf.json') -> bool:
        """启动性能监控
        
        注意：性能数据文件会在停止时由设备端写入到用例log目录，
        因此这里不记录任何文件路径，只负责触发开始。
        """
        res = self.device.perf_start(self.get_package_name(), sub_process_name,
                                     sub_window, case_name,
                                     log_output_file)
        if res:
            # 仅保存任务句柄，路径在停止时统一按固定位置读取
            self._perf_task = res
            logger.info(f"测试用例 {self.name} 性能监控已启动")
            return True
        else:
            logger.info(f"测试用例 {self.name} 性能监控启动失败")
            return False

    def start_logcat(self, clear: bool = False,
                     re_filter: Union[str, re.Pattern] = None) -> LogcatTask:
        """启动logcat收集"""
        output_file = os.path.join(self.get_log_dir(), "logcat.txt")
        res = self.device.logcat_start(output_file, clear, re_filter)
        if res:
            # 直接记录logcat文件路径到测试结果中
            self.record_logcat_data({'file_path': output_file})
            logger.info(f"测试用例 {self.name} logcat收集已启动，输出到: {output_file}")
            return res
        else:
            logger.info(f"测试用例 {self.name} logcat收集启动失败")
            return res

    def stop_perf(self) -> bool:
        """停止性能监控并收集数据
        
        设备端会在 self.get_log_dir()/perf.json 写入结果，
        这里在停止成功后按固定路径读取记录。
        """
        res = self.device.perf_stop(self.get_log_dir())
        if res:
            # 统一按固定文件路径读取
            self._perf_output_file = os.path.join(self.get_log_dir(), 'perf.json')
            self._collect_performance_data()
            logger.info(f"测试用例 {self.name} 性能监控已结束")
            return True
        else:
            logger.info(f"测试用例 {self.name} 性能监控结束失败")
            return False

    def stop_record(self) -> bool:
        """停止录制"""
        res = self.device.record_stop()
        if res:
            logger.info(f"测试用例 {self.name} 停止录制成功")
            return True
        else:
            logger.info(f"测试用例 {self.name} 停止录制失败")
            return False

    def set_test_context(self, context: Dict[str, Any]) -> None:
        """设置测试上下文信息"""
        self.test_context = context
        logger.info(f"测试用例 {self.name} 上下文信息已设置")

    def record_performance_data(self, data: Dict[str, Any]) -> None:
        """记录性能监控数据到测试结果中"""
        if not hasattr(self, '_test_result'):
            logger.warning("无法记录性能数据：测试结果对象不存在")
            return

        self._test_result.performance_data = data
        logger.info(f"测试用例 {self.name} 性能监控数据已记录")

    def record_logcat_data(self, data: Dict[str, Any]) -> None:
        """记录logcat数据到测试结果中"""
        if not hasattr(self, '_test_result'):
            logger.warning("无法记录logcat数据：测试结果对象不存在")
            return

        self._test_result.logcat_data = data
        logger.info(f"测试用例 {self.name} logcat数据已记录")

    def record_recording_data(self, data: Dict[str, Any]) -> None:
        """记录录制数据到测试结果中"""
        if not hasattr(self, '_test_result'):
            logger.warning("无法记录录制数据：测试结果对象不存在")
            return

        self._test_result.recording_data = data
        logger.info(f"测试用例 {self.name} 录制数据已记录")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取客户需要的性能指标汇总 - 基于ubox提供的丰富统计指标
        
        Returns:
            Dict[str, Any]: 包含客户需要的核心性能指标和详细统计信息
        """
        if not hasattr(self, '_test_result') or not self._test_result.performance_data:
            return {
                # 客户需要的核心指标
                'cpu_usage_avg': 0.0,
                'memory_peak_mb': 0.0,
                'fps_avg': 0.0,
                'stutter_rate_percent': 0.0,
                'network_upload_total_kb': 0.0,
                'network_download_total_kb': 0.0,
                # 数据状态
                'data_source': 'no_data',
                'metrics_count': 0
            }

        perf_data = self._test_result.performance_data
        data_source = perf_data.get('data_source', 'unknown')

        if data_source == 'ubox_overview':
            # 使用ubox提供的丰富统计指标
            return {
                # 客户需要的核心指标
                'cpu_usage_avg': perf_data.get('cpu_usage_avg', 0.0),
                'memory_peak_mb': perf_data.get('memory_peak_mb', 0.0),
                'fps_avg': perf_data.get('fps_avg', 0.0),
                'stutter_rate_percent': perf_data.get('stutter_rate_percent', 0.0),
                'network_upload_total_kb': perf_data.get('network_upload_total_kb', 0.0),
                'network_download_total_kb': perf_data.get('network_download_total_kb', 0.0),

                # 详细的性能指标
                'cpu_total_avg': perf_data.get('cpu_total_avg', 0.0),
                'cpu_usage_max': perf_data.get('cpu_usage_max', 0.0),
                'memory_avg_mb': perf_data.get('memory_avg_mb', 0.0),
                'fps_max': perf_data.get('fps_max', 0.0),
                'fps_min': perf_data.get('fps_min', 0.0),
                'fps_p50': perf_data.get('fps_p50', 0.0),
                'big_jank_count': perf_data.get('big_jank_count', 0),
                'small_jank_count': perf_data.get('small_jank_count', 0),
                'gpu_avg': perf_data.get('gpu_avg', 0.0),

                # 温度和功耗
                'cpu_temp_avg': perf_data.get('cpu_temp_avg', 0.0),
                'cpu_temp_max': perf_data.get('cpu_temp_max', 0.0),
                'battery_temp_avg': perf_data.get('battery_temp_avg', 0.0),
                'battery_temp_max': perf_data.get('battery_temp_max', 0.0),
                'power_avg': perf_data.get('power_avg', 0.0),
                'voltage_avg': perf_data.get('voltage_avg', 0.0),
                'current_avg': perf_data.get('current_avg', 0.0),

                # 内存详细信息
                'swap_memory_avg': perf_data.get('swap_memory_avg', 0.0),
                'virtual_memory_avg': perf_data.get('virtual_memory_avg', 0.0),

                # 网络详细信息
                'net_up_avg': perf_data.get('net_up_avg', 0.0),
                'net_down_avg': perf_data.get('net_down_avg', 0.0),

                # 帧时间信息
                'frame_time_avg': perf_data.get('frame_time_avg', 0.0),
                'frame_time_peak': perf_data.get('frame_time_peak', 0.0),

                # 数据状态
                'data_source': data_source,
                'metrics_count': perf_data.get('metrics_count', 0)
            }
        else:
            # 兼容旧格式数据
            return {
                'cpu_usage_avg': perf_data.get('cpu_usage_avg', 0.0),
                'memory_peak_mb': perf_data.get('memory_peak_mb', 0.0),
                'fps_avg': perf_data.get('fps_avg', 0.0),
                'stutter_rate_percent': perf_data.get('stutter_rate_percent', 0.0),
                'network_upload_total_kb': perf_data.get('network_upload_total_kb', 0.0),
                'network_download_total_kb': perf_data.get('network_download_total_kb', 0.0),
                'data_source': data_source,
                'metrics_count': 0
            }

    def print_performance_summary(self) -> None:
        """打印客户需要的性能指标汇总 - 基于ubox提供的丰富统计指标"""
        summary = self.get_performance_summary()
        data_source = summary.get('data_source', 'unknown')
        metrics_count = summary.get('metrics_count', 0)

        logger.info("=" * 60)
        logger.info("📊 性能监控数据汇总")
        logger.info("=" * 60)

        # 数据来源信息
        if data_source == 'ubox_overview':
            logger.info(f"📈 数据来源: ubox统计指标 ({metrics_count}个指标)")
        elif data_source == 'ubox_fallback':
            logger.info("📈 数据来源: ubox兼容模式")
        elif data_source == 'no_data':
            logger.info("📈 数据来源: 无性能数据")
        else:
            logger.info(f"📈 数据来源: {data_source}")

        logger.info("-" * 60)

        # 客户需要的核心性能指标
        logger.info("🎯 核心性能指标:")
        logger.info(f"  CPU使用率: {summary['cpu_usage_avg']:.2f}%")
        logger.info(f"  内存峰值: {summary['memory_peak_mb']:.2f} MB")
        logger.info(f"  平均FPS: {summary['fps_avg']:.2f}")
        logger.info(f"  卡顿率: {summary['stutter_rate_percent']:.2f}%")
        logger.info(f"  上传流量: {summary['network_upload_total_kb']:.2f} KB")
        logger.info(f"  下载流量: {summary['network_download_total_kb']:.2f} KB")

        # 如果数据来源是ubox，显示详细指标
        if data_source == 'ubox_overview':
            logger.info("-" * 60)
            logger.info("📊 详细性能指标:")

            # CPU详细信息
            if 'cpu_total_avg' in summary:
                logger.info(f"  总CPU使用率: {summary['cpu_total_avg']:.2f}%")
            if 'cpu_usage_max' in summary:
                logger.info(f"  CPU使用率峰值: {summary['cpu_usage_max']:.2f}%")

            # 内存详细信息
            if 'memory_avg_mb' in summary:
                logger.info(f"  内存平均值: {summary['memory_avg_mb']:.2f} MB")
            if 'swap_memory_avg' in summary:
                logger.info(f"  交换内存: {summary['swap_memory_avg']:.2f} MB")
            if 'virtual_memory_avg' in summary:
                logger.info(f"  虚拟内存: {summary['virtual_memory_avg']:.2f} MB")

            # FPS详细信息
            if 'fps_max' in summary:
                logger.info(f"  最高FPS: {summary['fps_max']:.2f}")
            if 'fps_min' in summary:
                logger.info(f"  最低FPS: {summary['fps_min']:.2f}")
            if 'fps_p50' in summary:
                logger.info(f"  FPS-P50: {summary['fps_p50']:.2f}")

            # 卡顿详细信息
            if 'big_jank_count' in summary:
                logger.info(f"  大卡顿次数: {summary['big_jank_count']}")
            if 'small_jank_count' in summary:
                logger.info(f"  小卡顿次数: {summary['small_jank_count']}")

            # GPU信息
            if 'gpu_avg' in summary:
                logger.info(f"  GPU使用率: {summary['gpu_avg']:.2f}%")

            # 温度信息
            if 'cpu_temp_avg' in summary:
                logger.info(f"  CPU温度: {summary['cpu_temp_avg']:.1f}°C")
            if 'battery_temp_avg' in summary:
                logger.info(f"  电池温度: {summary['battery_temp_avg']:.1f}°C")

            # 功耗信息
            if 'power_avg' in summary:
                logger.info(f"  平均功耗: {summary['power_avg']:.2f} mW")
            if 'voltage_avg' in summary:
                logger.info(f"  平均电压: {summary['voltage_avg']:.2f} mV")
            if 'current_avg' in summary:
                logger.info(f"  平均电流: {summary['current_avg']:.2f} mA")

            # 网络详细信息
            if 'net_up_avg' in summary:
                logger.info(f"  平均上传速度: {summary['net_up_avg']:.2f} KB/s")
            if 'net_down_avg' in summary:
                logger.info(f"  平均下载速度: {summary['net_down_avg']:.2f} KB/s")

            # 帧时间信息
            if 'frame_time_avg' in summary:
                logger.info(f"  平均帧时间: {summary['frame_time_avg']:.2f} ms")
            if 'frame_time_peak' in summary:
                logger.info(f"  峰值帧时间: {summary['frame_time_peak']:.2f} ms")

        logger.info("=" * 60)

    def _collect_performance_data(self) -> None:
        """收集并解析性能监控数据（perf.json）- 使用ubox提供的丰富统计指标"""
        try:
            if hasattr(self, '_perf_output_file') and os.path.exists(self._perf_output_file):
                # 读取性能监控JSON文件
                with open(self._perf_output_file, 'r', encoding='utf-8') as f:
                    perf_data = json.load(f)

                # 基础元信息
                performance_data: Dict[str, Any] = {
                    'file_path': self._perf_output_file,  # 性能数据文件路径
                    'file_size': os.path.getsize(self._perf_output_file),  # 文件大小(字节)
                    'app_display_name': perf_data.get('AppDisplayName', ''),  # 应用显示名称
                    'app_version': perf_data.get('AppVersion', ''),  # 应用版本号
                    'app_package_name': perf_data.get('AppPackageName', ''),  # 应用包名
                    'device_model': perf_data.get('DeviceModel', ''),  # 设备型号
                    'os_type': perf_data.get('OSType', ''),  # 操作系统类型(ANDROID/IOS)
                    'os_version': perf_data.get('OSVersion', ''),  # 操作系统版本
                    'cpu_type': perf_data.get('CpuType', ''),  # CPU架构类型(如arm64-v8a)
                    'gpu_type': perf_data.get('GpuType', ''),  # GPU类型
                    'case_name': perf_data.get('CaseName', ''),  # 测试用例名称
                    'data_start_time': perf_data.get('AbsDataStartTime', 0),  # 数据采集开始时间戳(毫秒)
                    'collection_time': datetime.now().isoformat()  # 数据收集时间
                }

                # 直接使用ubox提供的Overview统计指标，无需二次计算
                self._extract_ubox_performance_metrics(perf_data, performance_data)

                # 写入测试结果
                self.record_performance_data(performance_data)
                logger.info(f"性能监控数据收集完成: {self._perf_output_file}")
            else:
                logger.warning("性能监控文件不存在，无法收集数据")
        except Exception as e:
            logger.error(f"收集性能监控数据失败: {e}")

    def _extract_ubox_performance_metrics(self, perf_data: Dict[str, Any], performance_data: Dict[str, Any]) -> None:
        """提取ubox提供的性能统计指标"""
        try:
            # 获取Overview中的所有统计指标
            overview = perf_data.get('Overview', {}).get('ALL', [])

            # 创建指标映射字典，便于快速查找
            metrics_map = {}
            for metric in overview:
                key = metric.get('Key', '')
                name = metric.get('Name', '')
                value = metric.get('Value', 0)
                unit = metric.get('Unit', '')

                # 存储完整的指标信息
                metrics_map[f"{key}_{name}"] = {
                    'value': value,
                    'unit': unit,
                    'name': name
                }

            # 提取客户需要的核心性能指标
            # 1. CPU使用率
            cpu_app_avg = self._get_metric_value(metrics_map, 'AppUsage_Avg(AppCPU)', 0.0)
            cpu_total_avg = self._get_metric_value(metrics_map, 'TotalUsage_Avg(TotalCPU)', 0.0)
            cpu_app_peak = self._get_metric_value(metrics_map, 'AppUsage_Peak(AppCPU)', 0.0)
            cpu_total_peak = self._get_metric_value(metrics_map, 'TotalUsage_Peak(TotalCPU)', 0.0)

            # 2. 内存峰值
            memory_avg = self._get_metric_value(metrics_map, 'Memory_Avg(Memory)', 0.0)
            memory_peak = self._get_metric_value(metrics_map, 'Memory_Peak(Memory)', 0.0)

            # 3. FPS相关
            fps_avg = self._get_metric_value(metrics_map, 'fps_Avg(FPS)', 0.0)
            fps_max = self._get_metric_value(metrics_map, 'fps_Max(FPS)', 0.0)
            fps_min = self._get_metric_value(metrics_map, 'fps_Min(FPS)', 0.0)
            fps_p50 = self._get_metric_value(metrics_map, 'fps_P50(FPS)', 0.0)

            # 4. 卡顿相关
            jank_total = self._get_metric_value(metrics_map, 'Jank_Jank', 0)
            big_jank = self._get_metric_value(metrics_map, 'BigJank_Big Jank', 0)
            small_jank = self._get_metric_value(metrics_map, 'SmallJank_Small Jank', 0)
            stutter_rate = self._get_metric_value(metrics_map, 'Stutter_Stutter', 0.0)

            # 5. 网络流量
            net_up_avg = self._get_metric_value(metrics_map, 'UpSpeed_Avg(Send)[KB/s]', 0.0)
            net_down_avg = self._get_metric_value(metrics_map, 'DownSpeed_Avg(Recv)[KB/s]', 0.0)
            net_up_total = self._get_metric_value(metrics_map, 'UpSpeed_Sum(Send)[KB]', 0.0)
            net_down_total = self._get_metric_value(metrics_map, 'DownSpeed_Sum(Recv)[KB]', 0.0)

            # 6. GPU使用率
            gpu_avg = self._get_metric_value(metrics_map, 'GpuUsage_Avg(GPUUsage)', 0.0)

            # 7. 温度
            cpu_temp_avg = self._get_metric_value(metrics_map, 'CpuTemperature_Avg(CPUTemp)', 0.0)
            cpu_temp_max = self._get_metric_value(metrics_map, 'CpuTemperature_Max(CPUTemp)', 0.0)
            battery_temp_avg = self._get_metric_value(metrics_map, 'BatteryTemperature_Avg(BatteryTemp)', 0.0)
            battery_temp_max = self._get_metric_value(metrics_map, 'BatteryTemperature_Max(BatteryTemp)', 0.0)

            # 8. 功耗
            power_avg = self._get_metric_value(metrics_map, 'Power_Avg(Power)', 0.0)
            voltage_avg = self._get_metric_value(metrics_map, 'Voltage_Avg(Voltage)', 0.0)
            current_avg = self._get_metric_value(metrics_map, 'Current_Avg(Current)', 0.0)

            # 9. 内存详细信息
            swap_memory_avg = self._get_metric_value(metrics_map, 'SwapMemory_Avg(SwapMemory)', 0.0)
            virtual_memory_avg = self._get_metric_value(metrics_map, 'VirtualMemory_Avg(VirtualMemory)', 0.0)

            # 10. 帧时间
            frame_time_avg = self._get_metric_value(metrics_map, 'fps_Avg(FTime)[ms]', 0.0)
            frame_time_peak = self._get_metric_value(metrics_map, 'fps_Peak(FTime)', 0.0)

            # 存储所有提取的性能指标
            performance_data.update({
                # 客户需要的核心指标
                'cpu_usage_avg': cpu_app_avg,
                'cpu_usage_max': cpu_app_peak,
                'memory_peak_mb': memory_peak,
                'memory_avg_mb': memory_avg,
                'fps_avg': fps_avg,
                'fps_max': fps_max,
                'fps_min': fps_min,
                'fps_p50': fps_p50,
                'stutter_rate_percent': stutter_rate,
                'network_upload_total_kb': net_up_total,
                'network_download_total_kb': net_down_total,

                # 详细的性能指标
                'cpu_total_avg': cpu_total_avg,
                'cpu_total_max': cpu_total_peak,
                'gpu_avg': gpu_avg,
                'cpu_temp_avg': cpu_temp_avg,
                'cpu_temp_max': cpu_temp_max,
                'battery_temp_avg': battery_temp_avg,
                'battery_temp_max': battery_temp_max,
                'power_avg': power_avg,
                'voltage_avg': voltage_avg,
                'current_avg': current_avg,
                'swap_memory_avg': swap_memory_avg,
                'virtual_memory_avg': virtual_memory_avg,
                'frame_time_avg': frame_time_avg,
                'frame_time_peak': frame_time_peak,

                # 卡顿统计
                'jank_total': jank_total,
                'big_jank_count': big_jank,
                'small_jank_count': small_jank,

                # 网络统计
                'net_up_avg': net_up_avg,
                'net_down_avg': net_down_avg,

                # 数据来源标识
                'data_source': 'ubox_overview',
                'metrics_count': len(overview)
            })

            logger.info(f"成功提取ubox性能指标 {len(overview)} 个")

        except Exception as e:
            logger.error(f"提取ubox性能指标失败: {e}")
            # 如果提取失败，设置默认值
            performance_data.update({
                'cpu_usage_avg': 0.0,
                'memory_peak_mb': 0.0,
                'fps_avg': 0.0,
                'stutter_rate_percent': 0.0,
                'network_upload_total_kb': 0.0,
                'network_download_total_kb': 0.0,
                'data_source': 'ubox_fallback'
            })

    def _get_metric_value(self, metrics_map: Dict[str, Any], key: str, default_value: Any = 0.0) -> Any:
        """从指标映射中获取值"""
        metric = metrics_map.get(key)
        if metric:
            return metric['value']
        return default_value

    def apply_screenshot_config(self, screenshot_on_failure: bool = None, screenshot_on_success: bool = None) -> None:
        """
        应用截图配置
        
        Args:
            screenshot_on_failure: 失败时是否截图，None表示不修改
            screenshot_on_success: 成功时是否截图，None表示不修改
        """
        if screenshot_on_failure is not None:
            self.screenshot_on_failure = screenshot_on_failure
            logger.info(f"测试用例 {self.name} 失败时截图设置: {screenshot_on_failure}")

        if screenshot_on_success is not None:
            self.screenshot_on_success = screenshot_on_success
            logger.info(f"测试用例 {self.name} 成功时截图设置: {screenshot_on_success}")

    def get_device_serial(self) -> str:
        """获取设备序列号"""
        return self.test_context.get('serial_num', '') if hasattr(self, 'test_context') else ''

    def get_package_name(self) -> str:
        """获取测试包名"""
        return self.test_context.get('package_name', '') if hasattr(self, 'test_context') else ''

    def get_test_result_dir(self) -> str:
        """获取测试结果根目录"""
        if hasattr(self, 'test_context') and 'test_result_dir' in self.test_context:
            return self.test_context.get('test_result_dir')
        return './test_result'

    def get_case_base_dir(self) -> str:
        """获取用例基础目录: test_result/case/"""
        if hasattr(self, 'test_context') and 'case_base_dir' in self.test_context:
            return self.test_context.get('case_base_dir')
        return os.path.join(self.get_test_result_dir(), 'case')

    def get_log_base_dir(self) -> str:
        """获取日志基础目录: test_result/log/"""
        if hasattr(self, 'test_context') and 'log_base_dir' in self.test_context:
            return self.test_context.get('log_base_dir')
        return os.path.join(self.get_test_result_dir(), 'log')

    def get_case_dir(self) -> str:
        """获取当前用例的case目录:test_result/case/{用例名}/"""
        if hasattr(self, 'test_context') and 'case_dir' in self.test_context:
            return self.test_context.get('case_dir')
        return os.path.join(self.get_case_base_dir(), self.name)

    def get_case_pic_dir(self) -> str:
        """获取当前用例的case的目录:test_result/case/{用例名}/pic/"""
        if hasattr(self, 'test_context') and 'pic_dir' in self.test_context:
            return self.test_context.get('pic_dir')
        return os.path.join(self.get_case_base_dir(), self.name)

    def get_log_dir(self) -> str:
        """获取当前用例的log目录:test_result/log/{用例名}/"""
        if hasattr(self, 'test_context') and 'log_dir' in self.test_context:
            return self.test_context.get('log_dir')
        return os.path.join(self.get_log_base_dir(), self.name)

    def get_os_type(self) -> OSType:
        """获取当前设备的系统:ios、安卓、鸿蒙"""
        if hasattr(self, 'test_context') and 'os_type' in self.test_context:
            os_type = self.test_context.get('os_type')
            if isinstance(os_type, OSType):
                return os_type
            if isinstance(os_type, str):
                s = os_type.strip().lower()
                for o in OSType:
                    if s == o.value or s == o.name.lower():
                        return o
            return OSType.ANDROID
        return OSType.ANDROID

    def get_resource(self) -> list:
        """获取资源信息列表
        
        资源信息结构说明：
            每个资源项是一个字典，包含以下结构：
            - 固定属性（一定存在）：
              * type: 资源类型（如："其他自定义"、"QQ"、"用例"等）
              * usageId: 使用ID（如："10970602"）
            - 平台自定义配置（动态字段，根据平台和资源类型不同而变化）：
              * 其他所有字段都是平台自定义的，可能包括：username、password、label等
            - 特殊类型字段要求：
              * 用例类型（type="用例"）：一定有 name 字段（用例名称）
              * QQ类型（type="QQ"）：一定有 id 和 pwd 字段
        
        Returns:
            list: 资源信息列表，每个元素是一个字典
        """
        if hasattr(self, 'test_context') and self.test_context:
            return self.test_context.get('resource', [])
        return []

    def get_pkg_path(self) -> str:
        """获取当前安装包的绝对路径:/xx/test/app.apk; 要求：config yml中的app_name要指定的是apk或ipa或hap，如果是包名则无法获取"""
        return self.test_context.get('package_file_path', '') if hasattr(self, 'test_context') else ''

    def take_screenshot(self, pic_name: str = "screenshot", img_dir: str = None) -> Optional[str]:
        """
        截取屏幕截图
        
        Args:
            pic_name: 截图文件名
            img_dir: 截图文件目录
        Returns:
            Optional[str]: 截图文件路径，失败时返回None
        """
        if not self.device:
            logger.warning("设备对象未初始化，无法截图")
            return None

        try:
            if img_dir is None:
                img_dir = self.get_case_pic_dir()
            img_path = self.device.screenshot(pic_name, img_dir)
            # 将截图路径添加到当前步骤
            if self.current_step:
                self.current_step.screenshots.append(img_path)
            return img_path

        except Exception as e:
            logger.error(f"❌ 截图失败: {e}\n{traceback.format_exc()}")
            return None

    def take_screenshot_on_step_success(self) -> Optional[str]:
        """步骤成功时截图"""
        if not self.current_step:
            return None
        return self.take_screenshot("step_success")

    def take_screenshot_on_step_failure(self) -> Optional[str]:
        """步骤失败时截图"""
        if not self.current_step:
            return None
        return self.take_screenshot("step_failure")

    def take_screenshot_on_step_error(self) -> Optional[str]:
        """步骤错误时截图"""
        if not self.current_step:
            return None
        return self.take_screenshot("step_error")

    @abstractmethod
    def run_test(self) -> None:
        """运行测试用例，子类必须实现"""
        pass

    def execute(self, device, context: Dict[str, Any]) -> TestResult:
        """执行测试用例"""
        start_time = datetime.now()
        test_result = TestResult(
            test_name=self.name,
            description=self.description,
            status=TestStatus.RUNNING,
            start_time=start_time
        )

        try:
            logger.info(f"开始执行测试用例: {self.name} - {self.description}")

            # 保存设备对象到测试用例实例中
            self.device = device

            # 保存测试结果对象，供测试用例记录监控数据使用
            self._test_result = test_result

            # 设置测试上下文
            self.set_test_context(context)

            # 执行前置操作
            self.setup()

            try:
                # 执行测试用例主体逻辑
                # 说明：这里将 AssertionError 单独捕获，用于区分「断言失败」与「脚本异常」
                self.run_test()

                # 结束最后一个步骤（正常执行完成时）
                if self.current_step:
                    self.end_step(StepStatus.PASSED)

                # 根据步骤结果判断用例最终状态
                failed_steps = [s for s in self.steps if s.status == StepStatus.FAILED]
                if failed_steps:
                    # 有步骤被标记为 FAILED，则认为是断言失败场景
                    test_result.status = TestStatus.FAILED
                    test_result.error_message = f"有 {len(failed_steps)} 个步骤失败"
                else:
                    # 所有步骤都通过，认为用例通过
                    test_result.status = TestStatus.PASSED

            except AssertionError as e:
                # 专门处理断言失败：
                # - 将用例状态标记为 FAILED，而不是 ERROR
                # - 这样在框架层可以通过 TestStatus.FAILED 映射到脚本断言失败的退出码
                test_result.status = TestStatus.FAILED
                test_result.error_message = str(e)
                logger.error(f"测试用例断言失败: {self.name} - {e}\n{traceback.format_exc()}")

                # 结束当前步骤：
                # - 在 assert_ 中已经把步骤状态置为 FAILED，这里只补充错误信息并用 FAILED 收尾
                if self.current_step:
                    self.current_step.error_message = str(e)
                    self.end_step(StepStatus.FAILED)

            except Exception as e:
                # 除 AssertionError 以外的异常，都认为是脚本执行异常
                test_result.status = TestStatus.ERROR
                test_result.error_message = str(e)
                logger.error(f"测试用例异常: {self.name} - {e}\n{traceback.format_exc()}")

                # 结束当前步骤，标记为 ERROR
                if self.current_step:
                    self.current_step.error_message = str(e)
                    self.end_step(StepStatus.ERROR)

            finally:
                # 执行后置操作，确保无论测试是否异常都会执行
                try:
                    self.teardown()
                except Exception as teardown_error:
                    logger.error(f"teardown执行异常: {self.name} - {teardown_error}")

            # 复制步骤结果
            test_result.steps = self.steps.copy()

        except Exception as e:
            test_result.status = TestStatus.ERROR
            test_result.error_message = str(e)
            logger.error(f"测试用例异常: {self.name} - {e}\n{traceback.format_exc()}")

            # 结束当前步骤
            if self.current_step:
                self.current_step.error_message = str(e)
                self.end_step(StepStatus.ERROR)

            test_result.steps = self.steps.copy()

        finally:
            test_result.end_time = datetime.now()
            # 手动计算持续时间，因为__post_init__在对象创建时调用，那时end_time还是None
            if test_result.end_time and test_result.start_time:
                test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()

            duration_str = f"{test_result.duration:.2f}" if test_result.duration is not None else "未知"
            logger.info(f"测试用例完成: {self.name}, 状态: {test_result.status.value}, 耗时: {duration_str}秒")

        return test_result


class TestSuite:

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.test_cases: List[TestCase] = []

    def add_test_case(self, test_case: TestCase) -> 'TestSuite':
        """添加测试用例"""
        self.test_cases.append(test_case)
        return self

    def execute(self, device, context: Dict[str, Any]) -> List[TestResult]:
        """执行测试套件"""
        results = []

        for test_case in self.test_cases:
            result = test_case.execute(device, context)
            results.append(result)

        return results
