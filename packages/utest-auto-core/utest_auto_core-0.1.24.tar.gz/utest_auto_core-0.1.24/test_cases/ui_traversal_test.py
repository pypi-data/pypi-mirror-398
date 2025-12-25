#!/usr/bin/env python3
"""
简单UI控件点击测试用例

展示框架的基本能力：
1. 应用启动
2. 随意点击几个UI控件
3. 截图功能
4. 基本的滑动操作
"""

import time
import random
from core.test_case import TestCase, StepStatus, FailureStrategy
from ubox_py_sdk import DriverType, DeviceButton, EventHandler, Device


class SimpleUIClickTest(TestCase):
    """简单UI控件点击测试用例"""

    def __init__(self, device: Device):
        super().__init__(
            name="UI控件点击测试",
            description="展示框架的安装、启动、UI操作和截图能力",
            device=device
        )
        # 初始化事件处理器
        self.event_handler = self.device.handler
        # 设置失败策略为继续执行
        self.failure_strategy = FailureStrategy.CONTINUE_ON_FAILURE

    def setup(self) -> None:
        """测试前置操作"""
        self.log_info("开始准备测试环境...")

        # 配置事件处理器处理常见弹窗
        event_handler = self.event_handler
        event_handler.reset()

        # 添加常见的弹窗处理
        event_handler.watcher("允许").with_match_mode("strict").when("允许").click()
        event_handler.watcher("确定").with_match_mode("strict").when("确定").click()
        event_handler.watcher("同意").with_match_mode("strict").when("同意").click()
        event_handler.watcher("继续").with_match_mode("strict").when("继续").click()
        event_handler.watcher("跳过").with_match_mode("strict").when("跳过").click()
        event_handler.watcher("我知道了").when("我知道了").click()
        event_handler.watcher("关闭").when("关闭").click()
        event_handler.watcher("稍后").when("稍后").click()
        event_handler.watcher("取消").when("取消").click()

        # 开始后台监控
        event_handler.start(2.0)

        # 启动应用
        package_name = self.get_package_name()
        if package_name:
            self.start_step("启动应用", f"启动应用: {package_name}")
            success = self.device.start_app(package_name)
            self.assert_true("应用应成功启动", success)
            if success:
                time.sleep(3)  # 等待应用完全加载
                self.end_step(StepStatus.PASSED)
            else:
                self.end_step(StepStatus.FAILED)
        else:
            self.log_warning("未配置应用包名，跳过应用启动")

        # 开始录制
        # self.start_record()

    def teardown(self) -> None:
        """测试后置操作"""
        self.log_info("开始清理测试环境...")

        # 停止监控
        self.event_handler.stop()

        # 停止应用
        package_name = self.get_package_name()
        if package_name:
            self.device.stop_app(package_name)
            self.log_info(f"应用已停止: {package_name}")

        # 返回主界面
        self.device.press(DeviceButton.HOME)
        self.log_info("已返回主界面")

        # 停止录制
        # self.stop_record()

    def run_test(self) -> None:
        """执行简单UI控件点击测试"""
        self.start_perf()
        self.log_info("启动性能采集")
        # self.device.click('//*[@text="测试ANR"]')
        # time.sleep(60)
        self.wait_and_screenshot()

        self.click_ui_elements()

        self.final_screenshot()
        self.stop_perf()
        self.log_info("停止性能采集")

    def wait_and_screenshot(self) -> None:
        """等待应用加载并截图"""
        self.start_step("等待应用加载", "等待应用完全加载并截图")

        # 等待应用加载
        time.sleep(2)

        # 截图记录应用启动状态
        screenshot_path = self.take_screenshot("app_loaded")
        self.assert_not_none("应用加载截图应成功", screenshot_path)

        if screenshot_path:
            self.log_info(f"应用加载截图已保存: {screenshot_path}")

        self.end_step(StepStatus.PASSED)

    def click_ui_elements(self) -> None:
        """每次点击前获取UI树，点击一次控件（有text优先）"""
        self.start_step("点击UI控件", "获取UI树后点击一个控件，优先有text")

        # 获取UI控件树
        ui_tree = self.get_ui_tree()
        if not ui_tree:
            self.log_warning("无法获取UI树，兜底点击屏幕中心")
            self.device.click_pos([0.5, 0.5])
            time.sleep(1)
            self.take_screenshot("clicked_center_fallback")
            self.end_step(StepStatus.PASSED)
            return

        # 优先：有text值且可点击
        clickable_with_text = self.find_clickable_elements_with_text(ui_tree)
        element = None
        reason = ""
        if clickable_with_text:
            element = random.choice(clickable_with_text)
            reason = "有text"
        else:
            # 其次：任意可点击
            any_clickables = self.find_clickable_elements(ui_tree)
            if any_clickables:
                element = random.choice(any_clickables)
                reason = "任意可点击"

        if element is None:
            # 兜底：屏幕中心
            self.log_info("未找到可点击控件，兜底点击屏幕中心")
            self.device.click_pos([0.5, 0.5])
            time.sleep(1)
            self.take_screenshot("clicked_center_fallback")
            self.end_step(StepStatus.PASSED)
            return

        # 计算点击坐标
        bounds = element.get('bounds', {})
        x = (bounds.get('left', 0) + bounds.get('right', 0)) / 2
        y = (bounds.get('top', 0) + bounds.get('bottom', 0)) / 2
        screen_width, screen_height = self.device.screen_size()
        rel_x = x / screen_width
        rel_y = y / screen_height

        text = element.get('text', 'NoText')
        clicked = self.device.click_pos([rel_x, rel_y])
        self.log_info(f"点击控件[{reason}]: '{text}' at ({rel_x:.2f}, {rel_y:.2f}) - {'成功' if clicked else '失败'}")
        time.sleep(1)
        self.take_screenshot("clicked_element_once")
        self.end_step(StepStatus.PASSED)

    def get_ui_tree(self):
        """获取UI控件树"""
        try:
            # 使用框架提供的get_uitree方法
            ui_tree = self.device.get_uitree(xml=False)
            return ui_tree
        except Exception as e:
            self.log_error(f"获取UI控件树失败: {e}")
            return None

    def find_clickable_elements_with_text(self, ui_tree):
        """查找有text值的可点击控件"""
        clickable_elements = []

        def traverse_node(node):
            if not isinstance(node, dict):
                return

            # 检查是否有text值且可点击
            text = node.get('text', '').strip()
            if text and (node.get('clickable', False) or node.get('enabled', False)):
                # 检查是否有有效的边界
                bounds = node.get('bounds', {})
                if (bounds.get('left', 0) < bounds.get('right', 0) and
                        bounds.get('top', 0) < bounds.get('bottom', 0)):

                    # 过滤掉太小的控件
                    width = bounds.get('right', 0) - bounds.get('left', 0)
                    height = bounds.get('bottom', 0) - bounds.get('top', 0)
                    if width >= 20 and height >= 20:
                        clickable_elements.append(node)

            # 递归遍历子节点
            children = node.get('children', [])
            for child in children:
                traverse_node(child)

        # 从根节点开始遍历
        traverse_node(ui_tree)

        return clickable_elements

    def find_clickable_elements(self, ui_tree):
        """查找任何可点击的控件（不要求有text值）"""
        clickable_elements = []

        def traverse_node(node):
            if not isinstance(node, dict):
                return

            # 检查是否可点击
            if node.get('clickable', False) or node.get('enabled', False):
                # 检查是否有有效的边界
                bounds = node.get('bounds', {})
                if (bounds.get('left', 0) < bounds.get('right', 0) and
                        bounds.get('top', 0) < bounds.get('bottom', 0)):

                    # 过滤掉太小的控件
                    width = bounds.get('right', 0) - bounds.get('left', 0)
                    height = bounds.get('bottom', 0) - bounds.get('top', 0)
                    if width >= 20 and height >= 20:
                        clickable_elements.append(node)

            # 递归遍历子节点
            children = node.get('children', [])
            for child in children:
                traverse_node(child)

        # 从根节点开始遍历
        traverse_node(ui_tree)

        return clickable_elements

    def final_screenshot(self) -> None:
        """最终截图"""
        self.start_step("最终截图", "测试结束前进行最终截图")

        # 等待界面稳定
        time.sleep(2)

        # 截图
        screenshot_path = self.take_screenshot("test_completed")
        self.assert_not_none("最终截图应成功", screenshot_path)

        if screenshot_path:
            self.log_info(f"最终截图已保存: {screenshot_path}")

        self.end_step(StepStatus.PASSED)

    def log_debug(self, message: str) -> None:
        """记录调试日志"""
        self.log_info(f"[DEBUG] {message}")
