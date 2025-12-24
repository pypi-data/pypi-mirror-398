#!/usr/bin/env python
"""
ColorBridge 打包配置
正式版本，支持pip安装和跨平台
支持安装后自动配置Windows PATH
"""

import os
import sys
import platform
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


class CustomInstallCommand(install):
    """自定义安装命令 - 安装后自动配置PATH"""
    
    def run(self):
        # 调用父类安装
        install.run(self)
        
        # 显示安装成功消息
        print_post_install_message()
        
        # 尝试自动配置PATH
        self._try_configure_path()

    def _try_configure_path(self):
        """尝试自动配置PATH"""
        try:
            # 尝试导入PATH配置模块
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from colorbridge._path_config import configure_path_automatically
            
            print("\n🔄 正在尝试自动配置PATH...")
            success, message = configure_path_automatically()
            if success:
                print(f"✅ {message}")
            else:
                print(f"⚠️  {message}")
                print("💡 可以使用以下方式运行:")
                print(f'   python -m colorbridge --version')
                
        except ImportError as e:
            print(f"⚠️  无法导入PATH配置模块: {e}")
            print("💡 请手动运行 add_to_path_windows.bat 或参考安装后消息")
        except Exception as e:
            print(f"⚠️  PATH配置过程中出现错误: {e}")
            print("💡 可以使用以下方式运行:")
            print(f'   python -m colorbridge --version')


class CustomDevelopCommand(develop):
    """自定义开发模式安装命令"""
    
    def run(self):
        # 调用父类安装
        develop.run(self)
        
        # 显示开发模式安装消息
        print("🔧 开发模式安装完成！")
        print("💡 可以使用以下方式运行:")
        print(f'   python -m colorbridge --version')


# 安装后消息函数
def print_post_install_message():
    """安装后显示帮助信息"""
    system = platform.system()
    python_path = sys.executable
    
    print("\n" + "="*60)
    print("🎉 ColorBridge 安装成功！")
    print("="*60)
    
    if system == "Windows":
        print("\n📝 Windows 用户请注意：")
        print("由于Windows安全限制，Python Scripts目录可能不在PATH中。")
        print("\n🔄 推荐解决方案：")
        print("1. 自动配置PATH (最简单):")
        print("   运行: add_to_path_windows.bat (需要管理员权限)")
        print("   或使用: python -m colorbridge._path_config")
        
        print("\n2. 手动运行方式 (无需配置):")
        print(f'   使用: "{python_path}" -m colorbridge --version')
        print(f'   或: "{python_path}" -m colorbridge --help')
        
        print("\n3. 手动配置PATH:")
        print("   a. 右键'此电脑' -> 属性 -> 高级系统设置")
        print("   b. 环境变量 -> 系统变量Path -> 编辑")
        print("   c. 添加: C:\\Users\\%USERNAME%\\AppData\\Roaming\\Python\\Python314\\Scripts")
        print("   d. 重启命令行工具")
    else:
        print(f"\n✅ 安装完成！可以直接使用命令：")
        print("   colorbridge --version")
        print("   colorbridge --help")
    
    print("\n🔧 立即验证安装：")
    print(f'   "{python_path}" -m colorbridge --version')
    
    print("\n📚 完整文档：https://atomgit.com/H076lik/ColorBridge")
    print("💡 提示: 使用'ColorBridge启动器.bat'可获得最佳体验")
    print("="*60 + "\n")

# 读取 README 作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取 requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# 自动发现所有包
packages = find_packages(include=["colorbridge", "colorbridge.*", "core", "ui", "games", "games.billiard_3d"])

# 确保包含colorbridge包
if "colorbridge" not in packages:
    packages.append("colorbridge")

setup(
    name="colorbridge",
    version="2.1.17",
    author="076lik",
    author_email="m17859782086_1@163.com",
    description="🌈 ColorBridge - AI8051U串口助手，半透明多巴胺配色串口调试工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://atomgit.com/H076lik/ColorBridge",
    packages=packages,
    install_requires=requirements,
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "colorbridge=colorbridge.__main__:main",
        ],
        "gui_scripts": [
            "colorbridge-gui=colorbridge.__main__:main",
        ],
    },
    keywords="serial uart ai8051u usb-cdc debug embedded hardware",
    project_urls={
        "Homepage": "https://atomgit.com/H076lik/ColorBridge",
        "Repository": "https://atomgit.com/H076lik/ColorBridge.git",
        "Issues": "https://atomgit.com/H076lik/ColorBridge/issues",
    },
    # 平台支持
    platforms=["Windows", "Linux", "macOS"],
    # 自定义安装命令
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
    },
    # 项目分类
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
)