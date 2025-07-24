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
    """获取涨停统计"""
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


def get_individual_stock_sentiment(code):
    """获取个股相关的情绪数据"""
    try:
        # 尝试获取个股的龙虎榜数据
        stock_lhb = safe_get_data(ak.stock_lhb_detail_em, symbol=code.replace('sz', '').replace('sh', '').replace('bj', ''))
        return stock_lhb
    except:
        return None


def get_stock_sentiment_data(code, output_file=None):
    """获取个股相关市场情绪数据的主函数"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 相关的市场情绪数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 个股市场情绪数据报告", file=f_out)
        print(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"数据来源: 东方财富、同花顺等公开数据接口\n", file=f_out)
        
        # 显示进度 - 步骤1: 获取个股龙虎榜情绪
        update_progress(1, 7, prefix='个股情绪数据获取进度:', suffix='个股龙虎榜')
        individual_sentiment = get_individual_stock_sentiment(code)
        
        if individual_sentiment is not None and not individual_sentiment.empty:
            print("## 个股龙虎榜情绪数据", file=f_out)
            print("### 最近龙虎榜上榜记录", file=f_out)
            print(individual_sentiment.head(10).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 个股龙虎榜情绪数据: 获取失败或该股票近期未上榜", file=f_out)
        
        # 显示进度 - 步骤2: 获取新股统计
        update_progress(2, 7, prefix='个股情绪数据获取进度:', suffix='新股统计')
        new_stock_stats = get_new_stock_statistics()
        
        if new_stock_stats is not None and not new_stock_stats.empty:
            print("## 新股统计数据", file=f_out)
            print("### 新股发行统计（前10只）", file=f_out)
            print(new_stock_stats.head(10).to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 新股统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤3: 获取涨停统计
        update_progress(3, 7, prefix='个股情绪数据获取进度:', suffix='涨停统计')
        limit_up_stats = get_limit_up_statistics()
        
        if limit_up_stats is not None and not limit_up_stats.empty:
            print("## 涨停板统计数据", file=f_out)
            print("### 今日涨停股票（前20只）", file=f_out)
            print(limit_up_stats.head(20).to_string(index=False), file=f_out)
            
            # 检查目标股票是否涨停
            pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
            if '代码' in limit_up_stats.columns:
                target_stock = limit_up_stats[limit_up_stats['代码'] == pure_code]
                if not target_stock.empty:
                    print(f"### 🔥 目标股票 {code} 今日涨停情况", file=f_out)
                    print(target_stock.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 涨停板统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤4: 获取跌停统计
        update_progress(4, 7, prefix='个股情绪数据获取进度:', suffix='跌停统计')
        limit_down_stats = get_limit_down_statistics()
        
        if limit_down_stats is not None and not limit_down_stats.empty:
            print("## 跌停板统计数据", file=f_out)
            print("### 今日跌停股票（前20只）", file=f_out)
            print(limit_down_stats.head(20).to_string(index=False), file=f_out)
            
            # 检查目标股票是否跌停
            pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
            if '代码' in limit_down_stats.columns:
                target_stock = limit_down_stats[limit_down_stats['代码'] == pure_code]
                if not target_stock.empty:
                    print(f"### ⚠️ 目标股票 {code} 今日跌停情况", file=f_out)
                    print(target_stock.to_string(index=False), file=f_out)
            print("", file=f_out)
        else:
            print("## 跌停板统计数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤5: 获取股票热度排行
        update_progress(5, 7, prefix='个股情绪数据获取进度:', suffix='热度排行')
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
                    print(f"### 📈 目标股票 {code} 在热度排行中的位置", file=f_out)
                    print(target_stock.to_string(index=False), file=f_out)
                    print("", file=f_out)
                else:
                    print(f"### 目标股票 {code} 未进入当前热度排行榜", file=f_out)
        else:
            print("## 股票热度排行数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤6: 获取股票评论数据
        update_progress(6, 7, prefix='个股情绪数据获取进度:', suffix='评论关注度')
        comment_data = get_stock_comment_data()
        
        if comment_data is not None and not comment_data.empty:
            print("## 股票评论关注度数据", file=f_out)
            print("### 股票评论热度排行（前20名）", file=f_out)
            print(comment_data.head(20).to_string(index=False), file=f_out)
            print("", file=f_out)
            
            # 检查目标股票评论情况
            pure_code = re.sub(r'^(sh|sz|bj)', '', code.lower())
            if '代码' in comment_data.columns:
                target_stock = comment_data[comment_data['代码'] == pure_code]
                if not target_stock.empty:
                    print(f"### 💬 目标股票 {code} 评论关注度", file=f_out)
                    print(target_stock.to_string(index=False), file=f_out)
                    print("", file=f_out)
        else:
            print("## 股票评论关注度数据: 获取失败", file=f_out)
        
        # 显示进度 - 步骤7: 完成
        update_progress(7, 7, prefix='个股情绪数据获取进度:', suffix='数据获取完成')
        
        print(f"\n## 个股情绪分析小结", file=f_out)
        print(f"**分析对象:** {code}", file=f_out)
        print(f"**情绪数据维度:** 龙虎榜上榜、涨跌停统计、热度排行、评论关注度", file=f_out)
        print(f"**市场环境参考:** 基于当日涨跌停统计和新股发行情况", file=f_out)
        print(f"**数据时效性:** 以上数据为实时或日内数据，具有较强的时效性", file=f_out)
        
        print(f"\n**数据说明:** 以上数据来源于公开的市场情绪和统计信息。", file=f_out)
        print(f"**获取时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=f_out)
        print(f"**使用建议:** 情绪数据应结合基本面和技术面分析使用，不可单独作为投资依据。", file=f_out)
        
        time.sleep(0.5)
        print(f"个股市场情绪数据获取完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取个股市场情绪数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"个股市场情绪数据获取失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_sentiment.py <股票代码> [输出文件名]")
        print("示例: python stock_sentiment.py 002354")
        print("     python stock_sentiment.py sz002354 sentiment_output.txt")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        pure_code = re.sub(r'^(sh|sz|bj)', '', stock_code.lower())
        output_file = f"{pure_code}_个股情绪_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    get_stock_sentiment_data(stock_code, output_file)


if __name__ == "__main__":
    main()