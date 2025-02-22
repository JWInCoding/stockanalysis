#!/bin/bash

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "stock_env" ]; then
    echo "创建虚拟环境..."
    python3 -m venv stock_env
fi

# 激活虚拟环境
source stock_env/bin/activate

# 检查是否需要安装依赖
if ! pip list | grep -q "akshare"; then
    echo "安装依赖包..."
    pip install akshare pandas numpy
fi

# 运行股票分析脚本
python3 stock_data.py

# 保持终端窗口打开
exec $SHELL
