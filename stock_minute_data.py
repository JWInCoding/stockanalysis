#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import numpy as np
import os
import sys
import re
import time
from datetime import datetime, timedelta


def format_volume(volume):
    """将成交量格式化为易读的形式（单位：万手）"""
    return round(volume / 10000, 2)


def update_progress(progress, total, prefix='', suffix='', length=30):
    """显示进度条"""
    filled_length = int(length * progress // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {progress}/{total} {suffix}')
    sys.stdout.flush()
    if progress == total:
        print()


def get_minute_kline_data(code, period, days):
    """获取指定周期的分钟级K线数据
    
    Args:
        code: 股票代码
        period: 周期，如 5, 15, 60 分钟
        days: 获取的天数
        
    Returns:
        DataFrame: 分钟级K线数据
    """
    try:
        # 判断是否为指数
        is_index = False
        if re.match(r'^(sh|sz)', code.lower()):
            market = code[:2].lower()
            number = code[2:]
            if re.match(r'^(000|399)', number):
                is_index = True
        
        # 去除市场前缀
        symbol = re.sub(r'^(sh|sz|bj)', '', code)
        
        # 根据是否为指数选择不同的API
        if is_index:
            # 注意：这里使用的是指数分钟数据接口
            kline_data = ak.index_zh_a_hist_min_em(
                symbol=symbol,
                period=str(period),
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # 统一列名
            column_mapping = {
                '时间': '日期',
                '开盘': '开盘',
                '收盘': '收盘',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
            }
            kline_data = kline_data.rename(columns=column_mapping)
            
        else:
            # 股票分钟数据
            kline_data = ak.stock_zh_a_hist_min_em(
                symbol=symbol,
                period=str(period),
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # 统一列名
            column_mapping = {
                '时间': '日期',
                '开盘': '开盘',
                '收盘': '收盘',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
                '换手率': '换手率'
            }
            kline_data = kline_data.rename(columns=column_mapping)
        
        return kline_data
        
    except Exception as e:
        print(f"获取{period}分钟K线数据时出错: {e}")
        return None


def get_stock_minute_data(code, output_file=None):
    """获取股票或指数的分钟级数据并保存到文件"""
    # 如果提供了输出文件，准备写入
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的分钟级K线数据...", file=sys.stdout)
        
        # 写入文件标题
        print(f"# {code} 分钟级K线数据分析报告", file=f_out)
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取15分钟数据
        update_progress(1, 6, prefix='分钟级数据获取进度:', suffix='获取15分钟K线')
        kline_15min = get_minute_kline_data(code, 15, 5)  # 15分钟K线，最近5个交易日
        
        # 显示进度 - 步骤2: 获取5分钟数据
        update_progress(2, 6, prefix='分钟级数据获取进度:', suffix='获取5分钟K线')
        kline_5min = get_minute_kline_data(code, 5, 3)    # 5分钟K线，最近3个交易日
        
        # 显示进度 - 步骤3: 获取60分钟数据
        update_progress(3, 6, prefix='分钟级数据获取进度:', suffix='获取60分钟K线')
        kline_60min = get_minute_kline_data(code, 60, 21) # 60分钟K线，最近21个交易日
        
        # 检查是否成功获取数据
        if kline_15min is None or kline_5min is None or kline_60min is None:
            print(f"未能获取到 {code} 的完整分钟级数据", file=f_out)
            return
        
        # 显示进度 - 步骤4: 处理数据
        update_progress(4, 6, prefix='分钟级数据获取进度:', suffix='处理数据中')
        
        # 确保日期列格式统一
        for df in [kline_15min, kline_5min, kline_60min]:
            if isinstance(df['日期'].iloc[0], str):
                df['日期'] = pd.to_datetime(df['日期'])
                
            # 确保数值列为浮点数类型
            numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 显示进度 - 步骤5: 分析15分钟和5分钟数据
        update_progress(5, 6, prefix='分钟级数据获取进度:', suffix='分析短周期数据')
        
        # 写入15分钟K线数据
        print(f"## 15分钟K线数据 (最近5个交易日)", file=f_out)
        print(f"共获取到 {len(kline_15min)} 条15分钟K线数据\n", file=f_out)
        
        # 写入基本统计信息
        print("### 基本统计信息", file=f_out)
        print(f"- 最高价范围: {kline_15min['最高'].min():.2f} - {kline_15min['最高'].max():.2f}", file=f_out)
        print(f"- 最低价范围: {kline_15min['最低'].min():.2f} - {kline_15min['最低'].max():.2f}", file=f_out)
        print(f"- 成交量范围: {format_volume(kline_15min['成交量'].min()):.2f}万 - {format_volume(kline_15min['成交量'].max()):.2f}万", file=f_out)
        print(f"- 平均成交量: {format_volume(kline_15min['成交量'].mean()):.2f}万\n", file=f_out)
        
        # 打印最近的K线数据
        recent_count = min(20, len(kline_15min))
        recent_data = kline_15min.tail(recent_count)
        
        print(f"### 最近{recent_count}条15分钟K线数据", file=f_out)
        print("| 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量(万) | 成交额(万) |", file=f_out)
        print("|------|------|------|------|------|------------|------------|", file=f_out)
        
        for i, row in recent_data.iterrows():
            print(f"| {row['日期'].strftime('%Y-%m-%d %H:%M')} | {row['开盘']:.2f} | {row['收盘']:.2f} | {row['最高']:.2f} | {row['最低']:.2f} | {format_volume(row['成交量']):.2f} | {row['成交额']/10000:.2f} |", file=f_out)
        
        # 写入5分钟K线数据
        print(f"\n## 5分钟K线数据 (最近3个交易日)", file=f_out)
        print(f"共获取到 {len(kline_5min)} 条5分钟K线数据\n", file=f_out)
        
        # 写入基本统计信息
        print("### 基本统计信息", file=f_out)
        print(f"- 最高价范围: {kline_5min['最高'].min():.2f} - {kline_5min['最高'].max():.2f}", file=f_out)
        print(f"- 最低价范围: {kline_5min['最低'].min():.2f} - {kline_5min['最低'].max():.2f}", file=f_out)
        print(f"- 成交量范围: {format_volume(kline_5min['成交量'].min()):.2f}万 - {format_volume(kline_5min['成交量'].max()):.2f}万", file=f_out)
        print(f"- 平均成交量: {format_volume(kline_5min['成交量'].mean()):.2f}万\n", file=f_out)
        
        # 打印最近的K线数据
        recent_count = min(20, len(kline_5min))
        recent_data = kline_5min.tail(recent_count)
        
        print(f"### 最近{recent_count}条5分钟K线数据", file=f_out)
        print("| 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量(万) | 成交额(万) |", file=f_out)
        print("|------|------|------|------|------|------------|------------|", file=f_out)
        
        for i, row in recent_data.iterrows():
            print(f"| {row['日期'].strftime('%Y-%m-%d %H:%M')} | {row['开盘']:.2f} | {row['收盘']:.2f} | {row['最高']:.2f} | {row['最低']:.2f} | {format_volume(row['成交量']):.2f} | {row['成交额']/10000:.2f} |", file=f_out)
        
        # 显示进度 - 步骤6: 分析60分钟数据
        update_progress(6, 6, prefix='分钟级数据获取进度:', suffix='分析长周期数据')
        
        # 写入60分钟K线数据
        print(f"\n## 60分钟K线数据 (最近21个交易日)", file=f_out)
        print(f"共获取到 {len(kline_60min)} 条60分钟K线数据\n", file=f_out)
        
        # 写入基本统计信息
        print("### 基本统计信息", file=f_out)
        print(f"- 最高价范围: {kline_60min['最高'].min():.2f} - {kline_60min['最高'].max():.2f}", file=f_out)
        print(f"- 最低价范围: {kline_60min['最低'].min():.2f} - {kline_60min['最低'].max():.2f}", file=f_out)
        print(f"- 成交量范围: {format_volume(kline_60min['成交量'].min()):.2f}万 - {format_volume(kline_60min['成交量'].max()):.2f}万", file=f_out)
        print(f"- 平均成交量: {format_volume(kline_60min['成交量'].mean()):.2f}万\n", file=f_out)
        
        # 打印最近的K线数据
        recent_count = min(20, len(kline_60min))
        recent_data = kline_60min.tail(recent_count)
        
        print(f"### 最近{recent_count}条60分钟K线数据", file=f_out)
        print("| 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量(万) | 成交额(万) |", file=f_out)
        print("|------|------|------|------|------|------------|------------|", file=f_out)
        
        for i, row in recent_data.iterrows():
            print(f"| {row['日期'].strftime('%Y-%m-%d %H:%M')} | {row['开盘']:.2f} | {row['收盘']:.2f} | {row['最高']:.2f} | {row['最低']:.2f} | {format_volume(row['成交量']):.2f} | {row['成交额']/10000:.2f} |", file=f_out)
        
        # 综合数据分析
        print("\n## 综合分析", file=f_out)
        print("### 价格区间对比", file=f_out)
        print("| 周期 | 最高价 | 最低价 | 振幅 | 平均成交量(万手) |", file=f_out)
        print("|------|--------|--------|------|-----------------|", file=f_out)
        print(f"| 5分钟 | {kline_5min['最高'].max():.2f} | {kline_5min['最低'].min():.2f} | {(kline_5min['最高'].max() - kline_5min['最低'].min()):.2f} | {format_volume(kline_5min['成交量'].mean()):.2f} |", file=f_out)
        print(f"| 15分钟 | {kline_15min['最高'].max():.2f} | {kline_15min['最低'].min():.2f} | {(kline_15min['最高'].max() - kline_15min['最低'].min()):.2f} | {format_volume(kline_15min['成交量'].mean()):.2f} |", file=f_out)
        print(f"| 60分钟 | {kline_60min['最高'].max():.2f} | {kline_60min['最低'].min():.2f} | {(kline_60min['最高'].max() - kline_60min['最低'].min()):.2f} | {format_volume(kline_60min['成交量'].mean()):.2f} |", file=f_out)
        
        # 最新价格趋势
        print("\n### 最新交易趋势", file=f_out)
        latest_5min = kline_5min.iloc[-1]
        latest_15min = kline_15min.iloc[-1]
        latest_60min = kline_60min.iloc[-1]
        
        print(f"- 最新5分钟K线: 开盘价 {latest_5min['开盘']:.2f}, 收盘价 {latest_5min['收盘']:.2f}, 涨跌幅 {((latest_5min['收盘'] - latest_5min['开盘']) / latest_5min['开盘'] * 100):.2f}%", file=f_out)
        print(f"- 最新15分钟K线: 开盘价 {latest_15min['开盘']:.2f}, 收盘价 {latest_15min['收盘']:.2f}, 涨跌幅 {((latest_15min['收盘'] - latest_15min['开盘']) / latest_15min['开盘'] * 100):.2f}%", file=f_out)
        print(f"- 最新60分钟K线: 开盘价 {latest_60min['开盘']:.2f}, 收盘价 {latest_60min['收盘']:.2f}, 涨跌幅 {((latest_60min['收盘'] - latest_60min['开盘']) / latest_60min['开盘'] * 100):.2f}%", file=f_out)
        
        time.sleep(0.5)  # 给用户一点时间看清进度条完成
        print(f"分钟级K线数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"分钟级数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_minute_data.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_分钟级数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_minute_data(stock_code, output_file)


if __name__ == "__main__":
    main()