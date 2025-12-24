@echo off
title ColorBridge PATH配置工具
color 0E

echo ===============================================
echo  🌈 ColorBridge - Windows PATH配置工具
echo ===============================================
echo.

:: 检查是否为管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  需要管理员权限才能修改系统PATH
    echo.
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo 或在管理员命令提示符中运行此脚本
    pause
    exit /b 1
)

echo ✅ 管理员权限检测通过

:: 查找Python Scripts目录
echo.
echo [INFO] 正在查找Python Scripts目录...
set PYTHON_SCRIPTS=

:: 方法1: 检查当前用户的Python
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    for /f "tokens=*" %%j in ('"%%~dpi\python.exe" -c "import sys; import os; scripts_dir = os.path.join(sys.prefix, 'Scripts'); print(scripts_dir if os.path.exists(scripts_dir) else '')" 2^>nul') do (
        if not "%%j"=="" (
            set PYTHON_SCRIPTS=%%j
            goto :found_scripts
        )
    )
)

:: 方法2: 检查常见的Python安装位置
set COMMON_PATHS=C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\Scripts;C:\Python314\Scripts;C:\Python\Scripts;C:\Program Files\Python\Scripts
for %%p in (%COMMON_PATHS%) do (
    if exist "%%p" (
        set PYTHON_SCRIPTS=%%p
        goto :found_scripts
    )
)

:found_scripts
if "%PYTHON_SCRIPTS%"=="" (
    echo ❌ 未找到Python Scripts目录
    echo.
    echo 请手动查找Python安装位置：
    echo 通常位于：
    echo   C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\Scripts
    echo   或 C:\Python314\Scripts
    echo   或 C:\Program Files\Python\Scripts
    pause
    exit /b 1
)

echo ✅ 找到Python Scripts目录: %PYTHON_SCRIPTS%

:: 检查是否已在PATH中
echo.
echo [INFO] 检查当前PATH...
echo %PATH% | find /i "%PYTHON_SCRIPTS%" >nul
if %errorlevel% equ 0 (
    echo ✅ Python Scripts目录已在PATH中
    echo.
    echo 现在可以运行: colorbridge --version
    pause
    exit /b 0
)

echo ⚠️  Python Scripts目录不在PATH中

:: 提供配置选项
echo.
echo ===============================================
echo             请选择配置方式
echo ===============================================
echo  1. 添加到用户PATH (推荐，无需重启)
echo  2. 添加到系统PATH (需要重启生效)
echo  3. 仅临时添加 (当前会话有效)
echo  4. 退出
echo ===============================================
echo.

set /p CHOICE="请选择 (1-4): "

if "%CHOICE%"=="1" goto :user_path
if "%CHOICE%"=="2" goto :system_path
if "%CHOICE%"=="3" goto :temp_path
if "%CHOICE%"=="4" goto :exit
goto :exit

:user_path
echo.
echo [INFO] 正在添加到用户PATH...
reg add "HKCU\Environment" /v "Path" /t REG_EXPAND_SZ /d "%PATH%;%PYTHON_SCRIPTS%" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 已添加到用户PATH
    echo.
    echo 📋 操作完成！
    echo   需要重启资源管理器或重新登录生效
    echo   或运行: refreshenv
    echo.
    echo 🚀 测试运行: python -m colorbridge --version
) else (
    echo ❌ 添加失败
)
goto :end

:system_path
echo.
echo [INFO] 正在添加到系统PATH...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v "Path" /t REG_EXPAND_SZ /d "%PATH%;%PYTHON_SCRIPTS%" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 已添加到系统PATH
    echo.
    echo 📋 操作完成！
    echo   需要重启计算机生效
    echo   或运行: refreshenv
    echo.
    echo 🚀 测试运行: python -m colorbridge --version
) else (
    echo ❌ 添加失败（可能需要更高权限）
)
goto :end

:temp_path
echo.
echo [INFO] 临时添加到当前会话PATH...
set PATH=%PATH%;%PYTHON_SCRIPTS%
echo ✅ 已临时添加到PATH
echo.
echo 📋 注意：仅在当前命令行窗口有效
echo   关闭窗口后需要重新配置
echo.
echo 🚀 测试运行: colorbridge --version
goto :end

:end
echo.
echo ===============================================
echo  💡 提示：如果colorbridge命令仍然不可用
echo  可以使用以下方式运行：
echo.
echo   python -m colorbridge --version
echo   或 "C:\Users\%USERNAME%\AppData\Roaming\Python\Python314\Scripts\colorbridge.exe" --version
echo ===============================================
pause
exit /b 0

:exit
echo.
echo 退出配置工具
pause
exit /b 0