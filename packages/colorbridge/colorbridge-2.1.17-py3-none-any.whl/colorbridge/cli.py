#!/usr/bin/env python
"""
ColorBridge命令行入口点
"""

import sys
import os

# 确保可以导入同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    """主函数 - 启动ColorBridge"""
    # 解析命令行参数
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    quiet_mode = "--quiet" in sys.argv or "-q" in sys.argv
    version_mode = "--version" in sys.argv or "-v" in sys.argv
    help_mode = "--help" in sys.argv or "-h" in sys.argv
    
    # 显示版本信息
    if version_mode:
        print("ColorBridge v2.1.17 - AI8051U串口助手")
        print("作者: 076lik")
        print("许可证: GPLv3")
        return 0    # 显示帮助信息
    if help_mode:
        print("ColorBridge - AI8051U串口助手")
        print("")
        print("用法: colorbridge [选项]")
        print("")
        print("选项:")
        print("  -d, --debug    启用调试模式，显示详细调试信息")
        print("  -q, --quiet    静默模式，只显示错误信息")
        print("  -v, --version  显示版本信息")
        print("  -h, --help     显示此帮助信息")
        print("")
        print("示例:")
        print("  colorbridge              # 正常启动")
        print("  colorbridge --debug      # 调试模式启动")
        print("  colorbridge --quiet      # 静默模式启动")
        return 0
    
    # 创建 QApplication 实例
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    
    app = QApplication(sys.argv)
    app.setApplicationName("ColorBridge")
    app.setApplicationVersion("2.1.17")
    app.setOrganizationName("076lik")    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 显示启动模式
    if debug_mode:
        print("🐛 ColorBridge 调试模式启动")
    elif quiet_mode:
        print("🤫 ColorBridge 静默模式启动")
    else:
        print("🌈 ColorBridge 正常模式启动")
    
    # 确保logs目录存在
    from pathlib import Path
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化日志管理器、保护器和监控系统
    logger_manager = None
    log_protector = None
    monitoring_system = None
    log_analyzer = None
    
    try:
        # 初始化日志管理器（先初始化，这样保护器就知道当前日志文件）
        try:
            from core.colorbridge_logger_manager import init_logger_manager
            logger_manager = init_logger_manager(debug_mode=debug_mode)
            logger_manager.log_system_event("SYSTEM", "ColorBridge 启动中...")
        except ImportError as e:
            print(f"❌ 无法导入日志管理器: {e}")
            return 1
        
        # 初始化日志保护器（在日志管理器之后初始化，避免保护当前文件）
        try:
            from core.colorbridge_log_protector import init_log_protector
            log_protector = init_log_protector()
            if logger_manager:
                logger_manager.log_system_event("SYSTEM", "日志保护已启用")
        except ImportError as e:
            print(f"⚠️ 无法导入日志保护器: {e}")
        
        # 初始化监控系统
        try:
            from core.colorbridge_monitoring_system import MonitoringSystem
            monitoring_system = MonitoringSystem()
            monitoring_system.start_monitoring()
            if logger_manager:
                logger_manager.log_system_event("SYSTEM", "监控系统已启动")
        except ImportError as e:
            print(f"⚠️ 无法导入监控系统: {e}")
        
        # 初始化日志分析器
        try:
            from core.colorbridge_log_analyzer import LogAnalyzer
            log_analyzer = LogAnalyzer()
            if logger_manager:
                logger_manager.log_system_event("SYSTEM", "日志分析器已初始化")
        except ImportError as e:
            print(f"⚠️ 无法导入日志分析器: {e}")
        
        # 导入主窗口并启动应用程序
        try:
            from ui.colorbridge_main_window import ColorBridgeMainWindow
            main_window = ColorBridgeMainWindow(
                monitoring_system=monitoring_system,
                log_analyzer=log_analyzer,
                debug_mode=debug_mode
            )
            main_window.show()
            
            # 启动应用程序事件循环
            exit_code = app.exec()
            
            # 清理资源
            if monitoring_system:
                monitoring_system.stop_monitoring()
            
            if logger_manager:
                logger_manager.log_system_event("SYSTEM", "ColorBridge 正常退出")
            
            return exit_code
            
        except ImportError as e:
            if logger_manager:
                logger_manager.log_error("IMPORT", f"无法导入主窗口: {e}")
            print(f"❌ 无法导入主窗口: {e}")
            return 1
            
    except Exception as e:
        print(f"❌ ColorBridge 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())