#!/bin/bash

# 重定向标准错误输出到/dev/null来抑制pip的警告
exec 2>/dev/null

# 检查虚拟环境是否已经激活
if [[ "$VIRTUAL_ENV" != "" ]]; then
    # 如果已经激活，直接运行脚本
    python3 stock_data.py
else
    # 如果未激活，则激活虚拟环境（重定向错误输出）
    source stock_env/bin/activate 2>/dev/null

    # 如果是首次运行，安装依赖包（重定向所有输出）
    if ! pip list 2>/dev/null | grep -q "akshare"; then
        pip install akshare pandas numpy >/dev/null 2>&1
    fi

    # 运行股票分析脚本
    python3 stock_data.py
fi

# 运行完成后保持终端窗口
exec $SHELL
