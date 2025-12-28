"""
文件操作工具模块

提供文件和目录操作的实用函数。
"""

import os
from typing import Optional


def make_dir(path: str) -> None:
    """
    创建目录，如果目录已存在则忽略
    
    Args:
        path (str): 要创建的目录路径
    """
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except Exception as e:
        print("make_dir Exception:" + str(e))


def del_dir(path, p=True, except_files: Optional[list] = None) -> None:
    """
    删除目录及其内容
    
    Args:
        path (str): 要删除的目录路径
        p (bool): 是否删除根目录，默认为True
        except_files (list): 不删除的文件名列表
    """
    if except_files is None:
        except_files = []
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name not in except_files:
                    os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        if p:
            os.rmdir(path)
