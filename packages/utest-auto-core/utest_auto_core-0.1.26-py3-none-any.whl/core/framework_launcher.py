#!/usr/bin/env python3
"""
测试框架启动器

将启动逻辑封装在库中，模板中的 start_test.py 只需调用此函数即可
"""

import zipfile
import re
import plistlib
import io
import json
import os
import sys
import logging
import time
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from androguard.core.bytecodes import apk
from ubox_py_sdk import OSType

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.test_runner import TestRunner
from core.utils.file_utils import make_dir, del_dir
from test_cases.internal.loader import create_test_collection
from core.exit_codes import (
    SUCCESS, RUNNER_ERROR, INSTALL_ERROR, SCRIPT_ASSERT_ERROR,
    DEVICE_OFFLINE, CRASH, ANR
)

g_log_file_dir = None
g_case_base_dir = None


def log_exception_once(prefix: str, exc: Exception, logger) -> None:
    """仅打印一次异常堆栈，避免多处捕获重复打日志"""
    if not hasattr(log_exception_once, '_printed_exceptions'):
        log_exception_once._printed_exceptions = set()

    key = (type(exc), str(exc))
    if key in log_exception_once._printed_exceptions:
        return
    log_exception_once._printed_exceptions.add(key)
    logger.error(f"{prefix}: {exc}\n{traceback.format_exc()}")


def parse_app_source(app_name: str, logger=None, need_install: Optional[bool] = None) -> dict:
    """
    解析应用来源，判断是否为本地文件/包名
    
    Args:
        app_name: 应用名称（可能是包名或文件路径）
        logger: 日志记录器
        need_install: 强制控制是否需要安装（None表示跟随默认逻辑：有后缀就安装，无后缀就不安装）
    
    Returns:
        dict: 包含应用信息的字典，包括：
            - need_install: 是否需要安装
            - source_type: 来源类型（'file' 或 'package'）
            - package_name: 包名
            - file_path: 文件路径（如果是文件）
            - file_type: 文件类型（'apk'/'ipa'/'hap'）
    """
    result = {
        'need_install': False,
        'source_type': 'package',
        'package_name': '',
        'file_path': None,
        'file_type': None,
    }

    text = app_name.strip()
    file_extensions = ['.apk', '.ipa', '.hap']

    # 检查是否为文件路径（有后缀）
    is_file_path = False
    detected_file_type = None
    detected_file_path = None

    for ext in file_extensions:
        if text.lower().endswith(ext):
            is_file_path = True
            detected_file_type = ext[1:]
            i_test_app_path = os.path.join(os.path.dirname(os.getcwd()), text)
            if os.path.isabs(i_test_app_path) and os.path.exists(i_test_app_path):
                detected_file_path = i_test_app_path
                break

    # 如果 need_install 不为 None，则使用强制设置覆盖默认逻辑
    if need_install is not None:
        result['need_install'] = need_install
        if need_install:
            # 如果需要安装，尝试解析包名
            if is_file_path and detected_file_path:
                # 如果是文件路径，从文件中提取包名
                result['source_type'] = 'file'
                result['file_path'] = detected_file_path
                result['file_type'] = detected_file_type
                result['package_name'] = extract_package_name(detected_file_path, detected_file_type, logger)
            else:
                # 如果不是文件路径，但需要安装，则尝试解析包名（从包名解析）
                result['source_type'] = 'package'
                result['package_name'] = text
                if logger:
                    logger.warning(f"强制安装设置为True，但app_name不是文件路径，将使用包名: {text}")
        else:
            # 如果不需要安装，直接使用包名
            result['need_install'] = False
            result['source_type'] = 'package'
            result['package_name'] = text
            if is_file_path and detected_file_path:
                # 即使有文件路径，也不安装，但可以提取包名
                result['file_path'] = detected_file_path
                result['file_type'] = detected_file_type
                result['package_name'] = extract_package_name(detected_file_path, detected_file_type, logger)
        return result

    # 默认逻辑：有后缀就安装，无后缀就不安装
    if is_file_path and detected_file_path:
        result['need_install'] = True
        result['source_type'] = 'file'
        result['file_path'] = detected_file_path
        result['file_type'] = detected_file_type
        result['package_name'] = extract_package_name(detected_file_path, detected_file_type, logger)
    else:
        result['need_install'] = False
        result['source_type'] = 'package'
        result['package_name'] = text

    return result


