"""
UI遍历CI模块

提供基于CI场景的UI自动遍历功能，用于稳定性测试。
"""

import datetime
import logging
import os
import random
import re
from typing import Optional, Tuple
import xml.etree.cElementTree as ElementTree
from ubox_py_sdk import Device

from core.utils.traversal_util import (
    judge_match_file,
    get_current_package_dump_str, judge_screen_color
)

logger = logging.getLogger(__name__)

# 黑名单配置
BLACK_CONTROL_LIST = {
    'com.tencent.qqmusic': [
        ['《用户许可协议》', '《隐私政策》'],  # text黑名单
        ['com.tencent.qqmusic:id/aur', 'com.tencent.qqmusic:id/main_desk_title_more_btn'],  # resource-id黑名单
        ['分享到微信好友', '分享到微信朋友圈', '分享到QQ好友', '分享到QQ空间',
         '分享到新浪微博', '私信', '复制链接', '生成分享二维码']  # content-desc黑名单
    ],
    'com.tencent.ttpic': [
        [],  # text黑名单
        ['com.tencent.ttpic:id/btn_settings_container'],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.tencent.mobileqq': [
        ['服务条款', '使用条款', '隐私政策', '服务声明'],  # text黑名单
        [],  # resource-id黑名单
        ['帐户及设置']  # content-desc黑名单
    ],
    'com.tencent.now': [
        ['设置'],  # text黑名单
        ['com.tencent.now:id/ab5', 'com.tencent.now:id/ab7', 'com.tencent.now:id/ab9',
         'com.tencent.now:id/aba', 'com.tencent.now:id/abc'],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.tencent.wework': [
        ['已阅读并同意 软件许可及服务协议 和 隐私政策'],  # text黑名单
        ['com.tencent.wework:id/d0m'],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.tencent.qgame': [
        ['《企鹅电竞用户协议》'],  # text黑名单
        ['com.tencent.qgame:id/ivTitleBtnRightImage', 'com.tencent.qgame:id/share_qq_friend',
         'com.tencent.qgame:id/share_qzone', 'com.tencent.qgame:id/share_wechat_friend',
         'com.tencent.qgame:id/share_wechat_circle'],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.qzone': [
        ['设置'],  # text黑名单
        [],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.tencent.weishi': [
        [],  # text黑名单
        ['com.tencent.weishi:id/feed_share_status_container',
         'com.tencent.weishi:id/iv_title_bar_share',
         'com.tencent.weishi:id/iv_setting_btn'],  # resource-id黑名单
        []  # content-desc黑名单
    ],
    'com.tencent.karaoke': [
        ['服务许可协议', '隐私政策'],  # text黑名单
        [],  # resource-id黑名单
        ['设置']  # content-desc黑名单
    ]
}


