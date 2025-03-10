#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import akshare as ak
import re
from datetime import datetime, timedelta, date


def is_valid_stock_code(code):
    """验证股票代码和指数代码格式是否正确"""
    # 股票代码格式：sh000001 或 000001
    stock_pattern = r'^(?:sh|sz|bj)?[0-9]{6}$'
    # 指数代码格式支持两种：1A0001 或 000001/399001
    index_pattern = r'^(000[0-9]{3}|399[0-9]{3}|[0-9][A-Za-z][0-9]{4})$'
    return bool(re.match(stock_pattern, code.lower()) or re.match(index_pattern, code.upper()))


def normalize_stock_code(code):
    """标准化股票和指数代码格式"""
    code = code.strip()
    # 处理指数代码映射关系
    index_map = {
        '1A0001': 'sh000001',  # 上证指数
        '000001': 'sh000001',  # 上证指数
        '399001': 'sz399001',  # 深证成指
        '399006': 'sz399006',  # 创业板指
        '000300': 'sh000300',  # 沪深300
        '000016': 'sh000016',  # 上证50
        '399905': 'sz399905',  # 中证500
    }
    
    # 如果是老式指数代码格式（如1A0001）或直接输入指数代码，转换为带市场前缀的格式
    if re.match(r'^[0-9][A-Za-z][0-9]{4}$', code.upper()) or \
       re.match(r'^(000[0-9]{3}|399[0-9]{3})$', code):
        return index_map.get(code.upper(), index_map.get(code, code))
    
    # 如果已经带有市场前缀，则直接返回
    if re.match(r'^(sh|sz|bj)', code.lower()):
        return code.lower()
    
    # 其他情况（普通股票代码），去除可能的前缀
    return code


def get_stock_name(code):
    """获取股票或指数名称"""
    try:
        # 指数名称映射
        index_names = {
            'sh000001': '上证指数',
            '000001': '上证指数',
            '1A0001': '上证指数',
            'sz399001': '深证成指',
            '399001': '深证成指',
            'sz399006': '创业板指',
            '399006': '创业板指',
            'sh000300': '沪深300',
            '000300': '沪深300',
            'sh000016': '上证50',
            '000016': '上证50',
            'sz399905': '中证500',
            '399905': '中证500'
        }
        
        # 标准化代码
        normalized_code = normalize_stock_code(code)
        
        # 检查是否为指数代码
        # 1. 检查完整的带前缀指数代码
        if normalized_code in index_names:
            return index_names[normalized_code]
        # 2. 检查不带前缀的指数代码
        if re.match(r'^(000[0-9]{3}|399[0-9]{3})$', code):
            return index_names.get(code, None)
        # 3. 检查老式指数代码（如1A0001）
        if re.match(r'^[0-9][A-Za-z][0-9]{4}$', code.upper()):
            return index_names.get(code.upper(), None)
        
        # 如果不是指数，则获取股票名称
        # 去除可能的市场前缀
        pure_code = re.sub(r'^(sh|sz|bj)', '', normalized_code)
        stock_info = ak.stock_zh_a_spot_em()
        stock_row = stock_info[stock_info['代码'] == pure_code]
        if not stock_row.empty:
            return stock_row.iloc[0]['名称']
        
    except Exception as e:
        print(f"获取名称时出错: {e}")
        return None


def run_stock_analysis(stock_code):
    """
    顺序执行股票数据分析脚本
    
    Args:
        stock_code: 股票代码
    """
    # 标准化股票代码
    normalized_code = normalize_stock_code(stock_code)
    stock_name = get_stock_name(stock_code)
    
    # 生成当前时间戳，用于文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 设置输出文件名
    daily_output_file = f"{normalized_code}_日线数据_{timestamp}.txt"
    minute_output_file = f"{normalized_code}_分钟级数据_{timestamp}.txt"
    
    print(f"===== 开始分析股票 {normalized_code} ({stock_name}) =====")
    
    # 执行日线数据分析脚本
    print("\n1. 正在获取股票日线数据...")
    try:
        result = subprocess.run(
            ['python', 'stock_data.py', normalized_code, daily_output_file], 
            check=True,
            text=True
        )
        print(f"   日线数据已保存至: {daily_output_file}")
    except subprocess.CalledProcessError as e:
        print(f"   日线数据分析失败: {e}")
        return
    
    # 执行分钟级数据分析脚本
    print("\n2. 正在获取股票分钟级数据...")
    try:
        result = subprocess.run(
            ['python', 'stock_minute_data.py', normalized_code, minute_output_file],
            check=True,
            text=True
        )
        print(f"   分钟级数据已保存至: {minute_output_file}")
    except subprocess.CalledProcessError as e:
        print(f"   分钟级数据分析失败: {e}")
    
    print(f"\n===== 股票 {normalized_code} ({stock_name}) 分析完成 =====")


def main():
    # 显示欢迎信息
    print("=" * 60)
    print("股票数据分析工具")
    print("本工具将依次执行日线数据和分钟级数据分析")
    print("=" * 60)
    
    # 获取用户输入
    if len(sys.argv) > 1:
        # 从命令行参数获取股票代码
        stock_code = sys.argv[1]
    else:
        # 交互式输入股票代码
        print("\n请输入股票代码或指数代码，例如:")
        print("- 直接输入代码：000001")
        print("- 带市场前缀：sh000001、sz000001")
        print("- 指数代码：000001（上证指数）、399001（深证成指）、1A0001（上证指数）")
        stock_code = input("\n请输入股票代码: ").strip()
    
    # 验证股票代码
    if not stock_code:
        print("未输入有效的股票代码，程序退出")
        return
        
    if not is_valid_stock_code(stock_code):
        print("代码格式错误，请输入正确的股票代码或指数代码")
        return
    
    # 执行分析
    run_stock_analysis(stock_code)


if __name__ == "__main__":
    main()