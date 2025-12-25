#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Pillow图像绘制模块

该模块提供了在图片上绘制文本的功能，基于Pillow库实现。
主要功能包括：
- 支持在图片上绘制多个文本
- 支持自定义文本位置、字体、颜色等参数
- 自动处理参数验证和类型转换
- 保存绘制后的图片
"""
import os

from PIL import Image, ImageDraw


def draw_texts(
        image_file_path: str = "",
        image_file_save_kwargs: dict = dict(),
        texts: list[dict] = []
):
    """
    在图片上绘制多个文本，并保存结果图片。

    Args:
        image_file_path (str, optional): 原始图片文件路径。
            注意：此参数不能为空，必须指向一个有效的图片文件。
        image_file_save_kwargs (dict, optional): 图片保存参数，将传递给Image.save()方法。
            至少应包含'fp'键指定保存路径。默认值为None，会被转换为空字典。
        texts (list[dict], optional): 要绘制的文本列表，每个元素是一个字典，包含
            ImageDraw.text()方法所需的参数，如位置'xy'、文本内容'text'、字体'font'、
            颜色'fill'等。默认值为空列表。

    Returns:
        str: 保存的图片文件路径，如果未指定则为空字符串。
    """
    # 确保保存参数为字典类型，防止None值导致的类型错误
    image_file_save_kwargs = image_file_save_kwargs if isinstance(image_file_save_kwargs, dict) else dict()

    # 打开原始图片，若路径无效会引发IOError异常
    image_file = Image.open(image_file_path)

    # 创建绘图对象，用于在图片上绘制文本
    image_draw = ImageDraw.Draw(image_file)

    # 遍历文本列表，为每个文本执行绘制操作
    for text in texts:
        # 确保文本参数为字典类型，提高代码健壮性
        text = text if isinstance(text, dict) else dict()

        # 使用字典解包方式传递所有文本参数，绘制文本
        # 支持的参数包括：xy(位置), text(内容), font(字体), fill(颜色), anchor(锚点), etc.
        image_draw.text(**text)

    # 获取保存路径，若未指定则为空字符串
    save_path = image_file_save_kwargs.get("fp", "")
    if isinstance(save_path, str) and len(save_path) > 0:
        # 确保保存目录存在，若不存在则创建
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 保存修改后的图片，若save_path为空会引发异常
    image_file.save(**image_file_save_kwargs)

    # 返回保存的图片文件路径
    return save_path
