#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import akshare as ak
import re
from datetime import datetime, timedelta, date

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入项目模块
from src.utils.validators import is_valid_stock_code, normalize_stock_code
from src.utils.file_utils import ensure_dir


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


def run_script_safely(module_path, args, description):
    """安全执行脚本并处理异常"""
    try:
        print(f"   正在{description}...")
        
        # 构建模块路径 - 使用新的目录结构
        if module_path.startswith('stock_'):
            # 数据获取模块在 src/modules/ 目录下
            full_module_path = f"src.modules.{module_path.replace('.py', '')}"
        else:
            # 其他模块使用原始路径
            full_module_path = module_path.replace('.py', '').replace('/', '.')
        
        result = subprocess.run(
            ['python', '-m', full_module_path] + args,
            check=True,
            text=True,
            capture_output=True
        )
        print(f"   ✅ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description}失败: {e}")
        if e.stderr:
            print(f"   错误详情: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   ⚠️ 模块 {module_path} 不存在，跳过{description}")
        return False


def run_comprehensive_analysis(stock_code):
    """执行全面的股票数据获取分析"""
    # 标准化股票代码
    normalized_code = normalize_stock_code(stock_code)
    stock_name = get_stock_name(stock_code)
    
    # 创建输出目录结构 - 使用新的输出路径
    today = datetime.now().strftime('%Y%m%d')
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    output_dir = ensure_dir(os.path.join(project_root, "outputs", "stock_results", today))
    
    # 生成当前时间戳，用于文件名
    timestamp = datetime.now().strftime('%H%M%S')
    
    # 设置输出文件名 (加入股票名称)
    name_part = f"_{stock_name}" if stock_name else ""
    
    print(f"===== 开始全面分析股票 {normalized_code} ({stock_name}) =====")
    
    # 定义所有分析脚本和对应的输出文件
    analysis_scripts = [
        {
            'script': 'stock_data.py',
            'description': '获取日线数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_日线数据_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_minute_data.py', 
            'description': '获取分钟级数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_分钟级数据_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_fundamental.py',
            'description': '获取基本面数据', 
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_基本面数据_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_industry.py',
            'description': '获取行业板块数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_行业数据_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_capital_flow.py',
            'description': '获取资金流向数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_资金流向_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_index_component.py',
            'description': '获取指数成分股数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_指数成分股_{today}_{timestamp}.txt")
        },
        {
            'script': 'stock_sentiment.py',
            'description': '获取市场情绪数据',
            'output': os.path.join(output_dir, f"{normalized_code}{name_part}_市场情绪_{today}_{timestamp}.txt")
        }
    ]
    
    successful_analyses = 0
    total_analyses = len(analysis_scripts)
    
    print(f"\n开始执行 {total_analyses} 项数据获取任务:")
    
    # 执行所有分析脚本
    for i, analysis in enumerate(analysis_scripts, 1):
        print(f"\n{i}. {analysis['description']}")
        
        success = run_script_safely(
            analysis['script'],
            [normalized_code, analysis['output']],
            analysis['description']
        )
        
        if success:
            successful_analyses += 1
            print(f"   📁 数据已保存至: {os.path.basename(analysis['output'])}")
    
    # 输出总结
    print(f"\n===== 分析完成总结 =====")
    print(f"股票代码: {normalized_code} ({stock_name})")
    print(f"成功完成: {successful_analyses}/{total_analyses} 项数据获取")
    print(f"结果目录: {output_dir}")
    
    if successful_analyses == total_analyses:
        print("🎉 所有数据获取任务均已成功完成!")
    elif successful_analyses > 0:
        print("⚠️ 部分数据获取任务完成，请检查失败的任务")
    else:
        print("❌ 所有数据获取任务均失败，请检查网络连接和代码")
    
    return successful_analyses, total_analyses


