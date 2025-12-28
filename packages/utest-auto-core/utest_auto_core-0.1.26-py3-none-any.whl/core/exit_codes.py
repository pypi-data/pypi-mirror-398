#!/usr/bin/env python3
"""
退出码常量定义

与服务端编号一致，所有退出码相关的定义都在这里统一维护
"""

# 返回码定义（与服务端编号一致）
SUCCESS = 0  # 成功
RUNNER_ERROR = 2  # 其他脚本异常
INSTALL_ERROR = 3  # 安装失败
SCRIPT_ASSERT_ERROR = 5  # 脚本断言失败
DEVICE_OFFLINE = 10  # 手机掉线
CRASH = 17  # 应用崩溃
ANR = 18  # 应用无响应

# 退出码描述映射
EXIT_CODE_DESCRIPTIONS = {
    None: "未正常执行完成并生成报告，可能任务超时停止",
    SUCCESS: "任务正常执行完成",
    RUNNER_ERROR: "脚本执行异常",
    INSTALL_ERROR: "应用安装失败",
    SCRIPT_ASSERT_ERROR: "测试用例断言失败",
    DEVICE_OFFLINE: "设备离线",
    CRASH: "应用崩溃",
    ANR: "应用无响应(ANR)",
}

# 退出码状态映射
EXIT_CODE_STATUS = {
    SUCCESS: "success",
    # 其他所有退出码都是失败状态
}

def get_exit_code_description(exit_code) -> str:
    """
    根据退出码获取对应的描述信息
    
    Args:
        exit_code: 退出码
        
    Returns:
        str: 退出码对应的描述信息
    """
    if exit_code in EXIT_CODE_DESCRIPTIONS:
        return EXIT_CODE_DESCRIPTIONS[exit_code]
    else:
        return f"任务异常结束，退出码: {exit_code}"

def get_exit_code_status(exit_code) -> str:
    """
    根据退出码获取对应的状态
    
    Args:
        exit_code: 退出码
        
    Returns:
        str: 退出码对应的状态（"success" 或 "failed"）
    """
    return EXIT_CODE_STATUS.get(exit_code, "failed")

