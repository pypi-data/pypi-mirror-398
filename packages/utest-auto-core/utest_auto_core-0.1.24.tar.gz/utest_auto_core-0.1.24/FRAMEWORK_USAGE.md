### 一、用例类的基本结构

- **继承基类 `TestCase`**：
  - 必须实现 `run_test(self)`。
  - 可按需重写 `__init__`、`setup`、`teardown`。

示例用例：

```python
from core import TestCase, FailureStrategy
from ubox_py_sdk import Device, DeviceButton


class LoginTest(TestCase):
    """登录功能测试用例示例"""

    def __init__(self, device: Device):
        # 调用父类构造，设置用例名称与描述
        super().__init__(
            name="登录功能测试",                      # 用例名称，会显示在报告中
            description="验证手机号登录流程是否正常",    # 用例说明
            device=device                           # UBox 设备对象
        )
        # 设置断言失败策略：STOP_ON_FAILURE / CONTINUE_ON_FAILURE
        # STOP_ON_FAILURE：断言失败抛 AssertionError，中断后续步骤
        # CONTINUE_ON_FAILURE：断言失败只标记步骤失败，不抛异常，继续执行
        self.failure_strategy = FailureStrategy.STOP_ON_FAILURE

    def setup(self) -> None:
        """前置动作：例如启动应用、处理权限弹窗等"""
        self.log_info("准备登录测试环境...")
        pkg = self.get_package_name()
        if pkg:
            self.start_step("启动应用", f"启动应用: {pkg}")
            ok = self.device.start_app(pkg)
            self.assert_true("应用应成功启动", ok)
            self.end_step()
        else:
            self.log_warning("未配置包名，跳过启动应用")

    def teardown(self) -> None:
        """后置动作：例如停止应用、回到桌面等"""
        self.log_info("开始清理登录测试环境...")
        pkg = self.get_package_name()
        if pkg:
            self.device.stop_app(pkg)
            self.log_info(f"应用已停止: {pkg}")
        self.device.press(DeviceButton.HOME)
        self.log_info("已返回桌面")

    def run_test(self) -> None:
        """核心测试逻辑：分步骤实现"""
        self._step_input_phone()
        self._step_click_login()
        self._step_check_result()

    def _step_input_phone(self) -> None:
        """步骤：输入手机号"""
        self.start_step("输入手机号", "在手机号输入框输入：17912345681")
        # TODO：通过 UBox 定位到手机号输入框并输入
        # 例如：res = self.device.click('//*[@resource-id="xxx"]', timeout=5)
        found = False  # 根据实际 UI 操作结果设置
        self.assert_true("输入手机号失败！未找到手机号输入框", found)
        self.end_step()

    def _step_click_login(self) -> None:
        """步骤：点击登录按钮"""
        self.start_step("点击登录按钮")
        # TODO：self.device.click('//*[@text="登录"]', timeout=5)
        self.end_step()

    def _step_check_result(self) -> None:
        """步骤：校验登录结果"""
        self.start_step("校验登录结果")
        # TODO：通过截图 / 控件 / 文本等判断登录是否成功
        success = True
        self.assert_true("登录应成功", success)
        self.end_step()
```

---

### 二、测试上下文与信息获取能力（`self.get_xxx`）

框架在执行用例时，会通过 `TestCase.execute` 注入 `device` 和 `test_context`，用例可以通过 `get_xxx` 方法统一获取环境与资源信息。

- **`self.get_device_serial() -> str`**
  - **作用**：获取当前测试设备序列号（`serial_num`）。
  - **示例**：
    ```python
    serial = self.get_device_serial()
    self.log_info(f"当前设备序列号: {serial}")
    ```

- **`self.get_package_name() -> str`**
  - **作用**：获取被测应用包名。  
  - 来源：配置文件中的 `task.app_name`、或本地 APK/IPA/HAP 解析结果。
  - **示例**：
    ```python
    pkg = self.get_package_name()
    if pkg:
        self.device.start_app(pkg)
    else:
        self.log_warning("未获取到包名，无法启动应用")
    ```

