#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


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


def validate_date_format(date_str):
    """验证日期格式是否正确 (YYYYMMDD)"""
    date_pattern = r'^[0-9]{8}$'
    return bool(re.match(date_pattern, date_str))


def is_trading_day(date_str):
    """简单判断是否为工作日（不包含节假日判断）"""
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        # 0=Monday, 6=Sunday
        return date_obj.weekday() < 5  # Monday-Friday
    except ValueError:
        return False