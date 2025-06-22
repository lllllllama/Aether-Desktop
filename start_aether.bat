@echo off
REM Aether Desktop 启动脚本
REM ========================

echo.
echo ======================================
echo    Aether Desktop 智能桌面管家
echo ======================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请确保已安装Python并添加到PATH环境变量
    pause
    exit /b 1
)

REM 显示Python版本
echo 检测到Python环境:
python --version

echo.
echo 正在启动 Aether Desktop...
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 启动主程序
python main.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    echo.
    echo 常见问题解决方案:
    echo 1. 确保已安装所有依赖包: pip install -r requirements.txt
    echo 2. 检查配置文件 config.ini 是否正确
    echo 3. 确保有足够的系统权限
    echo 4. 查看日志文件了解详细错误信息
    echo.
    pause
)
