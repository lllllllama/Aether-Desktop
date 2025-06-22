@echo off
REM Aether Desktop 测试脚本
REM ======================

echo.
echo ======================================
echo    Aether Desktop 功能测试
echo ======================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

echo 正在运行功能测试...
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 运行测试脚本
python test_aether.py

echo.
echo 测试完成！
pause
