@echo off
:: ColorBridge Windows启动脚本
:: 自动检测Python并启动ColorBridge

echo ========================================
echo  🌈 ColorBridge - AI8051U串口助手
echo ========================================

:: 检查Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查ColorBridge是否安装
python -c "import colorbridge; print('✅ ColorBridge已安装')" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ColorBridge未安装
    echo    请运行: pip install colorbridge
    pause
    exit /b 1
)

:: 启动ColorBridge
echo 🚀 启动ColorBridge...
python -m colorbridge %*

if %ERRORLEVEL% NEQ 0 (
    echo ❌ ColorBridge启动失败
    pause
    exit /b %ERRORLEVEL%
)