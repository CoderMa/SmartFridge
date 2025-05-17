#!/bin/bash
# 智能售卖柜后台管理系统启动脚本 - Linux版本

echo "正在启动智能售卖柜后台管理系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python环境，请安装Python 3.8或更高版本。"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip3 install -r requirements.txt
pip3 install flask flask-cors

# 创建后台目录（如果不存在）
mkdir -p backend/templates
mkdir -p backend/static

# 启动后台应用
echo "启动后台管理系统..."
cd backend
python3 app.py

echo "应用已关闭。"