- **`self.get_test_result_dir() -> str`**
  - **作用**：获取测试结果根目录，一般为 `../test_result`。
  - **示例**：
    ```python
    root_dir = self.get_test_result_dir()
    self.log_info(f"当前测试结果根目录: {root_dir}")
    ```

- **`self.get_case_base_dir() -> str`**
  - **作用**：获取用例基础目录根，例如 `test_result/case/`。
  - 在需要直接将额外数据按用例维度落盘时可使用。

- **`self.get_log_base_dir() -> str`**
  - **作用**：获取日志基础目录根，例如 `test_result/log/`。

- **`self.get_case_dir() -> str`**
  - **作用**：获取当前用例的 case 目录，例如 `test_result/case/登录功能测试/` 或带 usageId 的目录。
  - 适合：额外日志、临时文件等按用例存放。
  - **示例**：
    ```python
    case_dir = self.get_case_dir()
    self.log_info(f"当前用例目录: {case_dir}")
    ```

- **`self.get_case_pic_dir() -> str`**
  - **作用**：获取当前用例的截图目录：`test_result/case/{用例名}/pic/`。
  - 框架默认截图都会保存到这里。

- **`self.get_log_dir() -> str`**
  - **作用**：获取当前用例的日志目录：`test_result/log/{用例名}/`。
  - perf.json、logcat.txt 等文件会统一输出到该目录。

- **`self.get_resource() -> list[dict]`**
  - **作用**：获取平台下发的资源列表（来自 `task.resource`），每个元素为一个 dict。
  - 结构约定：
    - **固定字段**：
      - `type`: 资源类型（如 `"用例"`, `"QQ"`, 其他自定义类型）
      - `usageId`: 使用 ID（平台下发）
    - **平台自定义字段**：
      - 例如：`username`, `password`, `name`, `label` 等
    - **特殊约定**：
      - type="用例"：一定包含 `name` 字段（用例名称）
      - type="QQ"：一定包含 `id` 和 `pwd`
  - **示例**：从资源中取 QQ 账号
    ```python
    for r in self.get_resource():
        if r.get("type") == "QQ":
            qq_id = r.get("id")
            qq_pwd = r.get("pwd")
            self.log_info(f"使用 QQ 账号: {qq_id}")
    ```

- **`self.get_pkg_path() -> str`**
  - **作用**：获取当前安装包的绝对路径（如 `/xx/test/app.apk`）。  
  - 要求：`config.yml` 中 `app_name` 指定的是 apk/ipa/hap 文件名，而不是包名。
  - **示例**：
    ```python
    pkg_path = self.get_pkg_path()
    self.log_info(f"当前测试安装包路径: {pkg_path}")
    ```

---

### 三、步骤管理与日志记录能力

#### 3.1 步骤生命周期管理

- **`self.start_step(step_name: str, description: str = "")`**
  - 开始一个测试步骤：
    - 若上一个步骤尚未结束，会自动调用 `end_step` 收尾。
    - 创建新的 `StepResult`，状态置为 `RUNNING`。
  - **示例**：
    ```python
    self.start_step("打开设置页", "从首页进入设置页面")
    ```

- **`self.end_step(status: StepStatus = None, wait_time: int = 1)`**
  - 结束当前步骤：
    - 设置步骤结束时间、计算耗时。
    - 若 `status` 为 `None` 且当前状态为 `RUNNING`，自动置为 `PASSED`。
    - 根据步骤状态与截图配置，自动触发截图（失败 / 成功 / 异常）。
  - **示例**：
    ```python
    # 默认结束为 PASSED
    self.end_step()

    # 或显式标记失败
    self.end_step(StepStatus.FAILED)
    ```

> **建议**：重要操作都通过 `start_step` + `end_step` 包裹，便于报告里看到清晰的步骤列表、耗时与截图。

#### 3.2 日志记录能力

- **`self.log_info(message: str) -> None`**
  - 记录信息级日志（带 `📝` 前缀），追加到当前步骤的 `logs`。
- **`self.log_warning(message: str) -> None`**
  - 记录警告日志（带 `⚠️` 前缀）。
- **`self.log_error(message: str) -> None`**
  - 记录错误日志（带 `❌` 前缀）。

