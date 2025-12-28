"""
工具包模块

提供各种实用工具函数，包括文件操作、目录管理、UI遍历、稳定性测试等功能。
"""

# 文件操作工具
from .file_utils import make_dir, del_dir

# 稳定性测试工具
from .stability_ci import OperationRecord, save_operation_records, save_activity_records

# UI遍历工具
from .traversal_ci import TraversalCI
from .traversal_util import (
    split_image,
    hist_similar,
    calc_similar,
    calc_similar_by_path,
    make_regular_image,
    dis_match,
    judge_match_file,
    judge_screen_color,
    get_current_package_dump_str,
    paint_res_on_screenshot,
)

__all__ = [
    # 文件操作
    'make_dir',
    'del_dir',
    # 稳定性测试工具
    'OperationRecord',
    'save_operation_records',
    'save_activity_records',
    # UI遍历
    'TraversalCI',
    'split_image',
    'hist_similar',
    'calc_similar',
    'calc_similar_by_path',
    'make_regular_image',
    'dis_match',
    'judge_match_file',
    'judge_screen_color',
    'get_current_package_dump_str',
    'paint_res_on_screenshot',
]