def run_basic_analysis(stock_code):
    """执行基础的股票分析（仅日线和分钟级数据）"""
    # 标准化股票代码
    normalized_code = normalize_stock_code(stock_code) 
    stock_name = get_stock_name(stock_code)
    
    # 创建输出目录结构
    today = datetime.now().strftime('%Y%m%d')
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    output_dir = ensure_dir(os.path.join(project_root, "outputs", "stock_results", today))
    
    # 生成当前时间戳，用于文件名
    timestamp = datetime.now().strftime('%H%M%S')
    
    # 设置输出文件名 (加入股票名称)
    name_part = f"_{stock_name}" if stock_name else ""
    daily_output_file = os.path.join(output_dir, f"{normalized_code}{name_part}_日线数据_{today}_{timestamp}.txt")
    minute_output_file = os.path.join(output_dir, f"{normalized_code}{name_part}_分钟级数据_{today}_{timestamp}.txt")
    
    print(f"===== 开始基础分析股票 {normalized_code} ({stock_name}) =====")

    success_count = 0
    
    # 执行日线数据分析脚本
    print("\n1. 正在获取股票日线数据...")
    if run_script_safely('stock_data.py', [normalized_code, daily_output_file], '获取日线数据'):
        success_count += 1
        print(f"   📁 日线数据已保存至: {os.path.basename(daily_output_file)}")

    # 执行分钟级数据分析脚本
    print("\n2. 正在获取股票分钟级数据...")
    if run_script_safely('stock_minute_data.py', [normalized_code, minute_output_file], '获取分钟级数据'):
        success_count += 1
        print(f"   📁 分钟级数据已保存至: {os.path.basename(minute_output_file)}")
        
    print(f"\n===== 基础分析完成 ({success_count}/2) =====")
    print(f"结果目录: {output_dir}")