**示例：**

```python
self.log_info("开始准备测试环境...")
self.log_warning("未配置包名，某些步骤将被跳过")
self.log_error("登录后未找到首页 Banner")
```

---

### 四、断言能力（及失败策略）

#### 4.1 断言接口一览

所有断言最终归一到 `assert_(message, condition)`，在步骤中自动记录结果与截图。

- **布尔断言**：
  - `self.assert_true(message: str, condition: Any)`
  - `self.assert_false(message: str, condition: Any)`
- **相等 / 不等**：
  - `self.assert_equal(message: str, actual: Any, expected: Any)`
  - `self.assert_not_equal(message: str, actual: Any, expected: Any)`
- **包含 / 不包含**：
  - `self.assert_contains(message: str, actual: Any, expected: Any)`
  - `self.assert_not_contains(message: str, actual: Any, expected: Any)`
- **空 / 非空**：
  - `self.assert_none(message: str, value: Any)`
  - `self.assert_not_none(message: str, value: Any)`
- **大小比较**：
  - `self.assert_greater_than(message: str, actual: Any, expected: Any)`
  - `self.assert_less_than(message: str, actual: Any, expected: Any)`

**示例：**

```python
self.assert_true("登录按钮点击应成功", login_clicked)
self.assert_equal("登录后应跳转到首页", current_page, "home")
self.assert_contains("欢迎文案应包含用户名", welcome_text, username)
self.assert_not_none("登录成功截图应成功生成", screenshot_path)
self.assert_greater_than("列表应至少有1个元素", len(items), 0)
```

#### 4.2 断言失败策略（区分断言失败 / 执行异常）

- **配置字段**：`self.failure_strategy: FailureStrategy`
  - **`FailureStrategy.STOP_ON_FAILURE`**（默认）：
    - 断言失败时：
      - 记录错误日志（`❌ 断言失败: ...`）。
      - 当前步骤状态设置为 `FAILED`，写入 `error_message`。
      - 如配置了失败截图，则进行截图。
      - **抛出 `AssertionError`**，用例会被标记为 `FAILED`，框架最终退出码为 **5（脚本断言失败）**。
  - **`FailureStrategy.CONTINUE_ON_FAILURE`**：
    - 断言失败时：
      - 同样记录失败日志、步骤状态置为 `FAILED`、可选截图。
      - 不抛异常，用例继续往下执行。
      - 最终会根据是否存在 `FAILED` 步骤，将用例整体状态标记为 `FAILED`。

> **注意**：  
> - 断言失败属于“脚本断言失败”，和运行时异常（代码 Bug 等）区分开来。  
> - 运行时异常会被框架标记为 `ERROR`，对应退出码为 **2（其它脚本异常）**。

---

### 五、截图与录屏能力

#### 5.1 截图能力

- **`self.take_screenshot(pic_name: str = "screenshot", img_dir: str = None) -> Optional[str]`**
  - 功能：
    - 调用 UBox 的 `device.screenshot` 截取当前屏幕。
    - 默认保存到当前用例的截图目录 `self.get_case_pic_dir()`。
    - 自动将截图路径添加到当前步骤的 `screenshots` 列表中。
  - 示例：
    ```python
    self.start_step("加载完成截图", "等待首页加载完成并截图")
    path = self.take_screenshot("home_loaded")
    self.assert_not_none("首页加载截图应成功", path)
    self.end_step()
    ```

- **步骤快捷截图**（框架内部按配置触发）：
  - `self.take_screenshot_on_step_success()`：步骤成功时截图。
  - `self.take_screenshot_on_step_failure()`：步骤失败时截图。
  - `self.take_screenshot_on_step_error()`：步骤异常时截图。
  - 是否启用由配置项和 `apply_screenshot_config` 决定。

#### 5.2 录屏能力

- **`self.start_record() -> bool`**
  - 功能：
    - 调用 UBox `record_start`，在当前用例 case 目录下生成 `video_YYYYMMDDHHMMSS.mp4`。
    - 将录制文件路径写入 `TestResult.recording_data`。
  - 建议用法：
    ```python
    self.start_step("开始录制", "录制整个登录流程")
    ok = self.start_record()
    self.assert_true("启动录制失败", ok)
    self.end_step()
    ```