def extract_package_name(file_path: str, file_type: str, logger=None) -> str:
    """从包文件中提取包名"""
    try:
        if file_type == 'apk':
            return extract_apk_package_name(file_path, logger)
        elif file_type == 'ipa':
            return extract_ipa_package_name(file_path, logger)
        elif file_type == 'hap':
            return extract_hap_package_name(file_path, logger)
        else:
            return ""
    except Exception:
        return ""


def extract_apk_package_name(apk_path: str, logger=None) -> str:
    """从APK文件中提取包名"""
    try:
        i_apk_info = apk.APK(apk_path)
        if i_apk_info is not None:
            return i_apk_info.get_package()
    except Exception:
        pass
    return ""


def extract_ipa_package_name(ipa_path: str, logger=None) -> str:
    """从IPA文件中提取包名"""
    try:
        with zipfile.ZipFile(ipa_path, 'r') as ipa:
            for file in ipa.namelist():
                if re.match(r'Payload/[^/]+\.app/Info\.plist', file):
                    plist_data = ipa.read(file)
                    # 使用 plistlib 来解析二进制 plist
                    plist = plistlib.load(io.BytesIO(plist_data))
                    bundle_id = plist.get('CFBundleIdentifier', '')
                    return bundle_id
        return ""
    except Exception as e:
        logger.error(f"解析 iOS IPA 文件错误: {e}")
        return ""


def extract_hap_package_name(hap_path: str, logger=None) -> str:
    """从HAP文件中提取包名"""
    try:
        with zipfile.ZipFile(hap_path, 'r') as hap:
            # 查找 pack.info 文件
            pack_info_files = [f for f in hap.namelist() if f.endswith('pack.info')]

            if not pack_info_files:
                logger.error("未找到 pack.info 文件")
                return ""

            pack_info_file = pack_info_files[0]
            pack_info_data = hap.read(pack_info_file)
            pack_info = json.loads(pack_info_data.decode('utf-8'))

            # 从 pack.info 中提取 bundleName，支持嵌套结构
            bundle_name = ''

            # 方法1：直接从根级别获取
            if 'bundleName' in pack_info:
                bundle_name = pack_info['bundleName']
            # 方法2：从 summary.app.bundleName 获取
            elif 'summary' in pack_info and 'app' in pack_info['summary']:
                bundle_name = pack_info['summary']['app'].get('bundleName', '')
            # 方法3：从 app.bundleName 获取
            elif 'app' in pack_info:
                bundle_name = pack_info['app'].get('bundleName', '')

            if bundle_name:
                logger.info(f"提取到鸿蒙包名: {bundle_name}")
                # 同时显示版本信息（如果有的话）
                version_info = ''
                if 'summary' in pack_info and 'app' in pack_info['summary'] and 'version' in pack_info['summary'][
                    'app']:
                    version_info = pack_info['summary']['app']['version'].get('name', '')
                    if version_info:
                        logger.info(f"应用版本: {version_info}")

            return bundle_name

    except Exception as e:
        logger.error(f"解析鸿蒙 HAP 文件错误: {e}")
        return ""


