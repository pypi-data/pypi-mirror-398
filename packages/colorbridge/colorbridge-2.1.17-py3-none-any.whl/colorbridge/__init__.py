"""
ColorBridge - AI8051U串口助手
半透明多巴胺配色串口调试工具

包入口文件，定义包级别导出的内容
"""

__version__ = "2.1.17"
__author__ = "076lik"
__license__ = "GPLv3"
__description__ = "🌈 ColorBridge - AI8051U串口助手，半透明多巴胺配色串口调试工具"

# 导入核心模块以便直接使用
from core.colorbridge_logger_manager import LoggerManager
from core.colorbridge_serial_manager import ColorBridgeSerialManager
from ui.colorbridge_main_window import ColorBridgeMainWindow

__all__ = [
    "LoggerManager",
    "ColorBridgeSerialManager", 
    "ColorBridgeMainWindow",
    "__version__",
    "__author__",
    "__license__",
    "__description__",
]