import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
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
        if current_date.weekday() < 5:
            future_dates.append(current_date.strftime("%Y-%m-%d"))
    
    return future_dates

def analyze_stock_data(code):
    """分析股票或指数数据"""
    try:
        pure_code = normalize_stock_code(code)
        name = get_stock_name(code)
        print(f"正在使用代码 {pure_code} 获取数据...")

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

        # 判断是否为指数代码
        if re.match(r'^(sh|sz)', pure_code.lower()):
            # 提取市场代码和数字部分
            market = pure_code[:2].lower()
            number = pure_code[2:]
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
                symbol=pure_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

        if stock_data is None or stock_data.empty:
            print(f"未能获取到 {code} 的数据，请检查代码是否正确")
            return

        # 打印列名，用于调试
        print("获取到的数据列名:", stock_data.columns.tolist())

        # 确保必要的列都存在
        required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
        if not all(col in stock_data.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in stock_data.columns]
            print(f"获取的数据格式不正确，缺少以下列：{missing_columns}")
            return

        # 确保日期列格式统一
        if isinstance(stock_data['日期'].iloc[0], str):
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

        # 确保数值列为浮点数类型
        numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
        for col in numeric_columns:
            if col in stock_data.columns:
                stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')

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

        # 获取最近21个交易日的数据
        recent_data = stock_data.tail(21)

        print(f"\n{pure_code} ({name}) 最近21个交易日数据：")
        print("日期\t\t收盘价\t成交量(万手)\t量比\t换手率\tMA3\tMA5\tMA8\tMA13\tMA21")
        print("-" * 120)
        
        for i, row in recent_data.iterrows():
            volume_ratio = row['成交量'] / row['Volume_MA5'] if not pd.isna(row['Volume_MA5']) else 0
            volume_ratio = round(volume_ratio, 2)
            turnover = f"{row['换手率']:.2f}%" if pd.notna(row['换手率']) else "N/A"
            
            print(f"{row['日期']}\t{row['收盘']:.2f}\t{format_volume(row['成交量'])}\t\t{volume_ratio:.2f}\t{turnover}\t"
                  f"{row['MA3']:.2f}\t{row['MA5']:.2f}\t{row['MA8']:.2f}\t{row['MA13']:.2f}\t{row['MA21']:.2f}")
        
        # 打印最新均线的排列情况
        latest = recent_data.iloc[-1]
        print("\n最新均线排列（从高到低）：")
        ma_dict = {
            'MA3': latest['MA3'],
            'MA5': latest['MA5'],
            'MA8': latest['MA8'],
            'MA13': latest['MA13'],
            'MA21': latest['MA21']
        }
        sorted_ma = dict(sorted(ma_dict.items(), key=lambda x: x[1], reverse=True))
        for ma, value in sorted_ma.items():
            print(f"{ma}: {value:.2f}")
        
        # 成交量分析
        avg_volume = recent_data['成交量'].mean()
        latest_volume = recent_data['成交量'].iloc[-1]
        volume_trend = "放量" if latest_volume > avg_volume else "缩量"
        print(f"\n成交量分析：")
        print(f"21日平均成交量：{format_volume(avg_volume):.2f}万手")
        print(f"最新成交量：{format_volume(latest_volume):.2f}万手")
        print(f"成交量特征：{volume_trend}")
        
        # 判断多空头排列
        if latest['MA3'] > latest['MA5'] > latest['MA8'] > latest['MA13'] > latest['MA21']:
            print("\n当前呈现标准多头排列")
        elif latest['MA3'] < latest['MA5'] < latest['MA8'] < latest['MA13'] < latest['MA21']:
            print("\n当前呈现标准空头排列")
        else:
            print("\n当前均线交叉混乱，建议观察趋势变化")
        
        # 技术指标分析
        print("\n=== 技术指标分析 ===")
        
        # MACD分析
        print("\nMACD指标分析：")
        macd_trend = "金叉" if latest['MACD'] > latest['Signal'] else "死叉"
        macd_strength = abs(latest['MACD'] - latest['Signal'])
        print(f"MACD当前形态：{macd_trend}")
        print(f"MACD强度：{macd_strength:.3f}")
        print(f"MACD值：{latest['MACD']:.3f}")
        print(f"信号线值：{latest['Signal']:.3f}")
        print(f"MACD柱状值：{latest['MACD_Hist']:.3f}")
        
        # RSI分析
        print("\nRSI指标分析：")
        rsi_value = latest['RSI']
        if rsi_value > 70:
            rsi_status = "超买区间"
        elif rsi_value < 30:
            rsi_status = "超卖区间"
        else:
            rsi_status = "中性区间"
        print(f"RSI值：{rsi_value:.1f} ({rsi_status})")
        
        # 布林带分析
        print("\n布林带分析：")
        current_price = latest['收盘']
        bb_position = ((current_price - latest['BB_Lower']) / 
                      (latest['BB_Upper'] - latest['BB_Lower']) * 100)
        print(f"当前价格：{current_price:.2f}")
        print(f"布林带上轨：{latest['BB_Upper']:.2f}")
        print(f"布林带中轨：{latest['BB_Middle']:.2f}")
        print(f"布林带下轨：{latest['BB_Lower']:.2f}")
        print(f"布林带位置：{bb_position:.1f}%")
        
        if current_price > latest['BB_Upper']:
            print("当前价格位于布林带上轨以上，可能存在回调风险")
        elif current_price < latest['BB_Lower']:
            print("当前价格位于布林带下轨以下，可能存在反弹机会")
        else:
            print("当前价格在布林带通道内运行")

        # 在技术指标分析部分添加换手率分析
        latest = recent_data.iloc[-1]
        if not pd.isna(latest['换手率']):
            print("\n换手率分析：")
            turnover = latest['换手率']
            if turnover > 20:
                print(f"当前换手率：{turnover:.2f}% - 换手率极高，表明交投十分活跃")
            elif turnover > 10:
                print(f"当前换手率：{turnover:.2f}% - 换手率较高，市场活跃度强")
            elif turnover > 5:
                print(f"当前换手率：{turnover:.2f}% - 换手率适中，成交较为活跃")
            else:
                print(f"当前换手率：{turnover:.2f}% - 换手率偏低，交投较为清淡")
            
        # 预测未来5个交易日的MA13和MA21
        ma13_predictions = predict_ma(recent_data, 13, 5)
        ma21_predictions = predict_ma(recent_data, 21, 5)
        
        last_date = recent_data.iloc[-1]['日期']
        future_dates = get_next_trading_dates(last_date, 5)
        
        print("\n未来5个交易日均线预测：")
        print("日期\t\tMA13预测\tMA21预测\t差值")
        print("-" * 50)
        for i in range(5):
            diff = ma13_predictions[i] - ma21_predictions[i]
            print(f"{future_dates[i]}\t{ma13_predictions[i]:.2f}\t{ma21_predictions[i]:.2f}\t{diff:.2f}")
        
        print("\n预测趋势分析：")
        ma13_trend = ma13_predictions[-1] - ma13_predictions[0]
        ma21_trend = ma21_predictions[-1] - ma21_predictions[0]
        print(f"MA13五日预测变化：{ma13_trend:.2f}")
        print(f"MA21五日预测变化：{ma21_trend:.2f}")
        
        # 综合分析和建议
        print("\n=== 综合分析和建议 ===")
        
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
            
        print("\n趋势信号：")
        if trend_signals:
            print("看多信号：")
            for signal in trend_signals:
                print(f"- {signal}")
        else:
            print("当前无明显看多信号")
            
        # 风险提示
        print("\n风险提示：")
        risks = []
        if latest['RSI'] > 70:
            risks.append("RSI处于超买区间，注意回调风险")
        if current_price > latest['BB_Upper']:
            risks.append("价格突破布林带上轨，注意回调风险")
        if latest_volume > avg_volume * 2:
            risks.append("成交量显著放大，注意价格变动风险")
        # 在风险提示部分添加换手率分析
        if not pd.isna(latest['换手率']) and latest['换手率'] > 15:
            risks.append(f"换手率达到{latest['换手率']:.2f}%，交易过于活跃，注意风险")
            
        if risks:
            for risk in risks:
                print(f"- {risk}")
        else:
            print("当前无明显风险信号")
        
        # 操作建议
        print("\n操作建议：")
        if len(trend_signals) >= 3 and not risks:
            print("可考虑逢低买入")
        elif len(risks) >= 2:
            print("建议保持谨慎，注意控制仓位")
        else:
            print("建议观望，等待更明确的信号")
        
    except Exception as e:
        print(f"获取数据时出错：{str(e)}")
        print("请检查网络连接或确认股票代码是否正确")

def main():
    print("\n请输入股票代码或指数代码，输入 'q' 退出：")
    print("\n股票代码格式：")
    print("- 直接输入代码：000001")
    print("- 带市场前缀：sh000001、sz000001、bj000001")
    print("\n指数代码支持两种格式：")
    print("- 000001（上证指数）、399001（深证成指）")
    print("- 1A0001（上证指数）")
    print("\n支持的主要指数：")
    print("- 上证指数：000001 或 1A0001")
    print("- 深证成指：399001")
    print("- 创业板指：399006")
    print("- 沪深300：000300")
    print("- 上证50：000016")
    print("- 中证500：399905")
    
    user_input = input().strip()
    if user_input.lower() == 'q':
        print("程序已退出")
        return
        
    if not is_valid_stock_code(user_input):
        print("代码格式错误，请输入正确的股票代码或指数代码")
        return
        
    print(f"\n正在获取 {user_input} 的数据...")
    analyze_stock_data(user_input)

if __name__ == "__main__":
    main()