def install_pkg(device, package_path: str, package_name: str, file_type: str = 'apk', logger=None,
                timeout: int = 1200, runner=None) -> bool:
    """安装应用包（支持APK/IPA/HAP）
    
    Args:
        device: 设备对象
        package_path: 安装包文件路径
        package_name: 包名
        file_type: 文件类型（apk/ipa/hap）
        logger: 日志记录器
        timeout: 超时时间（秒），默认1200秒（20分钟）
        runner: 测试运行器对象，用于收集错误信息
    
    Returns:
        bool: 安装是否成功
    """
    try:
        device_info = device.device_info()
        if device_info and logger:
            logger.info(
                f"设备型号: {device_info.get('model', 'Unknown')}, app_path:{package_path};开始安装app...（超时时间: {timeout}秒/{timeout // 60}分钟）")

        if file_type == 'apk':
            ok = install_android_package(device, package_path, logger, timeout, runner)
        elif file_type == 'ipa':
            ok = install_ios_package(device, package_path, package_name, logger, timeout, runner)
        elif file_type == 'hap':
            ok = install_harmonyos_package(device, package_path, logger, timeout, runner)
        else:
            error_msg = f"不支持的文件类型: {file_type}"
            if logger:
                logger.error(error_msg)
            if runner:
                runner.add_error_summary(error_msg)
            return False

        if not ok:
            # 详细错误信息已经在具体的安装函数中收集了，这里不再重复
            if logger:
                logger.error(f"应用包安装失败: {package_path}")
            return False

        # 安装成功后做一次冷启动并截图
        try:
            device.start_app(package_name)
            time.sleep(5)
            global g_case_base_dir
            device.screenshot("install_res", g_case_base_dir)
        except Exception as post_e:
            if logger:
                logger.warning(f"安装后启动/截图失败（忽略）: {post_e}")
        return True
    except Exception as e:
        error_msg = f"安装流程异常: {str(e)}"
        if logger:
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
        if runner:
            runner.add_error_summary(error_msg)
        return False


def install_android_package(device, apk_path: str, logger=None, timeout: int = 1200, runner=None) -> bool:
    """安装Android APK包
    
    Args:
        device: 设备对象
        apk_path: APK文件路径
        logger: 日志记录器
        timeout: 超时时间（秒），默认1200秒（20分钟）
    
    Returns:
        bool: 安装是否成功
    """
    try:
        if logger:
            logger.info(f"开始安装APK: {apk_path}，超时时间: {timeout}秒（{timeout // 60}分钟）")

        # 使用线程池执行器实现超时控制
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(device.local_install_app, apk_path)
            try:
                result = future.result(timeout=timeout)
                if not bool(result):
                    error_msg = "APK安装返回失败（ubox_py_sdk返回False，请查看日志获取详细错误信息）"
                    if logger:
                        logger.error(error_msg)
                    if runner:
                        runner.add_error_summary(error_msg)
                    return False
                if logger:
                    logger.info("APK安装完成")
                return True
            except FutureTimeoutError:
                error_msg = f"APK安装超时（超过{timeout}秒/{timeout // 60}分钟）: {apk_path}"
                if logger:
                    logger.error(error_msg)
                if runner:
                    runner.add_error_summary(error_msg)
                # 尝试取消任务（虽然可能已经在执行了）
                future.cancel()
                # 不等待任务完成，立即关闭线程池
                executor.shutdown(wait=False)
                return False
            except Exception as install_exc:
                # 捕获安装过程中的异常，获取详细错误信息
                error_type = type(install_exc).__name__
                error_msg = f"APK安装异常: {error_type}: {str(install_exc)}"
                if logger:
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if runner:
                    runner.add_error_summary(error_msg)
                    # 尝试从异常中提取关键信息
                    exc_str = str(install_exc)
                    if exc_str and len(exc_str) > 0:
                        # 如果异常信息包含关键错误描述，添加它
                        if 'install' in exc_str.lower() or 'failed' in exc_str.lower() or 'error' in exc_str.lower():
                            runner.add_error_summary(f"详细错误: {exc_str}")
                return False
        finally:
            # 确保线程池被关闭（如果还没关闭的话）
            try:
                executor.shutdown(wait=False)
            except Exception:
                pass
    except Exception as e:
        error_msg = f"Android包安装异常: {str(e)}"
        if logger:
            logger.error(error_msg)
        if runner:
            runner.add_error_summary(error_msg)
        return False


