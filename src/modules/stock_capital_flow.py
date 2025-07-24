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


def get_individual_fund_flow(code):
    """获取个股资金流向数据 - 使用确认可用的API接口"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    
    # 使用确认存在的同花顺资金流向接口
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    # 按优先级尝试API
    api_functions = [
        lambda: ak.stock_fund_flow_individual(symbol=pure_code, start_date=start_date, end_date=end_date),
        lambda: ak.stock_fund_flow_big_deal()  # 大单追踪数据作为备用
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            # 只取最近的数据，避免过量输出
            return result.head(20) if len(result) > 20 else result
    
    return None


def get_main_fund_flow_history(code, days=20):
    """获取主力资金流向历史数据"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    
    # 使用同花顺资金流向接口
    return safe_get_data(ak.stock_fund_flow_individual, symbol=pure_code, start_date=start_date, end_date=end_date)


def get_north_fund_flow():
    """获取北向资金流向数据"""
    api_functions = [
        lambda: ak.stock_hsgt_fund_flow_summary_em(),
        lambda: ak.stock_hsgt_fund_hist_em()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_north_fund_stock_holding(code):
    """获取北向资金对个股的持仓情况"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    
    api_functions = [
        lambda: ak.stock_hsgt_hold_detail_em(symbol=pure_code),
        lambda: ak.stock_hsgt_individual_detail_em(symbol=pure_code)
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_margin_trading_data(code):
    """获取融资融券数据"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    
    # 先尝试深交所数据
    api_functions = [
        lambda: ak.stock_margin_detail_szse(symbol=pure_code),
        lambda: ak.stock_margin_detail_sse(symbol=pure_code)
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_dragon_tiger_data():
    """获取最近龙虎榜数据"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    api_functions = [
        lambda: ak.stock_lhb_detail_daily_sina(trade_date=end_date),
        lambda: ak.stock_lhb_detail_em()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_stock_capital_flow_data(code, output_file=None):
    """获取股票资金流向数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的资金流向数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 资金流向数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 东方财富、新浪财经等公开数据接口\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取个股资金流向
        update_progress(1, 7, prefix='资金流向数据获取进度:', suffix='个股资金流向')
        fund_flow_data = get_individual_fund_flow(code)
        
        if fund_flow_data is not None and not fund_flow_data.empty:
            print("## 个股资金流向数据", file=f_out)
            print("### 最新资金流向", file=f_out)
            print(fund_flow_data.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 个股资金流向数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤2: 获取主力资金历史
        update_progress(2, 7, prefix='资金流向数据获取进度:', suffix='主力资金历史')
        main_flow_history = get_main_fund_flow_history(code)
        
        if main_flow_history is not None and not main_flow_history.empty:
            print("## 主力资金流向历史数据", file=f_out)
            print("### 最近20日主力资金流向", file=f_out)
            print(main_flow_history.head(10).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 主力资金流向历史数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤3: 获取北向资金整体流向
        update_progress(3, 7, prefix='资金流向数据获取进度:', suffix='北向资金流向')
        north_flow = get_north_fund_flow()
        
        if north_flow is not None and not north_flow.empty:
            print("## 北向资金整体流向数据", file=f_out)
            print(north_flow.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 北向资金整体流向数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤4: 获取北向资金个股持仓
        update_progress(4, 7, prefix='资金流向数据获取进度:', suffix='北向资金持仓')
        north_holding = get_north_fund_stock_holding(code)
        
        if north_holding is not None and not north_holding.empty:
            print("## 北向资金个股持仓数据", file=f_out)
            print(north_holding.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 北向资金个股持仓数据: 该股票未被北向资金持有或数据获取失败", file=f_out)
        
        # 显示进度 - 步骤5: 获取融资融券数据
        update_progress(5, 7, prefix='资金流向数据获取进度:', suffix='融资融券数据')
        margin_data = get_margin_trading_data(code)
        
        if margin_data is not None and not margin_data.empty:
            print("## 融资融券数据", file=f_out)
            print("### 最近融资融券情况", file=f_out)
            print(margin_data.head(10).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 融资融券数据: 获取失败或该股票不支持融资融券", file=f_out)
        
        # 显示进度 - 步骤6: 获取龙虎榜数据
        update_progress(6, 7, prefix='资金流向数据获取进度:', suffix='龙虎榜数据')
        lhb_data = get_dragon_tiger_data()
        
        if lhb_data is not None and not lhb_data.empty:
            pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
            stock_lhb = lhb_data[lhb_data['代码'] == pure_code] if '代码' in lhb_data.columns else pd.DataFrame()
            
            if not stock_lhb.empty:
                print("## 龙虎榜数据", file=f_out)
                print("### 最新龙虎榜上榜情况", file=f_out)
                print(stock_lhb.to_string(index=False), file=f_out)
                print("", file=f_out)
            else:
                print("## 龙虎榜数据: 该股票今日未上榜", file=f_out)
        else:
            print("## 龙虎榜数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤7: 完成
        update_progress(7, 7, prefix='资金流向数据获取进度:', suffix='数据获取完成')
        
        print(f"\n**数据说明:** 以上数据来源于公开的交易和资金流向信息。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"**API版本:** AKShare当前版本可能存在接口变化，部分数据获取失败属于正常情况。", file=f_out)
        
        time.sleep(0.5)
        print(f"资金流向数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取资金流向数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"资金流向数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_capital_flow.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_资金流向_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_capital_flow_data(stock_code, output_file)


if __name__ == "__main__":
    main()