- **`self.stop_record() -> bool`**
  - 功能：
    - 调用 UBox `record_stop`，结束录制。
  - 建议用法：
    ```python
    self.start_step("停止录制")
    ok = self.stop_record()
    self.assert_true("停止录制失败", ok)
    self.end_step()
    ```

---

### 六、性能 / Logcat 监控能力

#### 6.1 性能采集能力

- **`self.start_perf(sub_process_name: str = '', sub_window: str = '', case_name: str = '', log_output_file: str = 'perf.json') -> bool`**
  - 底层调用：`device.perf_start(...)`。
  - 效果：
    - UBox 在当前用例 log 目录写入性能监控结果文件（默认 `perf.json`）。
    - 文件内容包含 CPU、内存、FPS、卡顿、网络、温度、功耗等丰富统计指标。
  - 示例：
    ```python
    self.start_step("启动性能采集")
    ok = self.start_perf(case_name=self.name)
    self.assert_true("性能采集启动失败", ok)
    self.end_step()
    ```

- **`self.stop_perf() -> bool`**
  - 底层调用：`device.perf_stop(self.get_log_dir())`。
  - 功能：
    - 停止性能监控。
    - 统一从 `log_dir/perf.json` 读取数据，解析为标准化的 `performance_data` 字典，写入 `TestResult.performance_data`。
  - 通常配合使用：
    ```python
    self.start_step("停止性能采集并打印汇总")
    ok = self.stop_perf()
    self.assert_true("性能采集停止失败", ok)
    # 获取并打印性能汇总（CPU / 内存 / FPS / 流量 / 温度 / 功耗等）
    summary = self.get_performance_summary()
    self.print_performance_summary()
    self.end_step()
    ```

- **性能汇总相关接口**：
  - `self.get_performance_summary() -> dict`：
    - 返回结构化的性能指标字典，字段包括：
      - CPU：`cpu_usage_avg`, `cpu_total_avg`, `cpu_usage_max` 等
      - 内存：`memory_peak_mb`, `memory_avg_mb`, `swap_memory_avg` 等
      - 帧率：`fps_avg`, `fps_max`, `fps_min`, `fps_p50` 等
      - 卡顿：`stutter_rate_percent`, `big_jank_count`, `small_jank_count` 等
      - 网络：`network_upload_total_kb`, `network_download_total_kb`, `net_up_avg`, `net_down_avg` 等
      - 温度：`cpu_temp_avg`, `battery_temp_avg` 等
      - 功耗：`power_avg`, `voltage_avg`, `current_avg` 等
  - `self.print_performance_summary() -> None`：
    - 以可读日志形式打印上述关键指标，便于快速排查。

#### 6.2 Logcat 日志采集能力

- **`self.start_logcat(clear: bool = False, re_filter: Union[str, Pattern] = None) -> LogcatTask`**
  - 底层调用：`device.logcat_start(output_file, clear, re_filter)`。
  - 效果：
    - 在当前用例 log 目录生成 `logcat.txt`。
    - 将文件路径写入 `TestResult.logcat_data`，在报告中展示。
  - 用法示例：
    ```python
    self.start_step("启动 logcat 收集")
    task = self.start_logcat(clear=True)
    self.assert_not_none("logcat 启动失败", task)
    self.end_step()
    ```

> 说明：logcat 的停止一般由设备端 / SDK 内部管理，框架不强制要求在用例里调用 stop。

---

### 七、UI 操作能力（点击 / 滑动 / XPath / 按键）

> 这些能力全部通过 `self.device` 点出来，对应实现类是 `ubox_py_sdk.device.Device`（见 `ubox_py_sdk/device.py`）。  
> 本框架在 `TestCase.execute(...)` 中自动注入 `self.device`，用例只需要直接调用 `self.device.xxx(...)` 即可完成 UI 操作。

#### 7.1 设备与屏幕信息相关能力