def install_ios_package(device, ipa_path: str, package_name: str, logger=None, timeout: int = 1200,
                        runner=None) -> bool:
    """安装iOS IPA包
    
    Args:
        device: 设备对象
        ipa_path: IPA文件路径
        package_name: resign_bundle
        logger: 日志记录器
        timeout: 超时时间（秒），默认1200秒（20分钟）
    
    Returns:
        bool: 安装是否成功
    """
    try:
        if logger:
            logger.info(f"开始安装IPA: {ipa_path}，超时时间: {timeout}秒（{timeout // 60}分钟）")

        # 使用线程池执行器实现超时控制
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(device.local_install_app, ipa_path, True, package_name)
            try:
                result = future.result(timeout=timeout)
                if not bool(result):
                    error_msg = "IPA安装返回失败（ubox_py_sdk返回False，请查看日志获取详细错误信息）"
                    if logger:
                        logger.error(error_msg)
                    if runner:
                        runner.add_error_summary(error_msg)
                    return False
                if logger:
                    logger.info("IPA安装完成")
                return True
            except FutureTimeoutError:
                error_msg = f"IPA安装超时（超过{timeout}秒/{timeout // 60}分钟）: {ipa_path}"
                if logger:
                    logger.error(error_msg)
                if runner:
                    runner.add_error_summary(error_msg)
                return False
            except Exception as install_exc:
                # 捕获安装过程中的异常，获取详细错误信息
                error_type = type(install_exc).__name__
                error_msg = f"IPA安装异常: {error_type}: {str(install_exc)}"
                if logger:
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if runner:
                    runner.add_error_summary(error_msg)
                    exc_str = str(install_exc)
                    if exc_str and len(exc_str) > 0:
                        if 'install' in exc_str.lower() or 'failed' in exc_str.lower() or 'error' in exc_str.lower():
                            runner.add_error_summary(f"详细错误: {exc_str}")
                return False
    except Exception as e:
        error_msg = f"iOS包安装异常: {str(e)}"
        if logger:
            logger.error(error_msg)
        if runner:
            runner.add_error_summary(error_msg)
        return False


def _process_anr_result(anr_result: dict, case_base_dir: str, logger=None) -> dict:
    """
    处理ANR检测结果：简化字段并移动截图到用例基础目录
    
    Args:
        anr_result: ANR检测原始结果
        case_base_dir: 用例基础目录（g_case_base_dir）
        logger: 日志记录器
        
    Returns:
        dict: 处理后的简化结果（固定字段）
    """
    import shutil

    # 简化的结果字段（固定字段）
    processed_result = {
        'success': anr_result.get('success', False),
        'crash_count': anr_result.get('crash_count', 0),
        'anr_count': anr_result.get('anr_count', 0),
        'screenshots': [],  # 移动后的截图路径列表
    }

    # 处理截图：移动到用例基础目录
    original_screenshots = anr_result.get('screenshots', [])
    if original_screenshots and case_base_dir:
        # 确保目标目录存在
        if not os.path.exists(case_base_dir):
            os.makedirs(case_base_dir, exist_ok=True)

        for screenshot_path in original_screenshots:
            if os.path.exists(screenshot_path):
                try:
                    # 获取截图文件名
                    screenshot_filename = os.path.basename(screenshot_path)
                    # 目标路径：用例基础目录
                    dest_path = os.path.join(case_base_dir, screenshot_filename)

                    # 移动文件（如果目标文件已存在，先删除）
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    shutil.move(screenshot_path, dest_path)

                    # 记录移动后的路径
                    processed_result['screenshots'].append(dest_path)

                    if logger:
                        logger.info(f"ANR截图已移动到用例基础目录: {dest_path}")
                except Exception as e:
                    if logger:
                        logger.warning(f"移动ANR截图失败: {screenshot_path} -> {case_base_dir}, 错误: {e}")
                    # 移动失败时，保留原始路径
                    processed_result['screenshots'].append(screenshot_path)
            else:
                # 文件不存在，跳过
                if logger:
                    logger.warning(f"ANR截图文件不存在: {screenshot_path}")
    elif original_screenshots:
        # 没有用例基础目录，保留原始路径
        processed_result['screenshots'] = original_screenshots
        if logger:
            logger.warning("无法获取用例基础目录，ANR截图保留在原位置")

    return processed_result


