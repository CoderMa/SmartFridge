#!/bin/bash
# 智能售卖柜启动脚本 - Linux版本

echo "正在启动智能售卖柜控制系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python环境，请安装Python 3.8或更高版本。"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip3 install -r requirements.txt

# 启动应用
echo "启动应用..."
python3 src/main.py "$@"

echo "应用已关闭。"