- **`self.device.device_info(trace_id=None) -> dict`**
  - 获取设备完整信息：分辨率、密度、系统版本、机型、CPU、内存、存储等（Android / iOS 返回结构略有差异）。
  - 常用于在日志或报告中输出当前测试设备的硬件环境。

- **`self.device.screen_size(trace_id=None) -> List[int]`**
  - 返回屏幕物理分辨率 `[width, height]`，可用于将绝对坐标转换为相对坐标或反之。

- **`self.device.get_auth_info() -> Dict[str, Any]`**
  - 返回认证相关信息：`udid`、`authCode`、`debugId`、`client_addr`，通常用于调试或日志。

- **`self.device.cmd_adb(cmd, timeout=10, trace_id=None)`（Android / 鸿蒙）**
  - 在设备上执行 ADB 命令，例如 `"ls"`, `"ps"`, `"getprop"` 等。
  - Android 设备返回 `(output, exit_code)`，鸿蒙设备返回 output 字符串。

#### 7.2 截图与基础输入能力

- **`self.device.screenshot(label, img_path, crop=None, trace_id=None) -> str`**
  - 对当前画面截图，保存为本地文件路径（本框架在 `take_screenshot` 中已封装默认目录）。
  - 支持 `crop=(left, top, right, bottom)`，可用相对坐标(0~1)或像素坐标进行裁剪。

- **`self.device.screenshot_base64(crop=None, trace_id=None) -> str`**
  - 获取当前画面的截图并返回 base64 字符串，可用于接口上传或自定义比对。

- **`self.device.input_text(text, timeout=30, depth=10, trace_id=None) -> bool`**
  - 向设备输入一段文本，一般用于在已聚焦的输入框内输入内容。

#### 7.3 点击与滑动操作能力

- **相对坐标点击：`self.device.click_pos([x, y], duration=0.05, times=1, trace_id=None) -> bool`**
  - `x, y` 取值范围为 \[0, 1\]，表示相对屏幕宽高的比例。
  - `duration` 控制按下时长，`times` 控制点击次数（2 可实现双击）。
  - 示例：
    ```python
    self.start_step("点击屏幕中心")
    self.device.click_pos([0.5, 0.5])
    self.end_step()
    ```

- **根据 UI 树计算点击坐标**（参考 `ui_traversal_test.py`）：
  - 通过 `self.device.get_uitree(xml=False)` 获取结构化 UI 树；
  - 根据元素的 `bounds` 计算绝对坐标，再除以屏幕宽高得到相对坐标；
  - 最终通过 `click_pos` 进行点击。

- **相对坐标滑动：`self.device.slide_pos([x1, y1], [x2, y2], down_duration=0, slide_duration=0.3, trace_id=None) -> bool`**
  - 以相对坐标指定滑动起点和终点。
  - 示例：从下往上滑动列表
    ```python
    self.start_step("上滑列表")
    self.device.slide_pos([0.5, 0.8], [0.5, 0.2])
    self.end_step()
    ```

- **通用点击：`self.device.click(loc, by=DriverType.UI, offset=None, crop_box=None, timeout=30, duration=0.05, times=1, trace_id=None, **kwargs) -> bool`**
  - 支持多种定位方式：
    - `by=DriverType.UI`：`loc` 为 XPath 等 UI 选择器。
    - `by=DriverType.CV`：`loc` 为模板图片路径，基于图像匹配点击。
    - `by=DriverType.OCR`：`loc` 为待识别文字，基于 OCR 点击。
    - `by=DriverType.POS`：`loc` 为坐标。
  - `offset`：在定位点基础上添加偏移。
  - `crop_box`：指定图片/OCR 查找的屏蔽或保留区域（详见后文 “7.4.1 crop_box 参数说明” 小节）。

- **长按：`self.device.long_click(loc, by=1, offset=None, timeout=30, duration=1, crop_box=None, trace_id=None, **kwargs) -> bool`**
  - 与 `click` 参数一致，默认按压时间更长，用于长按/拖拽等场景。

- **多种定位方式滑动：`self.device.slide(loc_from, loc_to=None, by=1, timeout=120, down_duration=0, slide_duration=0.3, trace_id=None, **kwargs) -> bool`**
  - 支持从一个控件滑动到另一个控件，或基于 CV/OCR 的滑动。