def install_harmonyos_package(device, hap_path: str, logger=None, timeout: int = 1200, runner=None) -> bool:
    """安装鸿蒙HAP包
    
    Args:
        device: 设备对象
        hap_path: HAP文件路径
        logger: 日志记录器
        timeout: 超时时间（秒），默认1200秒（20分钟）
    
    Returns:
        bool: 安装是否成功
    """
    try:
        if logger:
            logger.info(f"开始安装HAP: {hap_path}，超时时间: {timeout}秒（{timeout // 60}分钟）")

        # 使用线程池执行器实现超时控制
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(device.local_install_app, hap_path)
            try:
                result = future.result(timeout=timeout)
                if not bool(result):
                    error_msg = "HAP安装返回失败（ubox_py_sdk返回False，请查看日志获取详细错误信息）"
                    if logger:
                        logger.error(error_msg)
                    if runner:
                        runner.add_error_summary(error_msg)
                    return False
                if logger:
                    logger.info("HAP安装完成")
                return True
            except FutureTimeoutError:
                error_msg = f"HAP安装超时（超过{timeout}秒/{timeout // 60}分钟）: {hap_path}"
                if logger:
                    logger.error(error_msg)
                if runner:
                    runner.add_error_summary(error_msg)
                return False
            except Exception as install_exc:
                # 捕获安装过程中的异常，获取详细错误信息
                error_type = type(install_exc).__name__
                error_msg = f"HAP安装异常: {error_type}: {str(install_exc)}"
                if logger:
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if runner:
                    runner.add_error_summary(error_msg)
                    exc_str = str(install_exc)
                    if exc_str and len(exc_str) > 0:
                        if 'install' in exc_str.lower() or 'failed' in exc_str.lower() or 'error' in exc_str.lower():
                            runner.add_error_summary(f"详细错误: {exc_str}")
                return False
    except Exception as e:
        error_msg = f"鸿蒙包安装异常: {str(e)}"
        if logger:
            logger.error(error_msg)
        if runner:
            runner.add_error_summary(error_msg)
        return False


