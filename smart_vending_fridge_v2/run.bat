@echo off
REM 智能售卖柜启动脚本 - Windows版本

echo 正在启动智能售卖柜控制系统...

REM 检查Python环境
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python环境，请安装Python 3.8或更高版本。
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip install -r requirements.txt

REM 启动应用
echo 启动应用...
python src\main.py %*

echo 应用已关闭。