class TraversalCI:
    """
    UI遍历CI类
    
    用于自动化UI遍历，支持黑名单过滤、相似页面检测等功能。
    """
    
    def __init__(self, device: Device=None):
        """
        初始化遍历器
        
        Args:
            device: ubox设备对象
        """
        self.device = device
        self.job_type = '0'
        self.top_side_elements = []
        self.click_able_elements = {}
        self._element_map = {}  # 用于存储key到元素的映射，便于获取元素详细信息
    
    def get_topside_elems_except_black_list(self, tree: ElementTree.Element, pkg_name: str) -> None:
        """
        获取顶层可点击元素（排除黑名单）
        
        Args:
            tree: XML元素树
            pkg_name: 包名
        """
        try:
            # 检查是否是ViewGroup且最后一个子元素可点击
            if tree.attrib.get('class') == 'android.view.ViewGroup':
                if len(tree) > 0 and tree[-1].attrib.get('clickable') == 'true':
                    # 检查黑名单
                    if pkg_name in BLACK_CONTROL_LIST:
                        black_list = BLACK_CONTROL_LIST[pkg_name]
                        elem = tree[-1]
                        text = elem.attrib.get('text', '')
                        resource_id = elem.attrib.get('resource-id', '')
                        content_desc = elem.attrib.get('content-desc', '')
                        
                        # 检查是否在黑名单中
                        if (text not in black_list[0] and
                            resource_id not in black_list[1] and
                            content_desc not in black_list[2]):
                            self.top_side_elements.append(elem)
                    else:
                        # 不在黑名单配置中，直接添加
                        self.top_side_elements.append(tree[-1])
                    
                    # 递归处理最后一个子元素
                    self.get_topside_elems_except_black_list(tree[-1], pkg_name)
                    return
        except Exception as e:
            logger.error(f"--get topside elems-- failed!!!!! Exception={e}")
        
        # 遍历所有子元素
        for elem in tree:
            try:
                if elem.attrib.get('clickable') == 'true':
                    # 检查黑名单
                    if pkg_name in BLACK_CONTROL_LIST:
                        black_list = BLACK_CONTROL_LIST[pkg_name]
                        text = elem.attrib.get('text', '')
                        resource_id = elem.attrib.get('resource-id', '')
                        content_desc = elem.attrib.get('content-desc', '')
                        
                        # 检查是否在黑名单中
                        if (text not in black_list[0] and
                            resource_id not in black_list[1] and
                            content_desc not in black_list[2]):
                            self.top_side_elements.append(elem)
                    else:
                        # 不在黑名单配置中，直接添加
                        self.top_side_elements.append(elem)
            except Exception as e:
                logger.error(f"处理元素时出错: {e}")
            
            # 递归处理子元素
            self.get_topside_elems_except_black_list(elem, pkg_name)
    
    def automatic_traversal_get_click_point(self, screenshot_filename: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """
        获取点击坐标点和元素key
        
        Args:
            screenshot_filename: 截图文件名
            
        Returns:
            Tuple: (center_x, center_y, flag, element_key)
                - center_x, center_y: 点击坐标
                - flag: 状态标志（'no_click'、'all_click'或None）
                - element_key: 元素key（格式：resource-id#class#bounds），用于后续获取元素详细信息
        """
        match_flag = False
        bounds = None
        element_key = None
        
        # 在已访问的页面中查找相似图片
        for ce_key, ce_value in self.click_able_elements.items():
            if ce_key == screenshot_filename:
                if not ce_value:
                    # 当前页面可点击元素为空
                    logger.info('--no clickable element--')
                    return None, None, 'no_click', None
                
                # 分离未点击和已点击的元素
                elem_list_un_click = []
                elem_list_clicked = []
                for e_key, e_value in ce_value.items():
                    if e_value == 0:
                        elem_list_un_click.append(e_key)
                    else:
                        elem_list_clicked.append(e_key)
                
                if elem_list_un_click:
                    # 随机选择一个未点击的元素
                    key = elem_list_un_click[random.randint(0, len(elem_list_un_click) - 1)]
                else:
                    # 当前页面可点击元素均被点击过
                    logger.info('--all elements clicked--')
                    return None, None, 'all_click', None
                
                logger.info(f"3-{ce_key}")
                logger.info(f"{self.click_able_elements[ce_key]}")
                
                # 保存元素key
                element_key = key
                # 从bounds中提取坐标
                bounds = key.split('#')[2]
                self.click_able_elements[screenshot_filename][key] += 1
                match_flag = True
                break
        
        if match_flag and bounds:
            # 解析bounds坐标
            pattern = re.compile(r'\d+')
            coord = pattern.findall(bounds)
            if len(coord) >= 4:
                center_x = (int(coord[2]) - int(coord[0])) / 2.0 + int(coord[0])
                center_y = (int(coord[3]) - int(coord[1])) / 2.0 + int(coord[1])
                return center_x, center_y, None, element_key
        
        # 未找到相似页面
        logger.info('--no similar page--')
        return None, None, None, None
    
    def automatic_traversal(self, dump_str: str, pkg_name: str, screenshot_filename: str,
                            step_case_screenshot_path: str, screen_size: Optional[Tuple[int, int]] = None) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str], Optional[dict]]:
        """
        自动遍历分析
        
        Args:
            dump_str: UI层次结构XML字符串
            pkg_name: 包名
            screenshot_filename: 截图文件名
            step_case_screenshot_path: 截图目录路径
            screen_size: 屏幕尺寸（可选）
            
        Returns:
            Tuple: (x, y, flag, match_file, element_info)
                - x, y: 点击坐标
                - flag: 状态标志（'black_screen'、'no_click'、'all_click'或None）
                - match_file: 匹配的截图文件路径
                - element_info: 元素信息字典（包含resource-id、class、bounds等），如果没有则返回None
        """
        start_time1 = datetime.datetime.now()
        
        # 判断屏幕颜色（黑屏/白屏）
        screen_color = judge_screen_color(os.path.join(step_case_screenshot_path,screenshot_filename), screen_size)
        if screen_color == 'black_screen':
            return None, None, 'black_screen', None, None
        elif screen_color == 'white_screen':
            return None, None, 'white_screen', None, None
        
        # 图像识别出相似图片，表示已经访问过此页面
        match_file = judge_match_file(step_case_screenshot_path, screenshot_filename)
        
        # 解析XML并提取可点击元素
        elem_dict = {}
        elem_list = []
        self.top_side_elements = []
        
        tree = get_current_package_dump_str(dump_str, pkg_name)
        if tree is None:
            logger.error("无法解析UI层次结构")
            return None, None, None, None, None
        
        # 获取顶层可点击元素（排除黑名单）
        self.get_topside_elems_except_black_list(tree, pkg_name)
        
        # 构建元素字典（同时保存元素对象以便后续获取详细信息）
        self._element_map = {}  # 用于存储key到元素的映射
        for elem in self.top_side_elements:
            try:
                bounds = elem.attrib.get('bounds', '')
                pattern = re.compile(r'\d+')
                coord = pattern.findall(bounds)
                if len(coord) >= 4 and (int(coord[3]) - int(coord[1])) >= 30:
                    elem_dict_key = (elem.attrib.get('resource-id', '') + '#' +
                                   elem.attrib.get('class', '') + '#' +
                                   bounds)
                    elem_list.append(elem_dict_key)
                    elem_dict[elem_dict_key] = 0
                    # 保存元素对象映射
                    self._element_map[elem_dict_key] = elem
            except Exception as e:
                logger.warning(f"处理元素时出错: {e}")
        
        # 如果没有图像匹配，检查元素列表是否匹配（表示是相同页面）
        if not match_file:
            for ce_key, ce_value in self.click_able_elements.items():
                if ce_value:
                    elem_list_all = []
                    for e_key, e_value in ce_value.items():
                        elem_list_all.append(e_key)
                    
                    # 比较元素列表
                    elem_list_set = list(set(elem_list))
                    elem_list_set.sort()
                    elem_list_all.sort()
                    
                    if elem_list_set == elem_list_all:
                        match_file = os.path.join(step_case_screenshot_path, ce_key)
                        break

        # 更新已访问页面记录
        if not match_file:
            self.click_able_elements[screenshot_filename] = elem_dict
        else:
            screenshot_filename = os.path.basename(match_file)
        
        # 获取点击坐标点和元素key
        center_x, center_y, flag, element_key = self.automatic_traversal_get_click_point(screenshot_filename)
        
        # 如果有元素key，从元素映射中获取完整的元素信息
        element_info = None
        if element_key and element_key in self._element_map:
            elem = self._element_map[element_key]
            # 解析key获取基本信息
            key_parts = element_key.split('#')
            resource_id = key_parts[0] if len(key_parts) > 0 and key_parts[0] else ''
            class_name = key_parts[1] if len(key_parts) > 1 and key_parts[1] else ''
            bounds = key_parts[2] if len(key_parts) > 2 and key_parts[2] else ''
            
            # 构建完整的元素信息字典
            element_info = {
                'resource_id': resource_id,
                'class': class_name,
                'bounds': bounds,
                'text': elem.attrib.get('text', ''),
                'content_desc': elem.attrib.get('content-desc', ''),
            }
        
        return center_x, center_y, flag, match_file, element_info