def run_framework(config_file_path: Optional[str] = None) -> int:
    """
    运行测试框架的主入口函数
    
    Args:
        config_file_path: 配置文件路径，如果为None则使用默认路径（当前目录下的config.yml）
    
    Returns:
        int: 退出码（0表示成功，其他值表示各种错误）
    """
    global g_log_file_dir, g_case_base_dir

    # 确定配置文件路径
    if config_file_path is None:
        # 默认使用当前工作目录下的 config.yml
        # 通常 start_test.py 和 config.yml 在同一目录
        config_file_path = os.path.join(os.getcwd(), 'config.yml')
        # 如果当前目录没有，尝试从调用者的文件位置推断
        if not os.path.exists(config_file_path):
            import inspect
            try:
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    caller_file = frame.f_back.f_globals.get('__file__', '')
                    if caller_file:
                        config_file_path = os.path.join(os.path.dirname(os.path.abspath(caller_file)), 'config.yml')
            except Exception:
                pass
            finally:
                if 'frame' in locals():
                    del frame
    else:
        config_file_path = os.path.abspath(config_file_path)

    # 设置结果目录
    root_path = os.path.dirname(os.path.dirname(os.getcwd()))
    test_result_dir = os.path.join(root_path, 'test_result')
    log_base_dir = os.path.join(test_result_dir, 'log')
    case_base_dir = os.path.join(test_result_dir, 'case')

    # 创建基础目录结构
    make_dir(log_base_dir)
    make_dir(case_base_dir)
    g_log_file_dir = log_base_dir
    g_case_base_dir = case_base_dir

    # 加载配置
    try:
        config_manager = ConfigManager(config_file_path)
        config = config_manager.load_config()

        if not config_manager.validate_task_config():
            print("任务配置验证失败")
            return RUNNER_ERROR

        # 初始化日志（从配置文件读取日志级别，默认INFO）
        log_file_path = os.path.join(log_base_dir, 'client_log.txt')
        log_level_str = config.log_level.upper() if hasattr(config, 'log_level') and config.log_level else 'INFO'
        log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level = log_level_map.get(log_level_str, logging.INFO)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info(f"从配置文件读取启动参数，日志级别: {log_level_str}")

        i_job_id = config.task.job_id
        g_serial_num = config.task.serial_num
        i_os_type = config.task.os_type
        i_app_name = config.task.app_name
        i_auth_code = config.task.auth_code

        logger.info(f'---UTEST测试--- job_id={i_job_id}, serial_num={g_serial_num}, '
                    f'os_type={i_os_type}, auth_code={i_auth_code}, app_name={i_app_name}, test_result_path={test_result_dir}')

        # 确定平台类型
        platform_map = {
            "android": OSType.ANDROID,
            "ios": OSType.IOS,
            "hm": OSType.HM
        }
        platform = platform_map.get(i_os_type.lower(), OSType.ANDROID)

        # 更新配置
        config.device.udid = g_serial_num
        config.device.os_type = platform
        config.device.auth_code = i_auth_code

        # 解析应用来源
        # 从配置中获取安装控制参数（如果配置了）
        need_install_config = config.task.need_install if hasattr(config.task, 'need_install') else None
        app_info = parse_app_source(i_app_name, logger, need_install=need_install_config)
        logger.info(f"应用来源解析: {app_info}")
        if need_install_config is not None:
            logger.info(f"安装控制参数已设置: need_install={need_install_config}")

        # 处理 resource 参数
        # 资源信息结构说明：
        # - 固定属性（一定存在）：type（资源类型）、usageId（使用ID）
        # - 平台自定义配置：其他所有字段都是平台自定义的，根据平台和资源类型不同而变化
        # - 用例类型（type="用例"）一定有 name 字段
        # - QQ类型（type="QQ"）一定有 id 和 pwd 字段
        resource_list = config.task.resource if hasattr(config.task, 'resource') else []

        # 检查是否有 type 为 "用例" 的资源项（只取第一个）
        case_resource = None
        if resource_list:
            for r in resource_list:
                if isinstance(r, dict) and r.get('type') == '用例':
                    case_resource = r
                    break  # 只取第一个用例资源

        if case_resource:
            # 提取用例名称（用例类型一定有 name 字段）
            case_name = case_resource.get('name')
            usage_id = case_resource.get('usageId')

            if case_name:
                # 更新 selected_tests，resource 中的用例优先级高于配置文件
                config.test.selected_tests = [case_name]
                logger.info(f"从 resource 参数中提取到用例: {case_name}，将覆盖配置文件中的 selected_tests")

            # 将 usageId 拼接到 case_base_dir
            if usage_id:
                usage_id_str = str(usage_id)
                case_base_dir = os.path.join(test_result_dir, 'case', usage_id_str)
                # 重新创建目录
                make_dir(case_base_dir)
                # 更新全局变量（已在函数开头声明 global）
                g_case_base_dir = case_base_dir
                logger.info(f"根据 resource 中的 usageId 更新 case_base_dir: {case_base_dir}")

    except Exception as e:
        log_exception_once("框架准备失败", e, logger)
        return RUNNER_ERROR

    # 初始化运行器
    runner_cm = None
    runner = None
    final_exit_code = SUCCESS

    try:
        runner_cm = TestRunner(config, log_file_path)
        final_exit_code = SUCCESS
        results = []
        anr_monitor_result = None
        can_run = True

        # 初始化设备
        try:
            runner_cm.__enter__()
        except Exception as init_e:
            # 收集详细的错误信息，包括异常类型和消息
            error_type = type(init_e).__name__
            error_msg = f"设备初始化失败: {error_type}: {str(init_e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if runner_cm:
                runner_cm.add_error_summary(error_msg)
                # 如果有traceback，提取关键信息（最后几行）
                try:
                    tb_lines = traceback.format_exc().split('\n')
                    # 提取最后3行非空的关键错误信息
                    key_lines = [line.strip() for line in tb_lines[-10:] if
                                 line.strip() and not line.strip().startswith('File')]
                    if key_lines:
                        runner_cm.add_error_summary(f"详细错误: {key_lines[-1]}")
                except:
                    pass
            final_exit_code = DEVICE_OFFLINE
            can_run = False

        runner = runner_cm

        runner.test_context = {
            "package_name": app_info.get('package_name') or i_app_name,
            "job_id": i_job_id,
            "serial_num": g_serial_num,
            "os_type": platform,
            "need_install": app_info['need_install'],
            "app_source_type": app_info['source_type'],
            "package_file_path": app_info.get('file_path'),
            "file_type": app_info.get('file_type'),
            "raw_app_name": i_app_name,
            "test_result_dir": test_result_dir,
            "case_base_dir": case_base_dir,
            "log_base_dir": log_base_dir,
            "resource": resource_list,  # 资源信息列表（每个资源项包含固定属性type和usageId，以及其他平台自定义配置）
        }

        # 创建初始状态的JSON报告文件
        try:
            initial_report_path = runner.create_initial_report()
            logger.info(f"初始JSON报告已创建: {initial_report_path}")
        except Exception as init_report_e:
            logger.warning(f"创建初始JSON报告失败，将在结束时创建完整报告: {init_report_e}")

        # 执行测试流程
        if can_run:
            if platform == OSType.HM:
                # 鸿蒙设备可能是锁屏状态，所以需要初始化一次解锁
                runner.device.init_driver()
                time.sleep(30)
            # 安装应用
            installed = False
            if runner.test_context.get('need_install') and runner.device:
                package_path = runner.test_context.get('package_file_path')
                file_type = runner.test_context.get('file_type', 'apk')
                if package_path and os.path.exists(package_path):
                    installed = install_pkg(
                        runner.device,
                        package_path,
                        runner.test_context.get('package_name'),
                        file_type,
                        logger,
                        timeout=1200,
                        runner=runner  # 传递runner，让安装函数直接收集详细错误信息
                    )
                    if not installed:
                        # 详细错误信息已经在install_pkg内部收集了
                        final_exit_code = INSTALL_ERROR
                else:
                    error_msg = f"应用包文件不存在: {package_path}"
                    logger.error(error_msg)
                    runner.add_error_summary(error_msg)
                    final_exit_code = INSTALL_ERROR
            else:
                runner.device.start_app(runner.test_context.get('package_name'))
                time.sleep(5)
                runner.device.screenshot("installed_res", g_case_base_dir)
                logger.info("无需安装应用包，按包名直接启动")

            # 执行测试
            execute_tests = (final_exit_code == SUCCESS)
            if execute_tests:
                # 创建测试用例集合
                try:
                    selected_tests = config.test.selected_tests
                    if selected_tests and len(selected_tests) > 0:
                        logger.info(f"运行指定的测试用例: {selected_tests}")
                        test_suite = create_test_collection(selected_tests, device=runner.device)
                    else:
                        logger.info("运行所有测试用例")
                        test_suite = create_test_collection(device=runner.device)
                except RuntimeError as e:
                    error_type = type(e).__name__
                    error_msg = f"创建测试用例集合失败: {error_type}: {str(e)}"
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                    runner.add_error_summary(error_msg)
                    # 提取关键错误信息
                    try:
                        tb_lines = traceback.format_exc().split('\n')
                        key_lines = [line.strip() for line in tb_lines[-5:] if
                                     line.strip() and ('Error' in line or 'Exception' in line)]
                        if key_lines:
                            runner.add_error_summary(f"详细错误: {key_lines[-1]}")
                    except:
                        pass
                    final_exit_code = RUNNER_ERROR
                    test_suite = None

                # 开启ANR检测（根据配置决定是否启用）
                anr_start_success = False
                enable_anr_monitor = config.test.enable_anr_monitor
                if enable_anr_monitor and platform in [OSType.ANDROID, OSType.HM] and runner.device:
                    logger.info("ANR/Crash监控已启用")
                    try:
                        logger.info("尝试停止一有的anr检测任务，防止同时有两个anr监听")
                        runner.device.anr_stop()
                    except Exception:
                        logger.warning("无需停止anr")
                    try:
                        anr_start_success = runner.device.anr_start(
                            package_name=runner.test_context.get('package_name'))
                        if anr_start_success:
                            logger.info("ANR/Crash监控启动成功")
                        else:
                            logger.warning("ANR/Crash监控启动失败")
                    except Exception as anr_start_e:
                        logger.warning(f"启动ANR监控失败，忽略: {anr_start_e}")
                        anr_start_success = False
                elif not enable_anr_monitor:
                    logger.info("ANR/Crash监控已禁用（配置中 enable_anr_monitor: false）")

                # 执行测试套件
                try:
                    results = runner.run_test_suite(test_suite)
                except Exception as run_e:
                    error_type = type(run_e).__name__
                    error_msg = f"运行阶段异常: {error_type}: {str(run_e)}"
                    log_exception_once("运行阶段异常", run_e, logger)
                    runner.add_error_summary(error_msg)
                    # 提取关键错误信息
                    try:
                        tb_lines = traceback.format_exc().split('\n')
                        key_lines = [line.strip() for line in tb_lines[-5:] if
                                     line.strip() and ('Error' in line or 'Exception' in line or 'Traceback' in line)]
                        if key_lines:
                            runner.add_error_summary(f"详细错误: {key_lines[-1]}")
                    except:
                        pass
                    final_exit_code = RUNNER_ERROR

                # 卸载应用
                if installed:
                    try:
                        runner.device.uninstall_app(runner.test_context.get('package_name'))
                    except Exception as uninstall_e:
                        logger.warning(f"卸载阶段异常忽略: {uninstall_e}")

                # 结束ANR检测
                if anr_start_success:
                    try:
                        anr_monitor_result = runner.device.anr_stop(g_log_file_dir)
                    except Exception as anr_stop_e:
                        logger.warning(f"停止ANR监控异常，忽略: {anr_stop_e}")
                        anr_monitor_result = None

                    if anr_monitor_result:
                        # 处理ANR结果：简化字段并移动截图到用例基础目录
                        processed_result = _process_anr_result(anr_monitor_result, g_case_base_dir, logger)
                        runner.set_global_monitor_result(processed_result)
                        anr_count = processed_result.get("anr_count", 0)
                        crash_count = processed_result.get("crash_count", 0)

                        if anr_count > 0:
                            error_msg = f"检测到ANR事件，数量: {anr_count}"
                            logger.error(error_msg)
                            runner.add_error_summary(error_msg)
                            final_exit_code = ANR
                        elif crash_count > 0:
                            error_msg = f"检测到Crash事件，数量: {crash_count}"
                            logger.error(error_msg)
                            runner.add_error_summary(error_msg)
                            final_exit_code = CRASH

                # 检查测试结果
                if final_exit_code not in (ANR, CRASH):
                    failed_tests = [r for r in results if r.status.value == "failed"]
                    error_tests = [r for r in results if r.status.value == "error"]

                    if error_tests:
                        error_msg = f"测试错误: {len(error_tests)} 个测试用例出错"
                        logger.error(error_msg)
                        runner.add_error_summary(error_msg)
                        # 添加前3个错误用例的详细信息
                        for test in error_tests[:3]:
                            runner.add_error_summary(f"  - {test.test_name}: {test.error_message}")
                        final_exit_code = RUNNER_ERROR
                    elif failed_tests:
                        error_msg = f"测试失败: {len(failed_tests)} 个测试用例失败"
                        logger.error(error_msg)
                        runner.add_error_summary(error_msg)
                        # 添加前3个失败用例的详细信息
                        for test in failed_tests[:3]:
                            runner.add_error_summary(f"  - {test.test_name}: {test.error_message}")
                        final_exit_code = SCRIPT_ASSERT_ERROR
                    else:
                        logger.info(f"测试成功: {len(results)} 个测试用例全部通过")
                        final_exit_code = SUCCESS

    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"测试执行异常: {error_type}: {str(e)}"
        log_exception_once("测试执行异常", e, logger)
        if runner is not None:
            runner.add_error_summary(error_msg)
            # 提取关键错误信息
            try:
                tb_lines = traceback.format_exc().split('\n')
                key_lines = [line.strip() for line in tb_lines[-5:] if
                             line.strip() and ('Error' in line or 'Exception' in line)]
                if key_lines:
                    runner.add_error_summary(f"详细错误: {key_lines[-1]}")
            except:
                pass
        final_exit_code = RUNNER_ERROR
    finally:
        # 生成报告
        if runner is not None:
            try:
                rp2 = runner.generate_report(exit_code=final_exit_code)
                logger.info(f"测试报告生成: {rp2}")
            except Exception as rpt2_e:
                logger.error(f"报告生成失败: {rpt2_e}")
        else:
            logger.warning("runner 未初始化，跳过报告生成")

        # 释放资源
        if runner_cm is not None:
            try:
                runner_cm.__exit__(None, None, None)
            except Exception as ee:
                logger.warning(f"资源释放异常: {ee}")

        # 关闭所有日志处理器，确保日志写入完成
        try:
            # 刷新所有日志处理器
            for handler in logging.root.handlers[:]:
                handler.flush()
            logger.info("日志已刷新")
        except Exception as log_e:
            logger.warning(f"刷新日志异常: {log_e}")

    # 使用os._exit而不是sys.exit，避免被其他异常处理捕获
    logger.info(f"测试完成，退出码: {final_exit_code}")
    return final_exit_code
