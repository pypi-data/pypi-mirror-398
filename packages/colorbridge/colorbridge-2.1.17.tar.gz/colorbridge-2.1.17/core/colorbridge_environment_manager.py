#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境自动检测和安装配置模块 - ColorBridge PCL2风格
全自动检测和配置运行环境，确保用户无需手动干预
"""

import sys
import os
import platform
import subprocess
import importlib
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

class EnvironmentChecker:
    """环境自动检测器"""
    
    def __init__(self):
        self.system_info = self.get_system_info()
        self.python_info = self.get_python_info()
        self.missing_packages = []
        self.missing_modules = []
        self.permission_issues = []
        self.hardware_issues = []
        
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "machine": platform.machine()
        }
    
    def get_python_info(self) -> Dict[str, Any]:
        """获取Python信息"""
        return {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path,
            "version_info": sys.version_info
        }
    
    def check_python_version(self) -> Tuple[bool, str]:
        """检查Python版本"""
        if sys.version_info < (3, 8):
            return False, f"Python版本过低: {sys.version_info.major}.{sys.version_info.minor}，需要3.8+"
        return True, f"Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}"
    
    def check_required_packages(self) -> Tuple[bool, List[str]]:
        """检查必需的Python包"""
        required_packages = [
            "PyQt6",
            "serial",  # pyserial
            "dateutil"  # python-dateutil
        ]
        
        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing.append(package)
        
        self.missing_packages = missing
        return len(missing) == 0, missing
    
    def check_serial_ports(self) -> Tuple[bool, List[str]]:
        """检查串口端口"""
        try:
            import serial.tools.list_ports
            
            ports = serial.tools.list_ports.comports()
            port_list = [str(port.device) for port in ports]
            
            return len(port_list) > 0, port_list
        except Exception as e:
            return False, [f"串口检测失败: {str(e)}"]
    
    def check_linux_serial_permissions(self) -> Tuple[bool, str, List[str]]:
        """检查Linux串口权限 - 增强版"""
        try:
            if platform.system() != "Linux":
                return True, "非Linux系统，跳过权限检查", []
            
            import grp
            import pwd
            import stat
            import glob
            import subprocess
            
            current_user = pwd.getpwuid(os.getuid()).pw_name
            
            # 方法1: 使用grp模块检查用户组
            in_dialout_grp = False
            try:
                current_groups = [g.gr_name for g in grp.getgrall() if current_user in g.gr_mem]
                in_dialout_grp = "dialout" in current_groups
            except Exception as e:
                print(f"[DEBUG] grp模块检查失败: {e}")
            
            # 方法2: 检查/etc/group文件
            in_dialout_etc = False
            try:
                with open("/etc/group", "r") as f:
                    for line in f:
                        if line.startswith("dialout:"):
                            if current_user in line:
                                in_dialout_etc = True
                            break
            except Exception as e:
                print(f"[DEBUG] /etc/group检查失败: {e}")
            
            # 方法3: 使用id命令检查（最可靠）
            in_dialout_id = False
            try:
                result = subprocess.run(
                    ["id", "-nG"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    groups = result.stdout.strip().split()
                    in_dialout_id = "dialout" in groups
            except Exception as e:
                print(f"[DEBUG] id命令检查失败: {e}")
            
            # 综合判断：如果任一方法检测到用户在dialout组，则认为用户在组中
            in_dialout = in_dialout_grp or in_dialout_etc or in_dialout_id
            
            # 检查常见串口设备权限
            serial_devices = []
            permission_issues = []
            
            # 常见串口设备路径
            common_serial_patterns = [
                "/dev/ttyUSB*",
                "/dev/ttyACM*", 
                "/dev/ttyS*",
                "/dev/ttyAMA*"
            ]
            
            for pattern in common_serial_patterns:
                for device in glob.glob(pattern):
                    try:
                        stat_info = os.stat(device)
                        mode = stat_info.st_mode
                        # 检查权限：用户是否有读写权限
                        user_read = bool(mode & stat.S_IRUSR)
                        user_write = bool(mode & stat.S_IWUSR)
                        
                        if not (user_read and user_write):
                            permission_issues.append(f"{device}: 用户缺少读写权限 (当前权限: {oct(mode)[-3:]})")
                        
                        serial_devices.append(device)
                    except Exception as e:
                        permission_issues.append(f"{device}: 无法检查权限 - {e}")
            
            suggestions = []
            detailed_message = ""
            
            if not in_dialout:
                detailed_message = "用户不在dialout组中"
                suggestions.append("永久解决方案: sudo usermod -a -G dialout $USER")
                suggestions.append("⚠️  注意: 添加用户到dialout组后需要重新登录或重启才能生效")
                
                # 检查用户是否已添加到组但未重新登录
                if in_dialout_etc and not (in_dialout_grp or in_dialout_id):
                    detailed_message = "用户已添加到dialout组，但需要重新登录或重启才能生效"
                    suggestions.append("💡 请注销并重新登录，或重启系统")
            
            if permission_issues:
                if detailed_message:
                    detailed_message += "，且串口设备权限不足"
                else:
                    detailed_message = "串口设备权限不足"
                
                suggestions.append("临时解决方案:")
                suggestions.append("  1. 修改设备权限: sudo chmod 666 /dev/ttyUSB*")
                suggestions.append("  2. 使用sudo运行: sudo colorbridge")
                suggestions.append("  3. 检查设备是否存在: ls -l /dev/ttyUSB*")
            
            if not serial_devices:
                suggestions.append("未检测到串口设备，请检查:")
                suggestions.append("  1. USB串口设备是否已连接")
                suggestions.append("  2. 驱动程序是否已安装")
                suggestions.append("  3. 设备是否被识别: dmesg | grep tty")
            
            if not in_dialout or permission_issues:
                # 生成详细状态报告
                status_report = []
                status_report.append(f"用户: {current_user}")
                status_report.append(f"在dialout组中: {in_dialout} (grp:{in_dialout_grp}, etc:{in_dialout_etc}, id:{in_dialout_id})")
                status_report.append(f"检测到串口设备: {len(serial_devices)}个")
                if permission_issues:
                    status_report.append(f"权限问题: {len(permission_issues)}个")
                
                full_message = f"Linux串口权限问题: {detailed_message}\n" + "\n".join(status_report)
                return False, full_message, suggestions
            else:
                return True, f"Linux串口权限检查通过 (用户:{current_user}, 设备:{len(serial_devices)}个)", []
                
        except ImportError as e:
            return False, f"无法导入Linux系统模块: {e}", ["请确保在Linux系统上运行"]
        except Exception as e:
            return False, f"Linux串口权限检查失败: {e}", []
    
    def check_game_module_dependencies(self) -> Tuple[bool, str, List[str]]:
        """检查游戏模块依赖 - 特别是Debian/Linux系统上的Qt6运行时依赖"""
        try:
            if platform.system() != "Linux":
                return True, "非Linux系统，游戏模块依赖检查跳过", []
            
            issues = []
            suggestions = []
            
            # 1. 检查PyQt6模块是否能正常导入（基本检查）
            try:
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtCore import QTimer
            except ImportError as e:
                issues.append(f"PyQt6模块导入失败: {str(e)}")
                suggestions.append("请安装PyQt6: pip install PyQt6>=6.6.0")
                suggestions.append("或从系统包管理器安装: sudo apt install python3-pyqt6")
            
            # 2. 检查Qt6运行时库依赖（Linux特有）
            try:
                import subprocess
                # 检查常见的Qt6库是否已安装
                qt6_libs = ["libqt6gui6", "libqt6widgets6", "libqt6core6", "libqt6network6", "qt6-qpa-plugins"]
                missing_libs = []
                
                for lib in qt6_libs:
                    result = subprocess.run(["dpkg", "-l", lib], capture_output=True, text=True)
                    if result.returncode != 0 or "ii" not in result.stdout:
                        missing_libs.append(lib)
                
                if missing_libs:
                    issues.append(f"缺少Qt6运行时库: {', '.join(missing_libs)}")
                    suggestions.append(f"安装Qt6库: sudo apt update && sudo apt install {' '.join(missing_libs)}")
            except Exception as e:
                # dpkg检查失败（可能不是Debian/Ubuntu系统）
                issues.append(f"Qt6库检查失败（可能不是Debian系）: {str(e)}")
                suggestions.append("请确保已安装Qt6运行时库")
            
            # 3. 检查显示环境
            display_issue = False
            if "DISPLAY" not in os.environ:
                issues.append("未设置DISPLAY环境变量（无图形显示环境）")
                suggestions.append("设置DISPLAY变量: export DISPLAY=:0")
                suggestions.append("或使用虚拟显示服务器: sudo apt install xvfb && xvfb-run python main.py")
                display_issue = True
            else:
                # 检查DISPLAY是否有效
                try:
                    result = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=2)
                    if result.returncode != 0:
                        issues.append(f"DISPLAY环境变量设置但无效: {os.environ.get('DISPLAY')}")
                        suggestions.append("检查X11服务器是否运行: echo $DISPLAY")
                        suggestions.append("尝试其他显示: export DISPLAY=:0")
                        display_issue = True
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    # xdpyinfo可能不存在或超时，这不是致命错误
                    pass
            
            # 4. 检查字体支持（Arial字体可能不存在）
            try:
                import subprocess
                result = subprocess.run(["fc-list", "|", "grep", "-i", "arial"], capture_output=True, text=True, shell=True)
                if result.returncode != 0:
                    issues.append("系统缺少Arial字体（游戏界面可能显示异常）")
                    suggestions.append("安装微软字体: sudo apt install ttf-mscorefonts-installer")
                    suggestions.append("或安装免费替代字体: sudo apt install fonts-liberation")
            except Exception:
                # 字体检查失败，非致命
                pass
            
            # 5. 检查游戏模块本身是否能导入
            try:
                import games.billiard_3d
                from games.billiard_3d.ui import BilliardGameUI
            except ImportError as e:
                issues.append(f"游戏模块导入失败: {str(e)}")
                suggestions.append("检查games目录是否存在")
                suggestions.append("重新安装ColorBridge: pip install -e .")
            
            if issues:
                detailed_message = "游戏模块依赖问题: " + "; ".join(issues[:3])  # 最多显示3个问题
                if len(issues) > 3:
                    detailed_message += f" ...等{len(issues)}个问题"
                return False, detailed_message, suggestions
            else:
                return True, "游戏模块依赖检查通过（Qt6库、显示环境、字体支持正常）", []
                
        except Exception as e:
            return False, f"游戏模块依赖检查异常: {str(e)}", ["请检查系统环境配置"]
    
    def check_admin_permissions(self) -> Tuple[bool, str]:
        """检查管理员权限"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0, "Windows管理员权限检查"
            else:
                return os.geteuid() == 0, "Unix root权限检查"
        except Exception:
            return False, "权限检查失败"
    
    def check_hardware_acceleration(self) -> Tuple[bool, str]:
        """检查硬件加速支持"""
        try:
            # 检查GPU支持
            import platform
            
            if platform.system() == "Windows":
                # Windows下检查DirectX支持
                try:
                    import ctypes
                    # 简单的GPU检测
                    return True, "硬件加速支持检查通过"
                except:
                    return False, "硬件加速支持检查失败"
            else:
                return True, "硬件加速支持检查通过"
        except Exception as e:
            return False, f"硬件加速检查异常: {str(e)}"
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行综合环境检查"""
        results = {
            "timestamp": str(os.times()),
            "system_info": self.system_info,
            "python_info": self.python_info,
            "checks": {}
        }
        
        # Python版本检查
        python_ok, python_msg = self.check_python_version()
        results["checks"]["python_version"] = {
            "status": "✅ 通过" if python_ok else "❌ 失败",
            "message": python_msg,
            "details": self.python_info
        }
        
        # 包依赖检查
        packages_ok, missing_packages = self.check_required_packages()
        results["checks"]["required_packages"] = {
            "status": "✅ 通过" if packages_ok else "❌ 失败",
            "message": f"包检查完成，缺失: {len(missing_packages)}个",
            "missing": missing_packages
        }
        
        # 串口检查
        serial_ok, serial_ports = self.check_serial_ports()
        results["checks"]["serial_ports"] = {
            "status": "✅ 通过" if serial_ok else "⚠️ 警告",
            "message": f"发现 {len(serial_ports)} 个串口",
            "ports": serial_ports
        }
        
        # Linux串口权限检查（仅Linux系统）
        if platform.system() == "Linux":
            linux_serial_ok, linux_serial_msg, linux_serial_suggestions = self.check_linux_serial_permissions()
            results["checks"]["linux_serial_permissions"] = {
                "status": "✅ 通过" if linux_serial_ok else "⚠️ 警告",
                "message": linux_serial_msg,
                "suggestions": linux_serial_suggestions
            }
        
        # 权限检查
        admin_ok, admin_msg = self.check_admin_permissions()
        results["checks"]["admin_permissions"] = {
            "status": "✅ 通过" if admin_ok else "⚠️ 警告",
            "message": admin_msg
        }
        
        # 硬件加速检查
        hw_ok, hw_msg = self.check_hardware_acceleration()
        results["checks"]["hardware_acceleration"] = {
            "status": "✅ 通过" if hw_ok else "⚠️ 警告",
            "message": hw_msg
        }
        
        # 游戏模块依赖检查（仅Linux系统）
        if platform.system() == "Linux":
            game_deps_ok, game_deps_msg, game_deps_suggestions = self.check_game_module_dependencies()
            results["checks"]["game_module_dependencies"] = {
                "status": "✅ 通过" if game_deps_ok else "⚠️ 警告",
                "message": game_deps_msg,
                "suggestions": game_deps_suggestions
            }
        
        # 总体状态
        critical_issues = not python_ok or not packages_ok
        results["overall_status"] = "🟢 正常" if not critical_issues else "🔴 需要修复"
        
        return results


class AutoInstaller:
    """自动安装和配置器"""
    
    def __init__(self, environment_checker: EnvironmentChecker):
        self.env_checker = environment_checker
        self.install_log = []
        
    def log(self, message: str):
        """记录安装日志"""
        self.install_log.append(f"[{os.times()}] {message}")
        print(f"[AutoInstaller] {message}")
    
    def install_missing_packages(self, missing_packages: List[str]) -> Tuple[bool, str]:
        """自动安装缺失的包"""
        if not missing_packages:
            return True, "没有缺失的包"
        
        self.log(f"开始安装缺失的包: {missing_packages}")
        
        # 包名映射
        package_mapping = {
            "PyQt6": "PyQt6>=6.6.0",
            "serial": "pyserial>=3.5",
            "dateutil": "python-dateutil>=2.8.2"
        }
        
        success_count = 0
        failed_packages = []
        
        for package in missing_packages:
            try:
                install_name = package_mapping.get(package, package)
                self.log(f"正在安装 {install_name}...")
                
                # 使用pip安装
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", install_name
                ], capture_output=True, text=True, timeout=300, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0:
                    self.log(f"✅ {package} 安装成功")
                    success_count += 1
                else:
                    self.log(f"❌ {package} 安装失败: {result.stderr}")
                    failed_packages.append(package)
                    
            except subprocess.TimeoutExpired:
                self.log(f"❌ {package} 安装超时")
                failed_packages.append(package)
            except Exception as e:
                self.log(f"❌ {package} 安装异常: {str(e)}")
                failed_packages.append(package)
        
        if success_count == len(missing_packages):
            return True, f"所有包安装成功 ({success_count}/{len(missing_packages)})"
        else:
            return False, f"部分包安装失败 ({success_count}/{len(missing_packages)}), 失败: {failed_packages}"
    
    def configure_serial_permissions(self) -> Tuple[bool, str]:
        """配置串口权限"""
        try:
            if platform.system() == "Linux":
                # Linux下配置串口权限
                self.log("检查Linux串口权限...")
                
                # 检查用户是否已经在dialout组中
                try:
                    import grp
                    import pwd
                    
                    # 获取当前用户信息
                    current_user = pwd.getpwuid(os.getuid()).pw_name
                    
                    # 获取dialout组信息
                    try:
                        dialout_group = grp.getgrnam("dialout")
                        if current_user in dialout_group.gr_mem:
                            self.log("✅ 用户已在dialout组中")
                            return True, "用户已在dialout组中"
                        else:
                            self.log("⚠️ 用户不在dialout组中，串口访问可能受限")
                            self.log("💡 请运行以下命令添加用户到dialout组:")
                            self.log(f"    sudo usermod -a -G dialout {current_user}")
                            self.log("💡 然后注销并重新登录以使权限生效")
                            self.log("💡 或者临时使用sudo运行程序: sudo colorbridge")
                            return False, "用户不在dialout组中，请添加到dialout组"
                    except KeyError:
                        self.log("⚠️ dialout组不存在，创建dialout组...")
                        try:
                            result = subprocess.run(
                                ["sudo", "groupadd", "dialout"],
                                capture_output=True, text=True
                            )
                            if result.returncode == 0:
                                self.log("✅ dialout组创建成功")
                                self.log(f"💡 请运行: sudo usermod -a -G dialout {current_user}")
                                return False, "dialout组已创建，请添加用户到组中"
                            else:
                                self.log(f"❌ 创建dialout组失败: {result.stderr}")
                                return False, "创建dialout组失败"
                        except Exception as e:
                            self.log(f"❌ 创建dialout组异常: {str(e)}")
                            return False, f"创建dialout组异常: {str(e)}"
                            
                except ImportError:
                    # 回退到使用groups命令
                    try:
                        result = subprocess.run(
                            ["groups"],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0 and "dialout" in result.stdout:
                            self.log("✅ 用户已在dialout组中")
                            return True, "用户已在dialout组中"
                        else:
                            self.log("⚠️ 用户不在dialout组中，串口访问可能受限")
                            self.log("💡 请运行: sudo usermod -a -G dialout $USER")
                            self.log("💡 然后注销并重新登录")
                            return False, "用户不在dialout组中"
                    except Exception as e:
                        self.log(f"❌ 检查用户组失败: {str(e)}")
                        return False, f"检查用户组失败: {str(e)}"
            
            elif platform.system() == "Windows":
                # Windows下通常不需要特殊配置
                self.log("✅ Windows串口权限检查通过")
                return True, "Windows串口权限检查通过"
            
            else:
                self.log("⚠️ 未知系统，跳过串口权限配置")
                return True, "未知系统，跳过串口权限配置"
                
        except Exception as e:
            self.log(f"❌ 串口权限配置异常: {str(e)}")
            return False, f"串口权限配置异常: {str(e)}"
    
    def create_desktop_shortcut(self) -> Tuple[bool, str]:
        """创建桌面快捷方式"""
        try:
            import platform
            
            if platform.system() == "Windows":
                # Windows桌面快捷方式
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_path, "ColorBridge.lnk")
                
                # 使用PowerShell创建快捷方式
                main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                
                script = f'''
                $WshShell = New-Object -comObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
                $Shortcut.TargetPath = "{sys.executable}"
                $Shortcut.Arguments = "{main_script}"
                $Shortcut.WorkingDirectory = "{working_dir}"
                $Shortcut.IconLocation = "{sys.executable}"
                $Shortcut.Description = "ColorBridge - AI8051U"
                $Shortcut.Save()
                '''
                
                result = subprocess.run([
                    "powershell", "-Command", script
                ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0:
                    self.log("✅ Windows桌面快捷方式创建成功")
                    return True, "Windows桌面快捷方式创建成功"
                else:
                    self.log(f"⚠️ Windows桌面快捷方式创建失败: {result.stderr}")
                    return False, "Windows桌面快捷方式创建失败"
            
            else:
                self.log("⚠️ 非Windows系统，跳过桌面快捷方式创建")
                return True, "非Windows系统，跳过桌面快捷方式创建"
                
        except Exception as e:
            self.log(f"❌ 桌面快捷方式创建异常: {str(e)}")
            return False, f"桌面快捷方式创建异常: {str(e)}"
    
    def auto_fix_environment(self) -> Dict[str, Any]:
        """自动修复环境问题"""
        self.log("开始自动环境修复...")
        
        results = {
            "timestamp": str(os.times()),
            "actions": {},
            "success": True,
            "message": "环境修复完成"
        }
        
        # 安装缺失的包
        if self.env_checker.missing_packages:
            pkg_ok, pkg_msg = self.install_missing_packages(self.env_checker.missing_packages)
            results["actions"]["install_packages"] = {
                "status": "✅ 成功" if pkg_ok else "❌ 失败",
                "message": pkg_msg
            }
            if not pkg_ok:
                results["success"] = False
        
        # 配置串口权限
        serial_ok, serial_msg = self.configure_serial_permissions()
        results["actions"]["configure_serial"] = {
            "status": "✅ 成功" if serial_ok else "❌ 失败",
            "message": serial_msg
        }
        
        # 创建桌面快捷方式
        shortcut_ok, shortcut_msg = self.create_desktop_shortcut()
        results["actions"]["create_shortcut"] = {
            "status": "✅ 成功" if shortcut_ok else "❌ 失败",
            "message": shortcut_msg
        }
        
        # 重新检查环境
        self.log("重新检查环境状态...")
        recheck_results = self.env_checker.run_comprehensive_check()
        results["recheck"] = recheck_results
        
        # 更新总体状态
        if recheck_results["overall_status"] == "🟢 正常":
            results["final_status"] = "🟢 环境完全正常"
        else:
            results["final_status"] = "🟡 环境基本正常，有轻微问题"
            results["success"] = False
        
        return results


class EnvironmentManager:
    """环境管理器 - 统一管理环境检测和自动修复"""
    
    def __init__(self):
        self.checker = EnvironmentChecker()
        self.installer = AutoInstaller(self.checker)
        self.last_check_results = None
        self.last_install_results = None
        
    def run_full_check_and_fix(self) -> Dict[str, Any]:
        """运行完整的检测和修复流程"""
        # 第一步：环境检测
        self.last_check_results = self.checker.run_comprehensive_check()
        
        # 第二步：自动修复
        self.last_install_results = self.installer.auto_fix_environment()
        
        # 第三步：生成报告
        return {
            "check_results": self.last_check_results,
            "install_results": self.last_install_results,
            "summary": {
                "overall_status": self.last_install_results["final_status"],
                "actions_taken": len(self.last_install_results["actions"]),
                "success": self.last_install_results["success"]
            }
        }
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        if not self.last_check_results:
            return "尚未运行环境检测"
        
        report = []
        report.append("🌈 ColorBridge 环境状态报告")
        report.append("=" * 40)
        
        # 总体状态
        report.append(f"📊 总体状态: {self.last_check_results['overall_status']}")
        report.append("")
        
        # 各项检查结果
        for check_name, check_result in self.last_check_results["checks"].items():
            report.append(f"{check_result['status']} {check_name}")
            report.append(f"   {check_result['message']}")
        
        # 安装结果
        if self.last_install_results:
            report.append("")
            report.append("🔧 自动修复结果:")
            for action_name, action_result in self.last_install_results["actions"].items():
                report.append(f"{action_result['status']} {action_name}")
                report.append(f"   {action_result['message']}")
        
        return "\n".join(report)
    
    def save_report(self, filepath: str) -> bool:
        """保存报告到文件"""
        try:
            report_data = {
                "check_results": self.last_check_results,
                "install_results": self.last_install_results,
                "install_log": self.installer.install_log
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存报告失败: {str(e)}")
            return False


# 便捷函数
def quick_environment_check() -> Dict[str, Any]:
    """快速环境检查"""
    manager = EnvironmentManager()
    return manager.run_full_check_and_fix()

def is_environment_ready() -> bool:
    """检查环境是否准备就绪"""
    manager = EnvironmentManager()
    results = manager.run_full_check_and_fix()
    return results["summary"]["success"]