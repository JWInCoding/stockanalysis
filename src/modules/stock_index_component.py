#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import sys
import re
import time
from datetime import datetime, timedelta


def update_progress(progress, total, prefix='', suffix='', length=30):
    """显示进度条"""
    filled_length = int(length * progress // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {progress}/{total} {suffix}')
    sys.stdout.flush()
    if progress == total:
        print()


def safe_get_data(func, *args, **kwargs):
    """安全获取数据的包装函数"""
    try:
        time.sleep(0.5)  # 避免请求过于频繁
        return func(*args, **kwargs)
    except Exception as e:
        print(f"数据获取失败: {str(e)}")
        return None


def get_hs300_stocks():
    """获取沪深300成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="000300")


def get_sz50_stocks():
    """获取上证50成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="000016")


def get_zz500_stocks():
    """获取中证500成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="000905")


def get_cyb_stocks():
    """获取创业板指成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="399006")


def get_kc50_stocks():
    """获取科创50成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="000688")


def get_bj50_stocks():
    """获取北证50成分股"""
    return safe_get_data(ak.index_stock_cons, symbol="899050")


def get_index_daily_data(symbol):
    """获取指数日线数据"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    return safe_get_data(ak.stock_zh_index_daily_em, symbol=symbol, start_date=start_date, end_date=end_date)


def get_stock_index_component_data(code, output_file=None):
    """获取股票指数成分股数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的指数成分股数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 指数成分股数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 中证指数公司等公开数据接口\n", file=f_out)
        
        pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
        
        # 定义要检查的指数列表
        index_checks = [
            ("沪深300", get_hs300_stocks),
            ("上证50", get_sz50_stocks),
            ("中证500", get_zz500_stocks),
            ("创业板指", get_cyb_stocks),
            ("科创50", get_kc50_stocks),
            ("北证50", get_bj50_stocks)
        ]
        
        stock_in_indices = []
        
        # 显示进度 - 检查各指数成分股
        for i, (index_name, get_func) in enumerate(index_checks, 1):
            update_progress(i, len(index_checks) + 3, prefix='指数成分股获取进度:', suffix=f'检查{index_name}')
            
            stocks = get_func()
            if stocks is not None and not stocks.empty:
                print(f"## {index_name}成分股数据", file=f_out)
                print(f"### {index_name}全部成分股", file=f_out)
                print(stocks.to_string(index=False), file=f_out)
                print("", file=f_out)
                
                # 检查目标股票是否在该指数中
                if '品种代码' in stocks.columns:
                    if pure_code in stocks['品种代码'].values:
                        stock_in_indices.append(index_name)
                elif 'code' in stocks.columns:
                    if pure_code in stocks['code'].values:
                        stock_in_indices.append(index_name)
                elif '代码' in stocks.columns:
                    if pure_code in stocks['代码'].values:
                        stock_in_indices.append(index_name)
            else:
                print(f"## {index_name}成分股数据: 获取失败", file=f_out)
        
        # 显示进度 - 生成成分股归属总结
        update_progress(len(index_checks) + 1, len(index_checks) + 3, prefix='指数成分股获取进度:', suffix='成分股归属')
        
        print("## 目标股票指数成分股归属", file=f_out)
        if stock_in_indices:
            print(f"### 股票 {code} 属于以下指数成分股:", file=f_out)
            for index_name in stock_in_indices:
                print(f"- {index_name}", file=f_out)
        else:
            print(f"### 股票 {code} 不属于主要指数成分股", file=f_out)
        print("", file=f_out)
        
        # 显示进度 - 获取相关指数表现
        update_progress(len(index_checks) + 2, len(index_checks) + 3, prefix='指数成分股获取进度:', suffix='指数表现')
        
        if stock_in_indices:
            print("## 相关指数近期表现", file=f_out)
            index_symbols = {
                "沪深300": "sh000300",
                "上证50": "sh000016", 
                "中证500": "sz000905",
                "创业板指": "sz399006",
                "科创50": "sh000688",
                "北证50": "bj899050"
            }
            
            for index_name in stock_in_indices:
                if index_name in index_symbols:
                    symbol = index_symbols[index_name]
                    index_data = get_index_daily_data(symbol)
                    if index_data is not None and not index_data.empty:
                        print(f"### {index_name}近期走势", file=f_out)
                        print(index_data.tail(10).to_string(index=False), file=f_out)
                        print("", file=f_out)
        
        # 显示进度 - 完成
        update_progress(len(index_checks) + 3, len(index_checks) + 3, prefix='指数成分股获取进度:', suffix='数据获取完成')
        
        print(f"\n**数据说明:** 以上数据来源于中证指数公司等权威指数发布机构。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        
        time.sleep(0.5)
        print(f"指数成分股数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取指数成分股数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"指数成分股数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_index_component.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_指数成分股_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_index_component_data(stock_code, output_file)


if __name__ == "__main__":
    main()