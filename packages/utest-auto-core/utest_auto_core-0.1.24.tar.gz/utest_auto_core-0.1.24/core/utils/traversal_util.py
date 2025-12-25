"""
UI遍历工具模块

提供UI遍历相关的工具函数，包括截图相似度匹配、屏幕颜色判断、XML解析等功能。
"""

import os
import logging
import numpy as np
from PIL import Image, ImageDraw
import xml.etree.cElementTree as ElementTree
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def split_image(img: Image.Image, part_size: Tuple[int, int] = (64, 64)) -> list:
    """
    将图片分割成多个部分
    
    Args:
        img: PIL图片对象
        part_size: 每个部分的尺寸，默认(64, 64)
        
    Returns:
        list: 分割后的图片列表
    """
    w, h = img.size
    pw, ph = part_size
    assert w % pw == h % ph == 0
    return [img.crop((i, j, i + pw, j + ph)).copy() for i in range(0, w, pw) for j in range(0, h, ph)]


def hist_similar(lh: list, rh: list) -> float:
    """
    计算两个直方图的相似度
    
    Args:
        lh: 左侧直方图
        rh: 右侧直方图
        
    Returns:
        float: 相似度值（0-1之间）
    """
    assert len(lh) == len(rh)
    return sum(1 - (0 if l == r else float(abs(l - r)) / max(l, r)) for l, r in zip(lh, rh)) / len(lh)


def calc_similar(li: Image.Image, ri: Image.Image) -> float:
    """
    计算两张图片的相似度
    
    Args:
        li: 左侧图片
        ri: 右侧图片
        
    Returns:
        float: 相似度值（0-1之间）
    """
    return sum(hist_similar(l.histogram(), r.histogram()) for l, r in zip(split_image(li), split_image(ri))) / 16.0


def calc_similar_by_path(lf: str, rf: str) -> float:
    """
    通过文件路径计算两张图片的相似度
    
    Args:
        lf: 左侧图片文件路径
        rf: 右侧图片文件路径
        
    Returns:
        float: 相似度值（0-1之间），失败返回0
    """
    try:
        li = make_regular_image(Image.open(lf))
        ri = make_regular_image(Image.open(rf))
        return calc_similar(li, ri)
    except Exception as e:
        logger.error(f"calc_similar_by_path Exception: {e}")
        return 0