#### 7.4 查找元素与 UI 树能力

- **获取 UI 树：`self.device.get_uitree(xml=False, trace_id=None) -> Union[Dict[str, Any], str]`**
  - `xml=False`：返回嵌套 dict 结构的控件树。
  - `xml=True`：返回 XML 字符串。

- **按 XPath 查找元素**：
  - 单个元素：`self.device.get_element(xpath, timeout=30, trace_id=None)`
  - 元素列表：`self.device.get_elements(xpath, trace_id=None)`

- **通用查找族（UI / CV / OCR / POS）**：
  - `self.device.find_ui(xpath, timeout=30, trace_id=None, **kwargs)`：基于 UI 控件查找，返回中心点坐标。
  - `self.device.find_cv(tpl, img=None, timeout=30, threshold=0.8, pos=None, pos_weight=0.05, ratio_lv=21, is_translucent=False, to_gray=False, tpl_l=None, deviation=None, time_interval=0.5, trace_id=None, **kwargs)`：基于模板图片查找坐标，支持通过 `crop_box` 只在指定区域内做匹配（通过 `kwargs` 传入）。
  - `self.device.find_ocr(word, left_word=None, right_word=None, timeout=30, time_interval=0.5, trace_id=None, **kwargs)`：基于 OCR 文本查找坐标，同样可通过 `crop_box` 限定识别区域（在 `kwargs` 中传入）。
  - `self.device.find(loc, by=1, timeout=30, trace_id=None, **kwargs)`：统一入口，按 `by` 选择查找方式。
  - `self.device.multi_find(ctrl="", img=None, pos=None, by=1, ctrl_timeout=30, img_timeout=10, trace_id=None, **kwargs)`：综合查找，优先控件，其次图片，最后坐标兜底。

- **图像 / OCR 元素定位（返回 bounds）**：
  - `self.device.get_element_cv(...) -> dict`：模板匹配查找元素，返回如 `{'bounds': [x1, y1, x2, y2]}`，支持通过 `crop_box` 指定只在局部区域内做图像识别。
  - `self.device.get_element_ocr(...) -> dict`：OCR 查找元素，返回包含 `bounds` 的字典，同样支持 `crop_box` 限定识别范围。

##### 7.4.1 `crop_box` 参数说明（图像 / OCR 查找的特色能力）

`crop_box` 是 UBox 的一个特色参数，用于**限制图像匹配或文字识别的范围**，从而：

- 提高匹配准确率，避免干扰区域的相似元素误触；
- 降低识别范围，提升查找性能；
- 支持“只在页面局部区域”查找某个按钮或文字。

`crop_box` 的取值规则（注意：这里的坐标均为**百分比**，即 0~1 之间的相对坐标）：

- **保留范围（推荐形式）**：使用两个点的坐标 `[[x1, y1], [x2, y2]]`
  - 含义：只在这个矩形区域内进行匹配 / 识别，其它区域全部忽略。
  - 示例：`[[0.3, 0.3], [0.7, 0.7]]` 表示保留屏幕中间 30%~70% 的矩形区域。

- **屏蔽范围**：使用 4 个数的列表 `[x1, x2, y1, y2]`
  - 含义：**屏蔽**这个矩形区域，不在该区域内做匹配 / 识别。
  - 示例：`[0, 1, 0, 0.3]` 表示屏蔽 x 轴 0~1、y 轴 0~0.3 的顶部区域（即顶部 30% 高度不参与匹配）。

常见用法示例：

```python
# 只在屏幕中间区域查找“登录”按钮（OCR 方式）
from ubox_py_sdk import DriverType

crop_center = [[0.3, 0.3], [0.7, 0.7]]  # 中间区域
clicked = self.device.click(
    loc="登录",
    by=DriverType.OCR,
    crop_box=crop_center,   # 仅在中间区域识别“登录”二字
    timeout=5
)
self.assert_true("未在中间区域找到登录按钮", clicked)

# 只在底部导航区域进行模板匹配（保留底部 30% 区域）
crop_bottom = [[0, 0.7], [1, 1]]
pos = self.device.find_cv(
    tpl="/path/to/icon.png",
    crop_box=crop_bottom,
    timeout=10
)
self.assert_not_none("未在底部导航栏找到指定图标", pos)
```

