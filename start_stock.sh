#!/bin/bash

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'  # 无颜色

echo -e "${GREEN}===== 股票数据分析工具 =====${NC}"

# 检查虚拟环境是否存在
if [ ! -d "stock_env" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv stock_env
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source stock_env/bin/activate

# 检查AKShare版本
if pip list | grep -q "akshare"; then
    AKSHARE_VERSION=$(pip show akshare | grep Version | cut -d ' ' -f 2)
    echo -e "当前AKShare版本: ${GREEN}$AKSHARE_VERSION${NC}"
    
    # 询问是否更新
    read -p "是否更新AKShare到最新版本? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "更新AKShare..."
        pip install --upgrade akshare
    fi
else
    # 安装依赖包
    echo "安装依赖包..."
    pip install akshare pandas numpy
fi

# 运行股票分析脚本
echo -e "${GREEN}启动分析脚本...${NC}"
python3 stock_analyzer.py

# 保持终端窗口打开
echo -e "${YELLOW}分析完成! 按Enter键退出...${NC}"
read
exec $SHELL