def make_regular_image(img: Image.Image, size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """
    将图片调整为标准尺寸
    
    Args:
        img: 原始图片
        size: 目标尺寸，默认(256, 256)
        
    Returns:
        Image.Image: 调整后的图片
    """
    return img.resize(size).convert('RGB')


def dis_match(src_pic: str, dst_pic: str) -> Optional[str]:
    """
    判断两张图片是否匹配（相似度>=0.8）
    
    Args:
        src_pic: 源图片路径
        dst_pic: 目标图片路径
        
    Returns:
        Optional[str]: 如果匹配返回目标图片路径，否则返回None
    """
    similar = calc_similar_by_path(src_pic, dst_pic)
    if similar >= 0.8:
        return dst_pic
    else:
        return None


def judge_match_file(step_case_screenshot_path: str, screenshot_filename: str) -> Optional[str]:
    """
    判断当前截图是否与已有截图匹配（表示已访问过此页面）
    
    Args:
        step_case_screenshot_path: 截图目录路径
        screenshot_filename: 当前截图文件名
        
    Returns:
        Optional[str]: 匹配的截图文件路径，未匹配返回None
    """
    match_file = None
    try:
        file_names = os.listdir(step_case_screenshot_path)
        # 按文件名中的数字排序
        file_names.sort(key=lambda x: int(x[:-4]) if x[:-4].isdigit() else 0)
        for screenshot_file in file_names:
            if screenshot_file != screenshot_filename:
                match_file = dis_match(
                    os.path.join(step_case_screenshot_path, screenshot_filename),
                    os.path.join(step_case_screenshot_path, screenshot_file)
                )
                if match_file:
                    break
    except Exception as e:
        logger.error(f"judge_match_file Exception: {e}")
    return match_file


def judge_screen_color(image_file: str, screen_size: Optional[Tuple[int, int]] = None) -> str:
    """
    判断屏幕颜色（黑屏/白屏/正常）
    判断黑白屏
    优化后的算法：
    1. 使用平均值和标准差，更稳定可靠
    2. 采样多个区域（中心、左上、右上、左下、右下），提高准确性
    3. 考虑RGB三个通道的平均值
    4. 使用更合理的阈值判断
    
    Args:
        image_file: 图片文件路径
        screen_size: 屏幕尺寸，如果为None则使用图片尺寸
        
    Returns:
        str: 'black_screen'、'white_screen'或'normal_screen'
    """
    try:
        # 使用PIL读取图片
        img = Image.open(image_file)
        if img is None:
            return 'normal_screen'

        # 转换为RGB模式（如果是RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 转换为numpy数组以便进行像素值计算
        img_array = np.array(img)

        # 如果未提供屏幕尺寸，使用图片尺寸
        if screen_size is None:
            w, h = img.size
            screen_size = (w, h)

        w, h = screen_size
        
        # 定义采样区域大小（每个区域占屏幕的20%）
        region_size = (int(w * 0.2), int(h * 0.2))
        
        # 采样多个区域：中心、左上、右上、左下、右下
        regions = [
            # 中心区域
            (int(w * 0.4), int(h * 0.4), int(w * 0.6), int(h * 0.6)),
            # 左上
            (int(w * 0.1), int(h * 0.1), int(w * 0.1) + region_size[0], int(h * 0.1) + region_size[1]),
            # 右上
            (int(w * 0.9) - region_size[0], int(h * 0.1), int(w * 0.9), int(h * 0.1) + region_size[1]),
            # 左下
            (int(w * 0.1), int(h * 0.9) - region_size[1], int(w * 0.1) + region_size[0], int(h * 0.9)),
            # 右下
            (int(w * 0.9) - region_size[0], int(h * 0.9) - region_size[1], int(w * 0.9), int(h * 0.9)),
        ]
        
        # 收集所有采样区域的像素值
        all_pixels = []
        for x1, y1, x2, y2 in regions:
            # 确保坐标在有效范围内
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w))
            y2 = max(0, min(y2, h))
            
            if x2 > x1 and y2 > y1:
                region = img_array[y1:y2, x1:x2]
                # 将RGB三个通道合并为灰度值（使用加权平均）
                # 标准权重：R=0.299, G=0.587, B=0.114
                gray = np.dot(region[..., :3], [0.299, 0.587, 0.114])
                all_pixels.extend(gray.flatten())
        
        if not all_pixels:
            return 'normal_screen'
        
        # 转换为numpy数组进行计算
        pixels = np.array(all_pixels)
        
        # 计算统计值
        mean_value = np.mean(pixels)  # 平均值
        std_value = np.std(pixels)     # 标准差
        min_value = np.min(pixels)     # 最小值
        max_value = np.max(pixels)     # 最大值
        
        # 计算像素值分布：统计接近0（黑色）和接近255（白色）的像素比例
        black_pixels_ratio = np.sum(pixels < 30) / len(pixels)   # 像素值 < 30 的比例
        white_pixels_ratio = np.sum(pixels > 225) / len(pixels)   # 像素值 > 225 的比例
        
        # 计算像素值范围（最大值-最小值），用于判断是否有UI元素变化
        pixel_range = max_value - min_value
        
        # 计算像素值分布的离散程度：使用四分位距（IQR）作为辅助判断
        q25 = np.percentile(pixels, 25)
        q75 = np.percentile(pixels, 75)
        iqr = q75 - q25  # 四分位距
        
        # 判断逻辑：
        # 1. 黑屏：平均值低、标准差很小、像素值范围小、大部分像素接近黑色
        #    - 关键区别：黑屏几乎没有变化，标准差和范围都很小
        # 2. 白屏：平均值高、标准差很小、像素值范围小、大部分像素接近白色
        # 3. 黑夜模式：平均值低但标准差较大、像素值范围较大（有UI元素变化）
        # 4. 正常屏幕：其他情况
        
        # 黑屏判断（更严格的条件，避免误判黑夜模式）：
        # - 平均值 < 35（整体很黑）
        # - 标准差 < 15（几乎没有变化，这是关键：黑屏几乎没有UI元素）
        # - 像素值范围 < 40（最大值和最小值差距很小）
        # - 黑色像素比例 > 85%（绝大部分是黑色）
        # - IQR < 10（像素值分布集中，没有明显的变化）
        is_black_screen = (
            mean_value < 35 and 
            std_value < 15 and 
            pixel_range < 40 and
            black_pixels_ratio > 0.85 and
            iqr < 10
        )
        
        if is_black_screen:
            return 'black_screen'
        
        # 白屏判断（同样严格的条件）：
        # - 平均值 > 220（整体很白）
        # - 标准差 < 15（几乎没有变化）
        # - 像素值范围 < 40（最大值和最小值差距很小）
        # - 白色像素比例 > 85%（绝大部分是白色）
        # - IQR < 10（像素值分布集中）
        is_white_screen = (
            mean_value > 220 and 
            std_value < 15 and 
            pixel_range < 40 and
            white_pixels_ratio > 0.85 and
            iqr < 10
        )
        
        if is_white_screen:
            return 'white_screen'
        
        # 正常屏幕（包括黑夜模式）
        # 黑夜模式虽然整体偏黑，但：
        # - 标准差通常 > 15（有UI元素变化）
        # - 像素值范围通常 > 40（有亮度变化）
        # - IQR通常 > 10（像素值分布较分散）
        return 'normal_screen'
        
    except Exception as e:
        logger.error(f"judge_screen_color Exception: {e}")
        return 'normal_screen'