`crop_box` 可以在以下接口中使用：

- 图像匹配：`get_element_cv` / `find_cv` / `click(by=CV)` / `multi_find` 等（通过 `kwargs` 传入）；
- OCR 识别：`get_element_ocr` / `find_ocr` / `click(by=OCR)` / `multi_find`；
- 其他基于图像或文字查找且支持区域限制的高级封装。

#### 7.5 应用生命周期与安装管理能力

- **安装 / 卸载应用**：
  - `self.device.install_app(app_url=None, app_path=None, need_resign=False, resign_bundle="", trace_id=None) -> bool`
  - `self.device.local_install_app(local_app_path, need_resign=False, resign_bundle="", trace_id=None) -> bool`
  - `self.device.uninstall_app(pkg, trace_id=None) -> bool`

- **启动 / 停止应用**：
  - `self.device.start_app(pkg, clear_data=False, trace_id=None, **kwargs) -> bool`
  - `self.device.stop_app(pkg, trace_id=None) -> bool`

#### 7.6 按键、剪贴板与网络代理能力

- **按键操作**：`self.device.press(DeviceButton.HOME / BACK / ... , trace_id=None) -> bool`
  - 通过 UBox 的按键枚举发送 HOME、BACK 等物理按键。

- **剪贴板操作**：
  - `self.device.set_clipboard(text, trace_id=None)`：设置设备剪贴板文本。
  - `self.device.get_clipboard(trace_id=None)`：获取当前剪贴板文本。

- **HTTP 全局代理设置**：
  - `self.device.set_http_global_proxy(host, port, username=None, password=None, trace_id=None)`
  - `self.device.get_http_global_proxy(trace_id=None)`
  - `self.device.clear_http_global_proxy(trace_id=None)`

#### 7.7 iOS URL 打开能力

- **`self.device.ios_open_url(url: str, permission_config: dict = None, trace_id=None) -> bool`**
  - iOS 专用的一站式 URL 打开能力：
    - 自动回到主屏幕，查找并点击“打开 URL”入口；
    - 输入目标 URL；
    - 根据 `permission_config` 自动处理权限弹窗（如“允许”、“打开”等）。
  - 用例示例：
    ```python
    ok = self.device.ios_open_url("https://example.com")
    self.assert_true("打开 URL 失败", ok)
    ```

#### 7.8 自动处理相关能力（Device 级补充说明）

除了本框架在第八节中通过 `EventHandler` 提供的 watcher 能力外，`Device` 本身还提供一组“事件自动处理”接口（一般用于更底层的自定义场景）：

- `self.device.load_default_handler(rule: list, trace_id=None)`：批量加载预设事件自动处理规则。
- `self.device.start_event_handler(trace_id=None)`：启动预设事件自动处理。
- `self.device.add_event_handler(match_element: str, action_element: str = None, trace_id=None)`：添加单条事件自动处理规则并生效。
- `self.device.sync_event_handler(trace_id=None)`：立即执行一次事件自动处理。
- `self.device.clear_event_handler(trace_id=None)`：清除事件自动处理规则。

通常情况下，用例开发同学更推荐使用“八、Watcher 弹窗处理能力（EventHandler-仅安卓）”中基于 `self.event_handler.watcher(...)` 的高层封装；  
只有在需要和 SDK 进行更底层集成时，才会直接使用以上 `Device` 级自动处理接口。

---

### 八、Watcher 弹窗处理能力（EventHandler-仅安卓）

> 面向权限弹窗、更新弹窗、广告弹窗等“干扰 UI 自动化”的场景，利用 UBox 的后台 watcher 自动处理。

#### 8.1 初始化与重置

```python
from ubox_py_sdk import EventHandler

def setup(self) -> None:
    """测试前置操作：配置 watcher 处理常见弹窗"""
    self.log_info("配置弹窗 watcher")
    # 获取事件处理器（由 UBox SDK 提供）
    self.event_handler = self.device.handler
    event_handler = self.event_handler
    event_handler.reset()  # 清空已有规则
```

