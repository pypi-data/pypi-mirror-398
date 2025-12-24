#!/usr/bin/env python
"""
ColorBridge PATH自动配置模块
在安装过程中自动配置Windows PATH
"""

import os
import sys
import platform
import subprocess
import ctypes
import winreg

def is_admin():
    """检查是否为管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_python_scripts_dir():
    """获取Python Scripts目录"""
    import site
    
    # 方法0: 使用site.getuserbase()获取用户安装目录（pip install --user）
    try:
        if hasattr(site, 'getuserbase'):
            user_base = site.getuserbase()
            if user_base:
                user_scripts = os.path.join(user_base, 'Scripts')
                if os.path.exists(user_scripts):
                    return user_scripts
    except:
        pass
    
    # 方法1: 检查环境变量PYTHONUSERBASE
    python_user_base = os.environ.get('PYTHONUSERBASE')
    if python_user_base:
        user_scripts = os.path.join(python_user_base, 'Scripts')
        if os.path.exists(user_scripts):
            return user_scripts
    
    # 方法2: 使用sys.prefix（系统安装目录）
    scripts_dir = os.path.join(sys.prefix, 'Scripts')
    if os.path.exists(scripts_dir):
        return scripts_dir
    
    # 方法3: 检查常见的Python安装位置
    common_paths = [
        os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'Python', f'Python{sys.version_info.major}{sys.version_info.minor}', 'Scripts'),
        os.path.join('C:', os.sep, f'Python{sys.version_info.major}{sys.version_info.minor}', 'Scripts'),
        os.path.join('C:', os.sep, 'Python', 'Scripts'),
        os.path.join('C:', os.sep, 'Program Files', f'Python{sys.version_info.major}{sys.version_info.minor}', 'Scripts'),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def is_in_path(scripts_dir):
    """检查目录是否已在PATH中"""
    path_env = os.environ.get('PATH', '')
    return scripts_dir in path_env

def add_to_user_path(scripts_dir):
    """添加到用户PATH"""
    try:
        # 获取当前用户PATH
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            current_path, _ = winreg.QueryValueEx(key, 'Path')
            if scripts_dir in current_path:
                return True, "已在用户PATH中"
            
            # 添加到PATH末尾
            new_path = current_path + ';' + scripts_dir if current_path else scripts_dir
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            return True, "已成功添加到用户PATH"
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        return False, f"添加失败: {str(e)}"

def add_to_system_path(scripts_dir):
    """添加到系统PATH"""
    try:
        # 需要管理员权限
        if not is_admin():
            return False, "需要管理员权限"
        
        # 获取系统PATH
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 
                            0, winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            current_path, _ = winreg.QueryValueEx(key, 'Path')
            if scripts_dir in current_path:
                return True, "已在系统PATH中"
            
            # 添加到PATH末尾
            new_path = current_path + ';' + scripts_dir if current_path else scripts_dir
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            return True, "已成功添加到系统PATH"
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        return False, f"添加失败: {str(e)}"

def configure_path_automatically():
    """自动配置PATH"""
    system = platform.system()
    
    if system != "Windows":
        return True, "非Windows系统，PATH已自动配置"
    
    # 查找Python Scripts目录
    scripts_dir = get_python_scripts_dir()
    if not scripts_dir:
        return False, "未找到Python Scripts目录"
    
    # 检查是否已在PATH中
    if is_in_path(scripts_dir):
        return True, f"Python Scripts目录已在PATH中: {scripts_dir}"
    
    print(f"📋 找到Python Scripts目录: {scripts_dir}")
    print("🔄 正在自动配置PATH...")
    
    # 尝试添加到用户PATH（不需要管理员）
    success, message = add_to_user_path(scripts_dir)
    if success:
        print(f"✅ {message}")
        
        # 刷新环境变量
        try:
            # 发送环境变量更新消息
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment')
            print("✅ 已刷新环境变量")
        except:
            print("⚠️  需要重启命令行工具或重新登录生效")
        
        return True, message
    
    # 如果用户PATH添加失败，尝试系统PATH
    print("⚠️  用户PATH配置失败，尝试系统PATH...")
    success, message = add_to_system_path(scripts_dir)
    if success:
        print(f"✅ {message}")
        return True, message
    
    return False, message

def configure_path_interactive():
    """交互式配置PATH"""
    system = platform.system()
    
    if system != "Windows":
        print("✅ 非Windows系统，PATH已自动配置")
        return True
    
    print("\n" + "="*60)
    print("🌈 ColorBridge PATH配置工具")
    print("="*60)
    
    # 查找Python Scripts目录
    scripts_dir = get_python_scripts_dir()
    if not scripts_dir:
        print("❌ 未找到Python Scripts目录")
        print("\n💡 请手动添加以下路径到PATH:")
        print(f"   {os.path.join(sys.prefix, 'Scripts')}")
        return False
    
    print(f"📋 找到Python Scripts目录: {scripts_dir}")
    
    if is_in_path(scripts_dir):
        print("✅ Python Scripts目录已在PATH中")
        return True
    
    print("\n🔄 检测到PATH需要配置")
    print("\n请选择配置方式:")
    print("1. 自动配置 (推荐)")
    print("2. 手动配置")
    print("3. 跳过配置")
    
    try:
        choice = input("\n请选择 (1-3): ").strip()
    except:
        choice = "1"
    
    if choice == "1":
        success, message = configure_path_automatically()
        if success:
            print(f"\n✅ {message}")
            print("\n🚀 现在可以运行: colorbridge --version")
        else:
            print(f"\n❌ {message}")
            print("\n💡 请使用手动运行方式:")
            print(f'   python -m colorbridge --version')
        return success
    
    elif choice == "2":
        print("\n📝 手动配置步骤:")
        print("1. 右键'此电脑' -> 属性 -> 高级系统设置")
        print("2. 环境变量 -> 系统变量Path -> 编辑")
        print(f"3. 添加: {scripts_dir}")
        print("4. 重启命令行工具")
        return False
    
    else:
        print("\n⚠️  跳过PATH配置")
        print("\n💡 可以使用以下方式运行:")
        print(f'   python -m colorbridge --version')
        return True

def main():
    """主函数"""
    try:
        configure_path_interactive()
    except Exception as e:
        print(f"❌ 配置过程中出现错误: {e}")
        print("\n💡 可以使用以下方式运行:")
        print('   python -m colorbridge --version')

if __name__ == "__main__":
    main()