def get_current_package_dump_str(src_dump_tree_str: str, pkg_name: Optional[str] = None) -> Optional[
    ElementTree.Element]:
    """
    从UI层次结构XML字符串中提取指定包名的元素树
    
    Args:
        src_dump_tree_str: UI层次结构XML字符串
        pkg_name: 包名，如果为None则返回整个树
        
    Returns:
        Optional[ElementTree.Element]: 解析后的元素树，失败返回None
    """
    try:
        tree = ElementTree.fromstring(src_dump_tree_str)
        if pkg_name:
            # 移除不属于指定包名的元素
            remove_tree_list = []
            for elem in tree:
                if elem.attrib.get('package') != pkg_name:
                    remove_tree_list.append(elem)
            for elem in remove_tree_list:
                tree.remove(elem)
        return tree
    except Exception as e:
        logger.error(f'--get current package dump str-- failed!!!!! Exception={e}')
        return None


def paint_res_on_screenshot(pos: Tuple[float, float], shape: str, filename: str) -> bool:
    """
    在截图上标记点击位置
    
    Args:
        pos: 位置坐标，对于circle为(x, y)，对于line为(x1, y1, x2, y2)
        shape: 标记形状，'circle'或'line'
        filename: 截图文件路径
        
    Returns:
        bool: 标记是否成功
    """
    try:
        screenshot_filename = filename
        # 使用PIL读取截图
        img = Image.open(screenshot_filename)
        if img is None:
            logger.error(f"无法读取截图文件: {screenshot_filename}")
            return False

        # 转换为RGB模式（确保可以绘制）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 创建绘图对象
        draw = ImageDraw.Draw(img)

        if shape == 'circle':
            # 绘制圆形标记（红色实心圆）
            pos_tuple = (int(pos[0]), int(pos[1]))
            # 绘制实心圆：圆心、半径20、红色(255, 0, 0)
            draw.ellipse(
                [pos_tuple[0] - 20, pos_tuple[1] - 20, pos_tuple[0] + 20, pos_tuple[1] + 20],
                fill=(255, 0, 0),  # 红色
                outline=(255, 0, 0)
            )
            img.save(screenshot_filename, quality=95)
            return True

        elif shape == 'line':
            # 绘制线条和终点圆形标记
            f_pos = (int(pos[0]), int(pos[1]))
            t_pos = (int(pos[2]), int(pos[3]))
            # 绘制线条（红色，宽度3）
            draw.line([f_pos, t_pos], fill=(255, 0, 0), width=3)
            # 绘制终点圆形标记
            draw.ellipse(
                [t_pos[0] - 20, t_pos[1] - 20, t_pos[0] + 20, t_pos[1] + 20],
                fill=(255, 0, 0),  # 红色
                outline=(255, 0, 0)
            )
            img.save(screenshot_filename, quality=95)
            return True

        elif shape == 'text':
            # 文本标记暂未实现
            pass

        return False
    except Exception as e:
        logger.error(f'--paint res on screenshot-- failed!!!!! Exception={e}')
        return False
