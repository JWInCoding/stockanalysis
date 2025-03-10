#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import numpy as np
import sys
import re
import time
from datetime import datetime, timedelta, date


def format_volume(volume):
    """将成交量格式化为易读的形式（单位：万手）"""
    return round(volume / 10000, 2)


def calculate_macd(data):
    """计算MACD指标"""
    exp1 = data['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = data['收盘'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def calculate_rsi(data, periods=14):
    """计算RSI指标"""
    delta = data['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(data, window=20, num_std=2):
    """计算布林带指标"""
    sma = data['收盘'].rolling(window=window).mean()
    std = data['收盘'].rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return sma, upper_band, lower_band


def predict_ma(recent_data, ma_period, predict_days):
    """预测未来几天的均线值"""
    prices = recent_data['收盘'].values
    x = np.arange(len(prices))
    y = prices
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    predictions = []
    last_prices = prices[-ma_period:].tolist()
    for i in range(predict_days):
        next_price = p(len(prices) + i)
        if len(last_prices) >= ma_period:
            last_prices.pop(0)
        last_prices.append(next_price)
        ma_value = sum(last_prices[-ma_period:]) / ma_period
        predictions.append(ma_value)
    return predictions


def get_next_trading_dates(last_date, num_days):
    """获取未来的交易日期"""
    if isinstance(last_date, date):
        last_date = last_date.strftime("%Y-%m-%d")
    elif isinstance(last_date, pd.Timestamp):
        last_date = last_date.strftime("%Y-%m-%d")
    current_date = datetime.strptime(last_date, "%Y-%m-%d")
    future_dates = []
    while len(future_dates) < num_days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # 只考虑工作日
            future_dates.append(current_date.strftime("%Y-%m-%d"))
    return future_dates


def update_progress(progress, total, prefix='', suffix='', length=30):
    """显示进度条"""
    filled_length = int(length * progress // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {progress}/{total} {suffix}')
    sys.stdout.flush()
    if progress == total:
        print()


def analyze_stock_data(code, output_file=None):
    """分析股票或指数数据，结果可输出到文件"""
    # 准备文件输出
    if output_file:
        f_out = open(output_file, 'w', encoding='utf-8')
    else:
        f_out = sys.stdout
    
    try:
        # 控制台显示进度信息
        print(f"正在获取 {code} 的日线数据...", file=sys.stdout)
        
        # 文件中写入标题
        print(f"# {code} 日线数据分析报告", file=f_out)
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", file=f_out)

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

        # 显示进度 - 步骤1
        update_progress(1, 5, prefix='日线数据分析进度:', suffix='获取数据中')
        
        # 判断是否为指数代码
        if re.match(r'^(sh|sz)', code.lower()):
            # 提取市场代码和数字部分
            market = code[:2].lower()
            number = code[2:]
            # 使用正确的指数数据获取接口
            stock_data = ak.stock_zh_index_daily_em(
                symbol=f"{market}{number}"
            )
            # 统一指数数据的列名
            if not stock_data.empty:
                column_mapping = {
                    'date': '日期',
                    'open': '开盘',
                    'close': '收盘',
                    'high': '最高',
                    'low': '最低',
                    'volume': '成交量',
                    'amount': '成交额'
                }
                stock_data = stock_data.rename(columns=column_mapping)
                # 指数数据添加空的换手率列
                stock_data['换手率'] = None
        else:
            # 获取股票历史数据
            stock_data = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

        if stock_data is None or stock_data.empty:
            print(f"未能获取到 {code} 的数据，请检查代码是否正确", file=f_out)
            return

        # 写入基本数据信息到文件
        print(f"## 基本数据信息", file=f_out)
        print(f"- 数据周期: 日线", file=f_out)
        print(f"- 起始日期: {start_date}", file=f_out)
        print(f"- 结束日期: {end_date}", file=f_out)
        print(f"- 总数据条数: {len(stock_data)}\n", file=f_out)

        # 显示进度 - 步骤2
        update_progress(2, 5, prefix='日线数据分析进度:', suffix='处理数据中')
        
        # 确保日期列格式统一
        if isinstance(stock_data['日期'].iloc[0], str):
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

        # 确保数值列为浮点数类型
        numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
        for col in numeric_columns:
            if col in stock_data.columns:
                stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')

        # 显示进度 - 步骤3
        update_progress(3, 5, prefix='日线数据分析进度:', suffix='计算技术指标')
        
        # 计算所有移动平均线
        stock_data['MA3'] = stock_data['收盘'].rolling(window=3).mean()
        stock_data['MA5'] = stock_data['收盘'].rolling(window=5).mean()
        stock_data['MA8'] = stock_data['收盘'].rolling(window=8).mean()
        stock_data['MA13'] = stock_data['收盘'].rolling(window=13).mean()
        stock_data['MA21'] = stock_data['收盘'].rolling(window=21).mean()

        # 计算MACD指标
        macd, signal, hist = calculate_macd(stock_data)
        stock_data['MACD'] = macd
        stock_data['Signal'] = signal
        stock_data['MACD_Hist'] = hist

        # 计算RSI指标
        stock_data['RSI'] = calculate_rsi(stock_data)

        # 计算布林带
        bb_sma, upper_band, lower_band = calculate_bollinger_bands(stock_data)
        stock_data['BB_Middle'] = bb_sma
        stock_data['BB_Upper'] = upper_band
        stock_data['BB_Lower'] = lower_band

        # 计算成交量的移动平均
        stock_data['Volume_MA5'] = stock_data['成交量'].rolling(window=5).mean()

        # 显示进度 - 步骤4
        update_progress(4, 5, prefix='日线数据分析进度:', suffix='分析数据中')
        
        # 获取最近21个交易日的数据
        recent_data = stock_data.tail(21)
        
        # 将结果写入文件
        print(f"## 最近21个交易日数据", file=f_out)
        print("| 日期 | 收盘价 | 成交量(万手) | 量比 | 换手率 | MA3 | MA5 | MA8 | MA13 | MA21 |", file=f_out)
        print("|------|--------|-------------|------|--------|-----|-----|-----|------|------|", file=f_out)
        
        for i, row in recent_data.iterrows():
            volume_ratio = row['成交量'] / row['Volume_MA5'] if not pd.isna(row['Volume_MA5']) else 0
            volume_ratio = round(volume_ratio, 2)
            turnover = f"{row['换手率']:.2f}%" if pd.notna(row['换手率']) else "N/A"
            print(f"| {row['日期'].strftime('%Y-%m-%d')} | {row['收盘']:.2f} | {format_volume(row['成交量']):.2f} | {volume_ratio:.2f} | {turnover} | {row['MA3']:.2f} | {row['MA5']:.2f} | {row['MA8']:.2f} | {row['MA13']:.2f} | {row['MA21']:.2f} |", file=f_out)
        
        print("\n## 均线排列（从高到低）", file=f_out)
        latest = recent_data.iloc[-1]
        ma_dict = {
            'MA3': latest['MA3'],
            'MA5': latest['MA5'],
            'MA8': latest['MA8'],
            'MA13': latest['MA13'],
            'MA21': latest['MA21']
        }
        sorted_ma = dict(sorted(ma_dict.items(), key=lambda x: x[1], reverse=True))
        for ma, value in sorted_ma.items():
            print(f"- {ma}: {value:.2f}", file=f_out)
        
        print("\n## 成交量分析", file=f_out)
        avg_volume = recent_data['成交量'].mean()
        latest_volume = recent_data['成交量'].iloc[-1]
        volume_trend = "放量" if latest_volume > avg_volume else "缩量"
        print(f"- 21日平均成交量：{format_volume(avg_volume):.2f}万手", file=f_out)
        print(f"- 最新成交量：{format_volume(latest_volume):.2f}万手", file=f_out)
        print(f"- 成交量特征：{volume_trend}", file=f_out)
        
        # 判断多空头排列
        trend_text = ""
        if latest['MA3'] > latest['MA5'] > latest['MA8'] > latest['MA13'] > latest['MA21']:
            trend_text = "当前呈现标准多头排列"
        elif latest['MA3'] < latest['MA5'] < latest['MA8'] < latest['MA13'] < latest['MA21']:
            trend_text = "当前呈现标准空头排列"
        else:
            trend_text = "当前均线交叉混乱，建议观察趋势变化"
        print(f"- 均线排列特征: {trend_text}", file=f_out)
        
        # 技术指标分析
        print("\n## 技术指标分析", file=f_out)
        
        # MACD分析
        print("\n### MACD指标分析", file=f_out)
        macd_trend = "金叉" if latest['MACD'] > latest['Signal'] else "死叉"
        macd_strength = abs(latest['MACD'] - latest['Signal'])
        print(f"- MACD当前形态：{macd_trend}", file=f_out)
        print(f"- MACD强度：{macd_strength:.3f}", file=f_out)
        print(f"- MACD值：{latest['MACD']:.3f}", file=f_out)
        print(f"- 信号线值：{latest['Signal']:.3f}", file=f_out)
        print(f"- MACD柱状值：{latest['MACD_Hist']:.3f}", file=f_out)
        
        # RSI分析
        print("\n### RSI指标分析", file=f_out)
        rsi_value = latest['RSI']
        if rsi_value > 70:
            rsi_status = "超买区间"
        elif rsi_value < 30:
            rsi_status = "超卖区间"
        else:
            rsi_status = "中性区间"
        print(f"- RSI值：{rsi_value:.1f} ({rsi_status})", file=f_out)
        
        # 布林带分析
        print("\n### 布林带分析", file=f_out)
        current_price = latest['收盘']
        bb_position = ((current_price - latest['BB_Lower']) / 
                      (latest['BB_Upper'] - latest['BB_Lower']) * 100)
        print(f"- 当前价格：{current_price:.2f}", file=f_out)
        print(f"- 布林带上轨：{latest['BB_Upper']:.2f}", file=f_out)
        print(f"- 布林带中轨：{latest['BB_Middle']:.2f}", file=f_out)
        print(f"- 布林带下轨：{latest['BB_Lower']:.2f}", file=f_out)
        print(f"- 布林带位置：{bb_position:.1f}%", file=f_out)
        
        if current_price > latest['BB_Upper']:
            print("- 当前价格位于布林带上轨以上，可能存在回调风险", file=f_out)
        elif current_price < latest['BB_Lower']:
            print("- 当前价格位于布林带下轨以下，可能存在反弹机会", file=f_out)
        else:
            print("- 当前价格在布林带通道内运行", file=f_out)

        # 显示进度 - 步骤5
        update_progress(5, 5, prefix='日线数据分析进度:', suffix='完成预测与总结')
        
        # 换手率分析
        if not pd.isna(latest['换手率']):
            print("\n### 换手率分析", file=f_out)
            turnover = latest['换手率']
            if turnover > 20:
                print(f"- 当前换手率：{turnover:.2f}% - 换手率极高，表明交投十分活跃", file=f_out)
            elif turnover > 10:
                print(f"- 当前换手率：{turnover:.2f}% - 换手率较高，市场活跃度强", file=f_out)
            elif turnover > 5:
                print(f"- 当前换手率：{turnover:.2f}% - 换手率适中，成交较为活跃", file=f_out)
            else:
                print(f"- 当前换手率：{turnover:.2f}% - 换手率偏低，交投较为清淡", file=f_out)
        
        # 预测未来5个交易日的MA13和MA21
        ma13_predictions = predict_ma(recent_data, 13, 5)
        ma21_predictions = predict_ma(recent_data, 21, 5)
        last_date = recent_data.iloc[-1]['日期']
        future_dates = get_next_trading_dates(last_date, 5)
        
        print("\n## 未来5个交易日均线预测", file=f_out)
        print("| 日期 | MA13预测 | MA21预测 | 差值 |", file=f_out)
        print("|------|---------|---------|------|", file=f_out)
        for i in range(5):
            diff = ma13_predictions[i] - ma21_predictions[i]
            print(f"| {future_dates[i]} | {ma13_predictions[i]:.2f} | {ma21_predictions[i]:.2f} | {diff:.2f} |", file=f_out)
        
        print("\n### 预测趋势分析", file=f_out)
        ma13_trend = ma13_predictions[-1] - ma13_predictions[0]
        ma21_trend = ma21_predictions[-1] - ma21_predictions[0]
        print(f"- MA13五日预测变化：{ma13_trend:.2f}", file=f_out)
        print(f"- MA21五日预测变化：{ma21_trend:.2f}", file=f_out)
        
        # 综合分析和建议
        print("\n## 综合分析和建议", file=f_out)
        
        # 趋势强度分析
        trend_signals = []
        if latest['MA5'] > latest['MA13']:
            trend_signals.append("短期均线在长期均线之上")
        if latest['RSI'] > 50:
            trend_signals.append("RSI处于上升趋势区间")
        if latest['MACD'] > latest['Signal']:
            trend_signals.append("MACD呈现金叉形态")
        if current_price > latest['BB_Middle']:
            trend_signals.append("价格在布林带中轨之上")
        
        print("\n### 趋势信号", file=f_out)
        if trend_signals:
            print("看多信号：", file=f_out)
            for signal in trend_signals:
                print(f"- {signal}", file=f_out)
        else:
            print("- 当前无明显看多信号", file=f_out)
        
        # 风险提示
        print("\n### 风险提示", file=f_out)
        risks = []
        if latest['RSI'] > 70:
            risks.append("RSI处于超买区间，注意回调风险")
        if current_price > latest['BB_Upper']:
            risks.append("价格突破布林带上轨，注意回调风险")
        if latest_volume > avg_volume * 2:
            risks.append("成交量显著放大，注意价格变动风险")
        
        # 换手率风险分析
        if not pd.isna(latest['换手率']) and latest['换手率'] > 15:
            risks.append(f"换手率达到{latest['换手率']:.2f}%，交易过于活跃，注意风险")
        
        if risks:
            for risk in risks:
                print(f"- {risk}", file=f_out)
        else:
            print("- 当前无明显风险信号", file=f_out)
        
        # 操作建议
        print("\n### 操作建议", file=f_out)
        if len(trend_signals) >= 3 and not risks:
            print("- 可考虑逢低买入", file=f_out)
        elif len(risks) >= 2:
            print("- 建议保持谨慎，注意控制仓位", file=f_out)
        else:
            print("- 建议观望，等待更明确的信号", file=f_out)

        time.sleep(0.5)  # 给用户一点时间看清进度条完成
        print(f"日线数据分析完成，结果已保存至: {output_file}", file=sys.stdout)
    
    except Exception as e:
        print(f"获取数据时出错：{str(e)}", file=f_out)
        print(f"请检查网络连接或确认股票代码是否正确", file=f_out)
        print(f"日线数据分析失败: {str(e)}", file=sys.stdout)
    
    finally:
        # 关闭输出文件
        if output_file and f_out != sys.stdout:
            f_out.close()


def main():
    """处理命令行参数"""
    if len(sys.argv) < 2:
        print("使用方法: python stock_data.py <股票代码> [输出文件名]")
        sys.exit(1)
    
    # 从命令行获取股票代码
    stock_code = sys.argv[1]
    
    # 如果提供了第二个参数作为输出文件名
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # 生成默认输出文件名
        output_file = f"{stock_code}_日线数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    analyze_stock_data(stock_code, output_file)


if __name__ == "__main__":
    main()