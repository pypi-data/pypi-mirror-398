# 核心模块包初始化文件 - ColorBridge v2.1.17

# 导入所有重命名的核心模块
from .colorbridge_serial_manager import ColorBridgeSerialManager
from .colorbridge_message_processor import ColorBridgeMessageProcessor
from .colorbridge_device_info_manager import ColorBridgeDeviceInfoManager
from .colorbridge_logger_manager import LoggerManager
from .colorbridge_monitoring_system import MonitoringSystem
from .colorbridge_error_recovery import ErrorRecoveryManager
from .colorbridge_log_analyzer import LogAnalyzer
from .colorbridge_log_protector import LogProtector
from .colorbridge_environment_manager import EnvironmentManager
from .colorbridge_debug_logger import get_debug_logger

__all__ = [
    'ColorBridgeSerialManager',
    'ColorBridgeMessageProcessor', 
    'ColorBridgeDeviceInfoManager',
    'LoggerManager',
    'MonitoringSystem',
    'ErrorRecoveryManager',
    'LogAnalyzer',
    'LogProtector',
    'EnvironmentManager',
    'get_debug_logger'
]

# 版本信息
__version__ = '2.1.17'
__author__ = 'ColorBridge开发团队'
__description__ = 'ColorBridge 核心模块包 v2.1.17 - Linux帮助对话框和版本统一更新，包含Linux帮助对话框、语法错误修复和版本号统一更新，确保跨平台兼容性和用户体验'