# UI模块初始化 - ColorBridge v2.1.17

# 核心UI组件
from .colorbridge_main_window import ColorBridgeMainWindow
from .colorbridge_settings_dialog import SettingsDialog

# UI组件
from .colorbridge_theme_manager import ThemeManager
from .colorbridge_notification_manager import EnhancedNotificationManager

__all__ = [
    # 核心组件
    'ColorBridgeMainWindow',
    'SettingsDialog',
    
    # UI组件
    'ThemeManager',
    'EnhancedNotificationManager'
]

# 版本信息
__version__ = '2.1.17'
__author__ = 'ColorBridge开发团队'
__description__ = 'ColorBridge UI模块 v2.1.17 - Linux帮助对话框和版本统一更新，包含PCL2风格主窗口、增强的通知管理器、主题管理器、设置对话框和Linux帮助对话框，支持跨平台兼容性、语法错误修复和版本号统一'