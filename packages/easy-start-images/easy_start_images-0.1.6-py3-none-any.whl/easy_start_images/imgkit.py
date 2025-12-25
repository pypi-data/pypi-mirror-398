#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
imgkit 封装模块
用于将 HTML 转换为图像的工具函数集合
基于 imgkit 库，提供更简洁的 API 和错误处理
"""

import os  # 导入 os 模块，用于文件路径操作和目录创建

import imgkit  # 导入 imgkit 库，用于 HTML 转图像功能


def from_string(**kwargs):
    """
    将 HTML 字符串转换为图像
    
    @see https://pypi.org/project/imgkit/ - imgkit 官方文档
    
    Args:
        **kwargs: 传递给 imgkit.from_string() 的参数，包括：
            - string: HTML 字符串内容（必需）
            - output_path: 输出图像文件路径（可选）
            - css: CSS 样式字符串或文件路径（可选）
            - options: 配置选项字典，如格式、质量等（可选）
            
    Returns:
        str or None: 成功时返回输出图像路径，失败时返回 None
    """
    # 路径处理：如果指定了输出路径，确保目录存在
    output_path = kwargs.get("output_path", None)
    if isinstance(output_path, str) and len(output_path) > 0:
        # 使用 os.makedirs 创建目录，exist_ok=True 确保已存在的目录不会引发错误
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 执行转换：调用 imgkit.from_string() 将 HTML 字符串转换为图像
    # imgkit.from_string() 成功时返回 True，失败时返回 False
    if imgkit.from_string(**kwargs):
        # 转换成功：返回输出路径
        return kwargs.get("output_path", None)

    # 转换失败：返回 None
    return None


def from_url(**kwargs):
    """
    将网页 URL 转换为图像
    
    @see https://pypi.org/project/imgkit/ - imgkit 官方文档
    
    Args:
        **kwargs: 传递给 imgkit.from_url() 的参数，包括：
            - url: 网页 URL 地址（必需）
            - output_path: 输出图像文件路径（可选）
            - css: CSS 样式字符串或文件路径（可选）
            - options: 配置选项字典，如格式、质量等（可选）
            
    Returns:
        str or None: 成功时返回输出图像路径，失败时返回 None
            
    """

    # 路径处理：如果指定了输出路径，确保目录存在
    output_path = kwargs.get("output_path", None)
    if isinstance(output_path, str) and len(output_path) > 0:
        # 使用 os.makedirs 创建目录，exist_ok=True 确保已存在的目录不会引发错误
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 执行转换：调用 imgkit.from_url() 将网页 URL 转换为图像
    # imgkit.from_url() 成功时返回 True，失败时返回 False
    if imgkit.from_url(**kwargs):
        # 转换成功：返回输出路径
        return kwargs.get("output_path", None)

    # 转换失败：返回 None
    return None


def from_file(**kwargs):
    """
    将 HTML 文件转换为图像
    
    @see https://pypi.org/project/imgkit/ - imgkit 官方文档
    
    Args:
        **kwargs: 传递给 imgkit.from_file() 的参数，包括：
            - file: HTML 文件路径（必需）
            - output_path: 输出图像文件路径（可选）
            - css: CSS 样式字符串或文件路径（可选）
            - options: 配置选项字典，如格式、质量等（可选）
            
    Returns:
        str or None: 成功时返回输出图像路径，失败时返回 None
            
    """
    # 路径处理：如果指定了输出路径，确保目录存在
    output_path = kwargs.get("output_path", None)
    if isinstance(output_path, str) and len(output_path) > 0:
        # 使用 os.makedirs 创建目录，exist_ok=True 确保已存在的目录不会引发错误
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 执行转换：调用 imgkit.from_file() 将 HTML 文件转换为图像
    # imgkit.from_file() 成功时返回 True，失败时返回 False
    if imgkit.from_file(**kwargs):
        # 转换成功：返回输出路径
        return kwargs.get("output_path", None)

    # 转换失败：返回 None
    return None
