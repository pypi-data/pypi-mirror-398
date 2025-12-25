"""
稳定性测试CI工具模块

提供稳定性测试相关的工具函数，包括操作记录和Activity记录的保存功能。
"""

import os
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OperationRecord:
    """操作记录"""
    round_num: int  # 轮次编号
    operation: str  # 操作类型：点击、上滑、返回键、重启应用
    position: str = None  # 操作位置，如坐标 (x, y)
    activity: str = "未知"  # 所在页面
    screenshot: str = None  # 截图地址
    timestamp: str = ""  # 操作时间戳
    element_info: dict = None  # 元素信息（resource-id、class、text、content-desc等），仅点击操作有值


def save_operation_records(operation_records: List[OperationRecord], log_dir: str) -> None:
    """
    保存操作记录到文件
    
    Args:
        operation_records: 操作记录列表
        log_dir: 日志目录
    """
    try:
        # 保存为JSON格式
        json_file = os.path.join(log_dir, 'operation_records.json')
        records_data = []
        for record in operation_records:
            records_data.append({
                'round_num': record.round_num,
                'operation': record.operation,
                'position': record.position,
                'activity': record.activity,
                'screenshot': record.screenshot,
                'timestamp': record.timestamp
            })
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records_data, f, ensure_ascii=False, indent=2)
        
        # 保存为文本格式（便于阅读）
        txt_file = os.path.join(log_dir, 'operation_records.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("稳定性测试操作记录\n")
            f.write("=" * 80 + "\n\n")
            
            for record in operation_records:
                f.write(f"轮次 {record.round_num}: {record.operation}\n")
                if record.position:
                    f.write(f"  位置: {record.position}\n")
                # 如果有元素信息，显示详细信息
                if record.element_info:
                    f.write(f"  元素信息:\n")
                    if record.element_info.get('resource_id'):
                        f.write(f"    resource-id: {record.element_info.get('resource_id')}\n")
                    if record.element_info.get('text'):
                        f.write(f"    text: {record.element_info.get('text')}\n")
                    if record.element_info.get('content_desc'):
                        f.write(f"    content-desc: {record.element_info.get('content_desc')}\n")
                    if record.element_info.get('class'):
                        f.write(f"    class: {record.element_info.get('class')}\n")
                f.write(f"  页面: {record.activity}\n")
                if record.screenshot:
                    f.write(f"  截图: {record.screenshot}\n")
                f.write(f"  时间: {record.timestamp}\n")
                f.write("-" * 80 + "\n\n")
        
        logger.info(f'操作记录已保存: {json_file} 和 {txt_file}')
    except Exception as e:
        logger.error(f'保存操作记录失败: {e}')


def save_activity_records(activity_records: Dict[str, Dict[str, Any]], log_dir: str) -> None:
    """
    保存Activity记录到文件
    
    Args:
        activity_records: Activity记录字典
        log_dir: 日志目录
    """
    try:
        # 保存为JSON格式
        json_file = os.path.join(log_dir, 'activity_records.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(activity_records, f, ensure_ascii=False, indent=2)
        
        # 保存为文本格式（便于阅读）
        txt_file = os.path.join(log_dir, 'activity_records.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("稳定性测试Activity访问记录\n")
            f.write("=" * 80 + "\n\n")
            
            # 按访问次数排序
            sorted_activities = sorted(activity_records.items(), 
                                     key=lambda x: x[1]['visit_count'], 
                                     reverse=True)
            
            for activity, info in sorted_activities:
                f.write(f"Activity: {activity}\n")
                f.write(f"  首次访问: {info['first_visit']}\n")
                f.write(f"  最后访问: {info['last_visit']}\n")
                f.write(f"  访问次数: {info['visit_count']}\n")
                f.write("-" * 80 + "\n\n")
        
        logger.info(f'Activity记录已保存: {json_file} 和 {txt_file}')
    except Exception as e:
        logger.error(f'保存Activity记录失败: {e}')
