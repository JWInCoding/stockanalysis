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


def get_stock_industry_info(code):
    """获取股票行业分类信息"""
    pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
    return safe_get_data(ak.stock_individual_info_em, symbol=pure_code)


def get_industry_list():
    """获取行业板块列表"""
    return safe_get_data(ak.stock_board_industry_name_em)


def get_industry_stocks(industry_name):
    """获取行业成分股列表"""
    return safe_get_data(ak.stock_board_industry_cons_em, symbol=industry_name)


def get_concept_list():
    """获取概念板块列表"""
    return safe_get_data(ak.stock_board_concept_name_em)


def get_concept_stocks(concept_name):
    """获取概念成分股列表"""
    return safe_get_data(ak.stock_board_concept_cons_em, symbol=concept_name)


def get_industry_fund_flow():
    """获取行业资金流向"""
    return safe_get_data(ak.stock_sector_fund_flow_rank, indicator="今日")


def get_concept_fund_flow():
    """获取概念板块资金流向"""
    return safe_get_data(ak.stock_board_concept_fund_flow_rank, indicator="今日")


def get_stock_sector_summary():
    """获取板块市场总体数据"""
    return safe_get_data(ak.stock_sector_summary)


def analyze_stock_industry(code, output_file=None):
    """获取股票行业板块数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的行业板块数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 行业板块数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 东方财富等公开数据接口\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取股票行业信息
        update_progress(1, 9, prefix='行业数据获取进度:', suffix='股票行业信息')
        stock_info = get_stock_industry_info(code)
        
        if stock_info is not None and not stock_info.empty:
            print("## 股票行业分类信息", file=f_out)
            print(stock_info.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 股票行业分类信息: 获取失败", file=f_out)
        
        # 显示进度 - 步骤2: 获取行业板块列表
        update_progress(2, 9, prefix='行业数据获取进度:', suffix='行业板块列表')
        industry_list = get_industry_list()
        
        if industry_list is not None and not industry_list.empty:
            print("## 市场行业板块列表", file=f_out)
            print("### 全市场行业分类（前20个）", file=f_out)
            print(industry_list.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 市场行业板块列表: 获取失败", file=f_out)
        
        # 显示进度 - 步骤3: 获取概念板块列表
        update_progress(3, 9, prefix='行业数据获取进度:', suffix='概念板块列表')
        concept_list = get_concept_list()
        
        if concept_list is not None and not concept_list.empty:
            print("## 市场概念板块列表", file=f_out)
            print("### 全市场概念分类（前20个）", file=f_out)
            print(concept_list.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 市场概念板块列表: 获取失败", file=f_out)
        
        # 显示进度 - 步骤4: 获取相关行业成分股
        update_progress(4, 9, prefix='行业数据获取进度:', suffix='行业成分股')
        industry_stocks = None
        if industry_list is not None and not industry_list.empty:
            # 尝试找到相关行业
            for _, row in industry_list.head(10).iterrows():
                industry_name = row.get('板块名称', '')
                if industry_name:
                    stocks = get_industry_stocks(industry_name)
                    if stocks is not None and not stocks.empty:
                        pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
                        if pure_code in stocks.get('代码', pd.Series()).values:
                            industry_stocks = stocks
                            print(f"## 所属行业成分股: {industry_name}", file=f_out)
                            print("### 同行业股票列表（前20只）", file=f_out)
                            print(stocks.head(20).to_string(index=False), file=f_out)
                            print("", file=f_out)
                            break
        
        if industry_stocks is None:
            print("## 所属行业成分股: 未找到相关行业或获取失败", file=f_out)
        
        # 显示进度 - 步骤5: 获取相关概念成分股
        update_progress(5, 9, prefix='行业数据获取进度:', suffix='概念成分股')
        related_concepts = []
        if concept_list is not None and not concept_list.empty:
            # 尝试找到相关概念（限制查询数量避免超时）
            for _, row in concept_list.head(20).iterrows():
                concept_name = row.get('板块名称', '')
                if concept_name:
                    stocks = get_concept_stocks(concept_name)
                    if stocks is not None and not stocks.empty:
                        pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
                        if pure_code in stocks.get('代码', pd.Series()).values:
                            related_concepts.append({
                                'concept_name': concept_name,
                                'stocks': stocks
                            })
                        
                        # 限制概念数量
                        if len(related_concepts) >= 5:
                            break
        
        if related_concepts:
            print("## 所属概念板块成分股", file=f_out)
            for i, concept_info in enumerate(related_concepts, 1):
                print(f"### 概念{i}: {concept_info['concept_name']}", file=f_out)
                print("#### 概念成分股列表（前15只）", file=f_out)
                print(concept_info['stocks'].head(15).to_string(index=False), file=f_out)
                print("", file=f_out)
        else:
            print("## 所属概念板块成分股: 未找到相关概念或获取失败", file=f_out)
        
        # 显示进度 - 步骤6: 获取行业资金流向
        update_progress(6, 9, prefix='行业数据获取进度:', suffix='行业资金流向')
        industry_fund_flow = get_industry_fund_flow()
        
        if industry_fund_flow is not None and not industry_fund_flow.empty:
            print("## 行业资金流向数据", file=f_out)
            print("### 今日行业资金流向排行（前20名）", file=f_out)
            print(industry_fund_flow.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 行业资金流向数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤7: 获取概念资金流向
        update_progress(7, 9, prefix='行业数据获取进度:', suffix='概念资金流向')
        concept_fund_flow = get_concept_fund_flow()
        
        if concept_fund_flow is not None and not concept_fund_flow.empty:
            print("## 概念板块资金流向数据", file=f_out)
            print("### 今日概念资金流向排行（前20名）", file=f_out)
            print(concept_fund_flow.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 概念板块资金流向数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤8: 获取板块市场总结
        update_progress(8, 9, prefix='行业数据获取进度:', suffix='板块市场总结')
        sector_summary = get_stock_sector_summary()
        
        if sector_summary is not None and not sector_summary.empty:
            print("## 板块市场总结数据", file=f_out)
            print("### 各板块市场表现总结", file=f_out)
            print(sector_summary.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 板块市场总结数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤9: 完成
        update_progress(9, 9, prefix='行业数据获取进度:', suffix='数据获取完成')
        
        print(f"\n**数据说明:** 以上数据来源于公开的行业分类和板块信息。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        
        time.sleep(0.5)
        print(f"行业板块数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取行业数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"行业数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_industry.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_行业数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    analyze_stock_industry(stock_code, output_file)


if __name__ == "__main__":
    main()