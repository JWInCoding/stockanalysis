#!/bin/bash

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 简化颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${GREEN}===== 股票数据分析工具 =====${NC}"

# 检查虚拟环境
if [ ! -d "stock_env" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv stock_env
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source stock_env/bin/activate

# 检查AKShare版本
if pip list 2>/dev/null | grep -q "akshare"; then
    # 获取当前版本
    CURRENT_VERSION=$(pip show akshare 2>/dev/null | grep Version | cut -d ' ' -f 2)
    echo -e "当前AKShare版本: ${GREEN}$CURRENT_VERSION${NC}"
    
    # 尝试获取最新版本（简单方法）
    LATEST_VERSION=$(python -c "
import json, urllib.request, sys
try:
    with urllib.request.urlopen('https://pypi.org/pypi/akshare/json', timeout=2) as r:
        print(json.loads(r.read())['info']['version'])
except: pass" 2>/dev/null)
    
    # 仅当有新版本时才提示更新
    if [ ! -z "$LATEST_VERSION" ] && [ "$LATEST_VERSION" != "$CURRENT_VERSION" ]; then
        echo -e "PyPI上最新版本: ${GREEN}$LATEST_VERSION${NC}"
        read -p "是否更新AKShare? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip install --upgrade akshare 2>/dev/null
        fi
    fi
else
    # 安装依赖包
    echo "安装依赖包..."
    pip install akshare pandas numpy 2>/dev/null
fi

# 运行分析脚本(此脚本将自行处理循环分析逻辑)
echo -e "${GREEN}启动分析脚本...${NC}"
python3 stock_analyzer.py

# 脚本结束
echo -e "${GREEN}分析结束!${NC}"