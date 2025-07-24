#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime


def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建输出目录: {directory}")
    return directory


def generate_output_filename(code, stock_name, data_type, extension='.txt'):
    """生成标准化的输出文件名"""
    today = datetime.now().strftime('%Y%m%d')
    timestamp = datetime.now().strftime('%H%M%S')
    name_part = f"_{stock_name}" if stock_name else ""
    
    return f"{code}{name_part}_{data_type}_{today}_{timestamp}{extension}"


def get_project_root():
    """获取项目根目录路径"""
    current_file = os.path.abspath(__file__)
    # 从 src/utils/file_utils.py 回到项目根目录
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def get_output_dir(subdir=None):
    """获取输出目录路径"""
    project_root = get_project_root()
    today = datetime.now().strftime('%Y%m%d')
    
    if subdir:
        output_path = os.path.join(project_root, "outputs", subdir, today)
    else:
        output_path = os.path.join(project_root, "outputs", "stock_results", today)
    
    return ensure_dir(output_path)