def show_analysis_menu():
    """显示分析模式选择菜单"""
    print("\n请选择分析模式:")
    print("1. 基础分析 (日线 + 分钟级数据)")
    print("2. 全面分析 (包含基本面、行业、资金流向等所有数据)")
    print("3. 自定义分析 (选择特定的数据类型)")
    
    while True:
        choice = input("\n请输入选择 (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("无效选择，请输入 1、2 或 3")


def show_custom_analysis_menu():
    """显示自定义分析菜单"""
    print("\n可选的数据获取模块:")
    modules = [
        ("日线数据", "stock_data.py"),
        ("分钟级数据", "stock_minute_data.py"), 
        ("基本面数据", "stock_fundamental.py"),
        ("行业板块数据", "stock_industry.py"),
        ("资金流向数据", "stock_capital_flow.py"),
        ("指数成分股数据", "stock_index_component.py"),
        ("市场情绪数据", "stock_sentiment.py")
    ]
    
    for i, (name, _) in enumerate(modules, 1):
        print(f"{i}. {name}")
    
    print("\n请输入要执行的模块编号，用逗号分隔 (如: 1,3,5):")
    while True:
        choice = input("选择: ").strip()
        try:
            selected = [int(x.strip()) for x in choice.split(',')]
            if all(1 <= x <= len(modules) for x in selected):
                return [modules[x-1] for x in selected]
            else:
                print("编号超出范围，请重新输入")
        except ValueError:
            print("输入格式错误，请用逗号分隔数字")


def run_custom_analysis(stock_code, selected_modules):
    """执行自定义分析"""
    # 标准化股票代码
    normalized_code = normalize_stock_code(stock_code)
    stock_name = get_stock_name(stock_code)
    
    # 创建输出目录结构
    today = datetime.now().strftime('%Y%m%d')
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    output_dir = ensure_dir(os.path.join(project_root, "outputs", "stock_results", today))
    
    # 生成当前时间戳，用于文件名
    timestamp = datetime.now().strftime('%H%M%S')
    name_part = f"_{stock_name}" if stock_name else ""
    
    print(f"===== 开始自定义分析股票 {normalized_code} ({stock_name}) =====")
    
    success_count = 0
    total_count = len(selected_modules)
    
    for i, (module_name, script_name) in enumerate(selected_modules, 1):
        # 生成输出文件名
        file_suffix = module_name.replace('数据', '').replace('级', '级')
        output_file = os.path.join(output_dir, f"{normalized_code}{name_part}_{file_suffix}_{today}_{timestamp}.txt")
        
        print(f"\n{i}. 正在{module_name}获取...")
        if run_script_safely(script_name, [normalized_code, output_file], module_name + '获取'):
            success_count += 1
            print(f"   📁 {module_name}已保存至: {os.path.basename(output_file)}")
    
    print(f"\n===== 自定义分析完成 ({success_count}/{total_count}) =====")
    print(f"结果目录: {output_dir}")


def main():
    """主函数"""
    # 显示欢迎信息
    print("=" * 60)
    print("股票数据分析工具 v2.1 - 模块化版本")
    print("支持技术面、基本面、行业面、资金面等全方位数据获取")
    print("=" * 60)
    
    # 获取用户输入
    if len(sys.argv) > 1:
        # 从命令行参数获取股票代码
        stock_code = sys.argv[1]
        analysis_mode = sys.argv[2] if len(sys.argv) > 2 else '1'
    else:
        # 交互式输入股票代码
        print("\n请输入股票代码或指数代码，例如:")
        print("- 直接输入代码：000001、002354")
        print("- 带市场前缀：sh000001、sz000001")
        print("- 指数代码：000001（上证指数）、399001（深证成指）")
        stock_code = input("\n请输入股票代码: ").strip()
        
        analysis_mode = show_analysis_menu()
    
    # 验证股票代码
    if not stock_code:
        print("未输入有效的股票代码，程序退出")
        return
        
    if not is_valid_stock_code(stock_code):
        print("代码格式错误，请输入正确的股票代码或指数代码")
        return
    
    # 根据选择执行不同的分析模式
    if analysis_mode == '1':
        run_basic_analysis(stock_code)
    elif analysis_mode == '2':
        run_comprehensive_analysis(stock_code)
    elif analysis_mode == '3':
        selected_modules = show_custom_analysis_menu()
        run_custom_analysis(stock_code, selected_modules)


def continuous_main():
    """支持连续分析多只股票的主函数"""
    # 显示欢迎信息
    print("=" * 60)
    print("股票数据分析工具 v2.1 - 模块化连续分析版")
    print("支持技术面、基本面、行业面、资金面等全方位数据获取")
    print("=" * 60)
    
    # 获取第一只股票代码
    if len(sys.argv) > 1:
        # 从命令行参数获取股票代码
        stock_code = sys.argv[1]
    else:
        # 交互式输入股票代码
        print("\n请输入股票代码或指数代码，例如:")
        print("- 直接输入代码：000001、002354")
        print("- 带市场前缀：sh000001、sz000001") 
        print("- 指数代码：000001（上证指数）、399001（深证成指）")
        stock_code = input("\n请输入股票代码: ").strip()
    
    # 验证并分析第一只股票
    if not stock_code:
        print("未输入有效的股票代码，程序退出")
        return
        
    if not is_valid_stock_code(stock_code):
        print("代码格式错误，请输入正确的股票代码或指数代码")
        return
    
    # 选择分析模式（首次）
    analysis_mode = show_analysis_menu()
    
    # 执行第一次分析
    if analysis_mode == '1':
        run_basic_analysis(stock_code)
    elif analysis_mode == '2':
        run_comprehensive_analysis(stock_code)
    elif analysis_mode == '3':
        selected_modules = show_custom_analysis_menu()
        run_custom_analysis(stock_code, selected_modules)
    
    # 连续分析循环
    while True:
        print("\n" + "="*50)
        print("\033[0;33m输入股票代码继续分析，直接回车退出:\033[0m", end=" ")
        stock_code = input().strip()
        
        if not stock_code:
            print("\033[0;32m谢谢使用，分析结果在 outputs/stock_results 目录!\033[0m")
            break
            
        if not is_valid_stock_code(stock_code):
            print("代码格式错误，请输入正确的股票代码或指数代码")
            continue
        
        # 询问是否使用相同的分析模式
        use_same_mode = input("使用相同的分析模式? (y/n，默认y): ").strip().lower()
        if use_same_mode != 'n':
            # 使用相同模式
            if analysis_mode == '1':
                run_basic_analysis(stock_code)
            elif analysis_mode == '2':
                run_comprehensive_analysis(stock_code)
            elif analysis_mode == '3':
                run_custom_analysis(stock_code, selected_modules)
        else:
            # 重新选择模式
            analysis_mode = show_analysis_menu()
            if analysis_mode == '1':
                run_basic_analysis(stock_code)
            elif analysis_mode == '2':
                run_comprehensive_analysis(stock_code)
            elif analysis_mode == '3':
                selected_modules = show_custom_analysis_menu()
                run_custom_analysis(stock_code, selected_modules)


if __name__ == "__main__":
    continuous_main()  # 使用支持连续分析的主函数