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


def get_stock_basic_info(code):
    """获取股票基本信息"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    return safe_get_data(ak.stock_individual_info_em, symbol=pure_code)


def get_financial_abstract(code):
    """获取财务摘要数据"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    # 尝试多个财务摘要接口
    api_functions = [
        lambda: ak.stock_financial_abstract_ths(symbol=pure_code),
        lambda: ak.stock_yjbb_em(symbol=pure_code),  # 业绩报告
        lambda: ak.stock_yjkb_em(symbol=pure_code)   # 业绩快报
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    return None


def get_profit_sheet(code):
    """获取利润表数据 - 使用正确的API参数"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    # 财务报表接口需要日期参数，不是股票代码
    latest_quarter = "20241231"  # 使用最新年报日期
    
    try:
        # 获取所有公司的利润表数据，然后筛选目标公司
        all_data = safe_get_data(ak.stock_lrb_em, date=latest_quarter)
        if all_data is not None and not all_data.empty:
            # 筛选目标股票
            target_data = all_data[all_data['股票代码'] == pure_code]
            return target_data if not target_data.empty else None
    except Exception:
        pass
    
    # 如果失败，尝试其他季度
    for quarter in ["20240930", "20240630", "20240331"]:
        try:
            all_data = safe_get_data(ak.stock_lrb_em, date=quarter)
            if all_data is not None and not all_data.empty:
                target_data = all_data[all_data['股票代码'] == pure_code]
                if not target_data.empty:
                    return target_data
        except Exception:
            continue
    
    return None


def get_balance_sheet(code):
    """获取资产负债表数据 - 使用正确的API参数"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    # 财务报表接口需要日期参数，不是股票代码
    latest_quarter = "20241231"  # 使用最新年报日期
    
    try:
        # 获取所有公司的资产负债表数据，然后筛选目标公司
        all_data = safe_get_data(ak.stock_zcfz_em, date=latest_quarter)
        if all_data is not None and not all_data.empty:
            # 筛选目标股票
            target_data = all_data[all_data['股票代码'] == pure_code]
            return target_data if not target_data.empty else None
    except Exception:
        pass
    
    # 如果失败，尝试其他季度
    for quarter in ["20240930", "20240630", "20240331"]:
        try:
            all_data = safe_get_data(ak.stock_zcfz_em, date=quarter)
            if all_data is not None and not all_data.empty:
                target_data = all_data[all_data['股票代码'] == pure_code]
                if not target_data.empty:
                    return target_data
        except Exception:
            continue
    
    return None


def get_cash_flow_sheet(code):
    """获取现金流量表数据 - 使用正确的API参数"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    # 财务报表接口需要日期参数，不是股票代码
    latest_quarter = "20241231"  # 使用最新年报日期
    
    try:
        # 获取所有公司的现金流量表数据，然后筛选目标公司
        all_data = safe_get_data(ak.stock_xjll_em, date=latest_quarter)
        if all_data is not None and not all_data.empty:
            # 筛选目标股票
            target_data = all_data[all_data['股票代码'] == pure_code]
            return target_data if not target_data.empty else None
    except Exception:
        pass
    
    # 如果失败，尝试其他季度
    for quarter in ["20240930", "20240630", "20240331"]:
        try:
            all_data = safe_get_data(ak.stock_xjll_em, date=quarter)
            if all_data is not None and not all_data.empty:
                target_data = all_data[all_data['股票代码'] == pure_code]
                if not target_data.empty:
                    return target_data
        except Exception:
            continue
    
    return None





def get_dividend_data(code):
    """获取分红配股数据 - 使用正确的API名称"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    
    # 直接尝试分红配股接口
    try:
        result = safe_get_data(ak.stock_fhps_em, symbol=pure_code)
        if result is not None and not result.empty:
            return result
    except Exception:
        pass
    
    # 如果失败，说明可能没有分红记录
    return None


def get_stock_fundamental_data(code, output_file=None):
    """获取股票基本面数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的基本面数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 基本面数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 东方财富、同花顺等公开数据接口\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取基本信息
        update_progress(1, 8, prefix='基本面数据获取进度:', suffix='基本信息')
        basic_info = get_stock_basic_info(code)
        
        if basic_info is not None and not basic_info.empty:
            print("## 股票基本信息", file=f_out)
            print(basic_info.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 股票基本信息: 获取失败", file=f_out)
        
        # 显示进度 - 步骤2: 获取财务摘要
        update_progress(2, 8, prefix='基本面数据获取进度:', suffix='财务摘要')
        financial_abstract = get_financial_abstract(code)
        
        if financial_abstract is not None and not financial_abstract.empty:
            print("## 财务摘要数据", file=f_out)
            print("### 最近财务摘要", file=f_out)
            print(financial_abstract.head(4).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 财务摘要数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤3: 获取利润表
        update_progress(3, 8, prefix='基本面数据获取进度:', suffix='利润表')
        profit_sheet = get_profit_sheet(code)
        
        if profit_sheet is not None and not profit_sheet.empty:
            print("## 利润表数据", file=f_out)
            print("### 最近4个报告期利润表", file=f_out)
            print(profit_sheet.head(4).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 利润表数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤4: 获取资产负债表
        update_progress(4, 8, prefix='基本面数据获取进度:', suffix='资产负债表')
        balance_sheet = get_balance_sheet(code)
        
        if balance_sheet is not None and not balance_sheet.empty:
            print("## 资产负债表数据", file=f_out)
            print("### 最近4个报告期资产负债表", file=f_out)
            print(balance_sheet.head(4).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 资产负债表数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤5: 获取现金流量表
        update_progress(5, 8, prefix='基本面数据获取进度:', suffix='现金流量表')
        cash_flow_sheet = get_cash_flow_sheet(code)
        
        if cash_flow_sheet is not None and not cash_flow_sheet.empty:
            print("## 现金流量表数据", file=f_out)
            print("### 最近4个报告期现金流量表", file=f_out)
            print(cash_flow_sheet.head(4).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 现金流量表数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤6: 获取分红配股
        update_progress(6, 7, prefix='基本面数据获取进度:', suffix='分红配股')
        dividend_data = get_dividend_data(code)
        
        if dividend_data is not None and not dividend_data.empty:
            print("## 分红配股数据", file=f_out)
            print("### 历史分红配股记录", file=f_out)
            print(dividend_data.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 分红配股数据: 获取失败或无分红记录", file=f_out)
        
        # 显示进度 - 步骤7: 完成
        update_progress(7, 7, prefix='基本面数据获取进度:', suffix='数据获取完成')
        
        print(f"\n**数据说明:** 以上数据来源于上市公司财务报表和公开披露信息。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        
        time.sleep(0.5)
        print(f"基本面数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取基本面数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"基本面数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_fundamental.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_基本面数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_fundamental_data(stock_code, output_file)


if __name__ == "__main__":
    main()