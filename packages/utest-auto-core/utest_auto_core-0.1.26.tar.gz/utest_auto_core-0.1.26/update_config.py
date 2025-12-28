#!/usr/bin/env python3
"""
更新配置文件中的任务参数
"""

import sys
import os
import json
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from ubox_py_sdk import RunMode


def update_task_config(job_id, serial_num, os_type, app_name, auth_code=None, resource_list=None):
    """
    更新配置文件中的任务参数
    
    Args:
        job_id: 任务ID
        serial_num: 设备序列号
        os_type: 操作系统类型
        app_name: 应用包名
        auth_code: 设备认证码（可选）
        resource_list: 资源信息列表（可选，每个元素是JSON字符串）
        
    资源信息说明：
        每个资源项是一个JSON对象，包含以下结构：
        - 固定属性（一定存在）：
          * type: 资源类型（如："其他自定义"、"QQ"、"用例"等）
          * usageId: 使用ID（如："10970602"）
        - 平台自定义配置（动态字段，根据平台和资源类型不同而变化）：
          * 其他所有字段都是平台自定义的，可能包括：username、password、config1、label等
        - 特殊类型字段要求：
          * 用例类型（type="用例"）：一定有 name 字段（用例名称）
          * QQ类型（type="QQ"）：一定有 id 和 pwd 字段
    """
    # 配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')

    try:
        # 解析资源信息列表
        resource = []
        if resource_list:
            for resource_str in resource_list:
                try:
                    # 尝试解析JSON字符串
                    resource_item = json.loads(resource_str)
                    resource.append(resource_item)
                except json.JSONDecodeError as e:
                    print(f"⚠️ 警告：无法解析资源信息 '{resource_str}'，跳过: {e}")
                    continue
        
        # 使用ConfigManager更新config
        config_manager = ConfigManager(config_path)
        config_manager.update_config(job_id, serial_num, os_type, app_name, RunMode.NORMAL, auth_code, resource)

        print(f"配置文件已更新: job_id={job_id}, serial_num={serial_num}, os_type={os_type}, app_name={app_name}, mode=normal")
        if resource:
            print(f"资源信息已更新: 共 {len(resource)} 项")
        return True

    except Exception as e:
        print(f"更新配置文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("用法: uv run update_config.py <job_id> <serial_num> <os_type> <app_name> [auth_code] [resource1] [resource2] ...")
        print("resource参数: 每个resource是一个JSON字符串，会被解析并添加到resource列表中")
        print("资源信息结构说明:")
        print("  - 固定属性（一定存在）: type（资源类型）、usageId（使用ID）")
        print("  - 平台自定义配置: 其他所有字段都是平台自定义的，根据平台和资源类型不同而变化")
        print("  - 特殊类型字段要求:")
        print("    * 用例类型（type=\"用例\"）: 一定有 name 字段（用例名称）")
        print("    * QQ类型（type=\"QQ\"）: 一定有 id 和 pwd 字段")
        sys.exit(1)

    job_id = sys.argv[1]
    serial_num = sys.argv[2]
    os_type = sys.argv[3]
    app_name = sys.argv[4]
    auth_code = sys.argv[5] if len(sys.argv) > 5 else None
    
    # 第6个参数及以后都是资源信息（JSON字符串）
    resource_list = sys.argv[6:] if len(sys.argv) > 6 else None

    success = update_task_config(job_id, serial_num, os_type, app_name, auth_code, resource_list)
    sys.exit(0 if success else 1)
