@echo off
chcp 65001 >nul
REM 智能售卖柜后台管理系统启动脚本 - Windows版本

echo 正在启动智能售卖柜后台管理系统...

REM 检查Python环境
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python环境，请安装Python 3.8或更高版本。
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip install -r requirements.txt
pip install flask flask-cors

REM 创建后台目录（如果不存在）
if not exist "backend" mkdir backend
if not exist "backend\templates" mkdir backend\templates
if not exist "backend\static" mkdir backend\static

REM 启动后台应用
echo 启动后台管理系统...
cd backend
python app.py

echo 应用已关闭。