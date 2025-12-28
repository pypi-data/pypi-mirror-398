#!/usr/bin/env python3

import time
import traceback
import random
from core.test_case import TestCase, StepStatus, FailureStrategy
from ubox_py_sdk import DriverType, OSType, DeviceButton, EventHandler, Device, LogcatTask, PinchDirection


class TestCase1(TestCase):
    """框架使用示例用例（Demo）

    演示内容：
    1) 用例名称/描述设置（见 __init__）
    2) 步骤管理（start_step/end_step）end_step不是必须调用的，在断言中会自动设置结果
    3) 断言（assert_true/assert_equal 等）
    4) 录制（start_record/stop_record）
    5) logcat 采集（start_logcat）
    6) 性能采集（start_perf/stop_perf，停时自动解析 perf.json 并写入报告）
    """

    def __init__(self, device: Device):
        # 设置用例名称与描述（会显示在报告中）
        super().__init__(
            name="test",
            description="演示步骤/断言/性能采集/logcat/录制等能力",
            device=device
        )
        # 初始化事件处理器（如需使用，可在用例内添加 watcher 等逻辑）
        self.event_handler = self.device.handler
        # 失败策略：失败是否继续执行。这里采用“遇错即停”，更贴近日常回归诉求
        # 如需收集全部失败可切换为 FailureStrategy.CONTINUE_ON_FAILURE
        self.failure_strategy = FailureStrategy.STOP_ON_FAILURE
        self.logcat_task = None

    def run_test(self) -> None:
        # print(self.get_resource())
        #
        # ty  = self.get_os_type()
        # if ty == OSType.IOS:
        #     print(ty)
        # if ty == OSType.ANDROID:
        #     print(ty)

        self.start_perf()
        self.device.slide_pos([0.1, 0.5], [0.2, 0.5])
        self.device.pinch(
            rect=[0.3, 0.3, 0.4, 0.4],  # 中间区域，相对坐标 [x, y, w, h]
            scale=1.5,  # 放大 1.5 倍
            direction=PinchDirection.HORIZONTAL  # 水平方向
        )
        self.start_step("aa","aa")
        self.assert_true("aa",False)
        self.stop_perf()
        self.device.find("a",by=DriverType.UI)
        # self.stability_test_ci(timeout=30)
        # device.click_pos([0.5,0.5],times=1)
        # # self.device.click_pos((0.28,0.18), duration=0.01, times=2)
        # res1 = device.get_element('//*[@content-desc="弹幕：已开启，按钮"]',timeout=5)
        # print(res1)
        #
        # res2 = device.find('//*[@content-desc="弹幕：已开启，按钮"]', timeout=5)
        # print(res2)
        # time.sleep(15)
        # res = device.click('//*[@content-desc="弹幕：已开启，按钮"]',timeout=5)
        # print(res)
