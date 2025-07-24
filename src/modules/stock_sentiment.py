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


def get_market_sentiment_index():
    """获取市场情绪指数 - 尝试多个API接口"""
    api_functions = [
        lambda: ak.stock_market_sentiment_lg(),
        lambda: ak.index_fear_greed_lg(),
        lambda: ak.stock_comment_em()  # 备用评论情绪数据
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_margin_trading_summary():
    """获取融资融券市场总体数据"""
    api_functions = [
        lambda: ak.stock_margin_summary_szse(),
        lambda: ak.stock_margin_summary_sse(),
        lambda: ak.stock_margin_underlying_info_szse()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_new_stock_statistics():
    """获取新股统计数据"""
    api_functions = [
        lambda: ak.stock_new_statistics(),
        lambda: ak.stock_ipo_info(),
        lambda: ak.new_stock_em()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_limit_up_statistics():
    """获取涨跌停统计"""
    today = datetime.now().strftime("%Y%m%d")
    api_functions = [
        lambda: ak.stock_zt_pool_em(date=today),
        lambda: ak.stock_zt_pool_dtgc_em(date=today),
        lambda: ak.stock_zt_pool_strong_em(date=today)
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_limit_down_statistics():
    """获取跌停统计"""
    today = datetime.now().strftime("%Y%m%d")
    api_functions = [
        lambda: ak.stock_dt_pool_em(date=today),
        lambda: ak.stock_zt_pool_em(date=today)  # 备用接口
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_hot_rank_data():
    """获取股票热度排行"""
    api_functions = [
        lambda: ak.stock_hot_rank_em(),
        lambda: ak.stock_hot_rank_wc(),
        lambda: ak.stock_comment_em()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_stock_comment_data():
    """获取股票评论关注度"""
    api_functions = [
        lambda: ak.stock_comment_em(),
        lambda: ak.stock_hot_rank_em(),
        lambda: ak.baidu_search_index()  # 百度搜索指数作为备用
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_fear_greed_index():
    """获取恐慌贪婪指数"""
    api_functions = [
        lambda: ak.stock_fear_greed_index_lg(),
        lambda: ak.index_fear_greed_lg(),
        lambda: ak.stock_market_sentiment_lg()
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_market_turnover():
    """获取市场成交统计"""
    api_functions = [
        lambda: ak.stock_market_capitalization(),
        lambda: ak.stock_market_activity_legu(),
        lambda: ak.stock_zh_a_spot_em().describe()  # 备用统计数据
    ]
    
    for func in api_functions:
        result = safe_get_data(func)
        if result is not None and not result.empty:
            return result
    
    return None


def get_stock_sentiment_data(code, output_file=None):
    """获取市场情绪数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 相关的市场情绪数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 市场情绪数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 龙虎榜网、东方财富等公开数据接口\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取市场情绪指数
        update_progress(1, 10, prefix='市场情绪数据获取进度:', suffix='市场情绪指数')
        sentiment_index = get_market_sentiment_index()
        
        if sentiment_index is not None and not sentiment_index.empty:
            print("## 市场情绪指数", file=f_out)
            print("### 情绪指数历史数据", file=f_out)
            print(sentiment_index.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 市场情绪指数: 获取失败", file=f_out)
        
        # 显示进度 - 步骤2: 获取融资融券总体数据
        update_progress(2, 10, prefix='市场情绪数据获取进度:', suffix='融资融券总体')
        margin_summary = get_margin_trading_summary()
        
        if margin_summary is not None and not margin_summary.empty:
            print("## 融资融券市场总体数据", file=f_out)
            print("### 融资融券余额统计", file=f_out)
            print(margin_summary.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 融资融券市场总体数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤3: 获取新股统计
        update_progress(3, 10, prefix='市场情绪数据获取进度:', suffix='新股统计')
        new_stock_stats = get_new_stock_statistics()
        
        if new_stock_stats is not None and not new_stock_stats.empty:
            print("## 新股统计数据", file=f_out)
            print("### 新股发行统计", file=f_out)
            print(new_stock_stats.head(10).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 新股统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤4: 获取涨停统计
        update_progress(4, 10, prefix='市场情绪数据获取进度:', suffix='涨停统计')
        limit_up_stats = get_limit_up_statistics()
        
        if limit_up_stats is not None and not limit_up_stats.empty:
            print("## 涨停板统计数据", file=f_out)
            print("### 今日涨停股票（前20只）", file=f_out)
            print(limit_up_stats.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 涨停板统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤5: 获取跌停统计
        update_progress(5, 10, prefix='市场情绪数据获取进度:', suffix='跌停统计')
        limit_down_stats = get_limit_down_statistics()
        
        if limit_down_stats is not None and not limit_down_stats.empty:
            print("## 跌停板统计数据", file=f_out)
            print("### 今日跌停股票（前20只）", file=f_out)
            print(limit_down_stats.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 跌停板统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤6: 获取股票热度排行
        update_progress(6, 10, prefix='市场情绪数据获取进度:', suffix='热度排行')
        hot_rank = get_hot_rank_data()
        
        if hot_rank is not None and not hot_rank.empty:
            print("## 股票热度排行数据", file=f_out)
            print("### 股票关注度排行（前20名）", file=f_out)
            print(hot_rank.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
            
            # 检查目标股票是否在热门榜单中
            pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
            if '代码' in hot_rank.columns:
                target_stock = hot_rank[hot_rank['代码'] == pure_code]
                if not target_stock.empty:
                    print(f"### 目标股票 {code} 在热度排行中的位置", file=f_out)
                    print(target_stock.to_string(index=False), file=f_out)
                    print("", file=f_out)
        else:
            print("## 股票热度排行数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤7: 获取股票评论数据
        update_progress(7, 10, prefix='市场情绪数据获取进度:', suffix='评论关注度')
        comment_data = get_stock_comment_data()
        
        if comment_data is not None and not comment_data.empty:
            print("## 股票评论关注度数据", file=f_out)
            print("### 股票评论热度排行（前20名）", file=f_out)
            print(comment_data.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 股票评论关注度数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤8: 获取恐慌贪婪指数
        update_progress(8, 10, prefix='市场情绪数据获取进度:', suffix='恐慌贪婪指数')
        fear_greed = get_fear_greed_index()
        
        if fear_greed is not None and not fear_greed.empty:
            print("## 恐慌贪婪指数", file=f_out)
            print("### 市场恐慌贪婪指数历史", file=f_out)
            print(fear_greed.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 恐慌贪婪指数: 获取失败", file=f_out)
        
        # 显示进度 - 步骤9: 获取市场成交统计
        update_progress(9, 10, prefix='市场情绪数据获取进度:', suffix='市场成交统计')
        market_turnover = get_market_turnover()
        
        if market_turnover is not None and not market_turnover.empty:
            print("## 市场成交统计数据", file=f_out)
            print("### 市场总体成交情况", file=f_out)
            print(market_turnover.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 市场成交统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤10: 完成
        update_progress(10, 10, prefix='市场情绪数据获取进度:', suffix='数据获取完成')
        
        print(f"\n**数据说明:** 以上数据来源于公开的市场情绪和统计信息。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"**API说明:** AKShare接口经常更新，部分API可能暂时不可用，这是正常现象。", file=f_out)
        
        time.sleep(0.5)
        print(f"市场情绪数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取市场情绪数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"市场情绪数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_sentiment.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_市场情绪_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_sentiment_data(stock_code, output_file)


if __name__ == "__main__":
    main()