#### 8.2 配置 watcher 规则

常见规则示例（来自 `test_cases/ui_traversal_test.py`）：

```python
event_handler.watcher("允许").with_match_mode("strict").when("允许").click()
event_handler.watcher("确定").with_match_mode("strict").when("确定").click()
event_handler.watcher("同意").with_match_mode("strict").when("同意").click()
event_handler.watcher("继续").with_match_mode("strict").when("继续").click()
event_handler.watcher("跳过").with_match_mode("strict").when("跳过").click()
event_handler.watcher("我知道了").when("我知道了").click()
event_handler.watcher("关闭").when("关闭").click()
event_handler.watcher("稍后").when("稍后").click()
event_handler.watcher("取消").when("取消").click()
```

- **语义说明**：
  - **`watcher("名称")`**：创建一个 watcher 规则。
  - **`.with_match_mode("strict")`**：设置严格匹配模式。
  - **`.when("文本")`**：当界面上出现指定文本时触发。
  - **`.click()`**：触发时自动点击。

#### 8.3 启动与停止后台 watcher

- **启动后台监控**：
  ```python
  # 间隔 2 秒轮询 UI，自动执行 watcher 行为
  event_handler.start(2.0)
  ```

- **停止后台监控**（通常在 `teardown` 中）：
  ```python
  self.event_handler.stop()
  ```

---

### 九、稳定性 CI / 遍历能力（`self.stability_test_ci` 仅安卓）

> 面向长时间稳定性测试场景，通过遍历 UI 控件树、自动点击、记录操作与 Activity 访问，发现黑屏 / 崩溃 / ANR 等问题。

#### 9.1 用例中一键开启稳定性 CI

```python
def run_test(self) -> None:
    """执行稳定性遍历测试"""
    self.start_step("稳定性遍历", "基于 UI 控件树进行自动遍历")
    # timeout 单位：秒，默认 15 分钟，可自定义为更长或更短
    self.stability_test_ci(timeout=60 * 30)  # 示例：30 分钟
    self.end_step()
```

#### 9.2 内部能力概览（方便理解日志与输出）

`stability_test_ci` 内部基于 `TraversalCI` 和 UBox `Device` 提供如下能力：

- **环境准备**：
  - 使用 `self.get_package_name()`、`self.get_case_pic_dir()`、`self.get_log_dir()` 获取包名与目录。
  - 为遍历过程创建临时截图目录与最终截图目录。

- **主循环逻辑**（每一轮）：
  - 检查当前前台应用：`device.current_app()`，若已退出则重启并记录操作。
  - 记录当前 Activity：`device.current_activity()`，统计访问次数。
  - 获取 UI 树：`device.get_uitree(xml=True)`。
  - 截图：`device.screenshot(str(round_num), rounds_src 目录)`。
  - 调用 `TraversalCI.automatic_traversal(...)`：
    - 判断黑屏 / 白屏 / 正常屏幕。
    - 根据历史截图与元素列表判断是否为已访问页面。
    - 过滤黑名单控件（如隐私协议、分享弹窗等）。
    - 选择一个可点击元素，返回点击坐标与元素信息（`resource-id/class/bounds/text/content-desc`）。
  - 根据返回的 `flag` 进行不同处理：
    - `black_screen`：累计黑屏次数，超过阈值时保存黑屏截图。
    - `no_click` / `all_click`：根据次数执行上滑 / 返回键 / 重启应用等兜底策略。
    - 正常点击：调用 `device.click_pos` 点击目标控件，在截图中使用红圈标记点击位置，并记录操作详情。

- **结束条件与结果输出**：
  - 超过配置的 `timeout` 后停止遍历：
    - 在当前用例 log 目录中生成：
      - `operation_records.json` / `operation_records.txt`：记录每一轮的点击 / 上滑 / 返回 / 重启等操作。
      - `activity_records.json` / `activity_records.txt`：记录每个 Activity 的首次访问时间、最后访问时间、访问次数等。
  - 所有截图、操作记录、Activity 访问记录都会在报告中以用例附属数据的形式体现。

---


