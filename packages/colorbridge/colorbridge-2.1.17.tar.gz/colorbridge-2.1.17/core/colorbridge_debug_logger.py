#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一调试日志系统 - ColorBridge
替换所有print调试语句，提供统一的日志管理
"""

import logging
import sys
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class DebugLogger:
    """统一调试日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not DebugLogger._initialized:
            self._setup_logger()
            DebugLogger._initialized = True
    
    def _setup_logger(self):
        """设置日志系统"""
        self.logger = logging.getLogger('ColorBridge')
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # 文件处理器
            try:
                from datetime import datetime
                import os
                from pathlib import Path
                
                # 确保logs目录存在
                log_dir = Path("logs")
                log_dir.mkdir(parents=True, exist_ok=True)
                
                log_filename = log_dir / f"colorbridge_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                file_handler = logging.FileHandler(str(log_filename), encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
            except Exception as e:
                print(f"[DEBUG] Debug日志文件创建失败: {e}")
                file_handler = None
            
            # 格式化器
            formatter = logging.Formatter(
                '[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            if file_handler:
                file_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
            if file_handler:
                self.logger.addHandler(file_handler)
    
    def debug(self, message: str, module: str = ""):
        """调试日志"""
        if module:
            message = f"[{module}] {message}"
        self.logger.debug(message)
    
    def info(self, message: str, module: str = ""):
        """信息日志"""
        if module:
            message = f"[{module}] {message}"
        self.logger.info(message)
    
    def warning(self, message: str, module: str = ""):
        """警告日志"""
        if module:
            message = f"[{module}] {message}"
        self.logger.warning(message)
    
    def error(self, message: str, module: str = ""):
        """错误日志"""
        if module:
            message = f"[{module}] {message}"
        self.logger.error(message)
    
    def critical(self, message: str, module: str = ""):
        """严重错误日志"""
        if module:
            message = f"[{module}] {message}"
        self.logger.critical(message)
    
    def set_level(self, level: LogLevel):
        """设置日志级别"""
        self.logger.setLevel(level.value)
        for handler in self.logger.handlers:
            handler.setLevel(level.value)


# 全局日志实例
debug_logger = DebugLogger()


def get_debug_logger() -> DebugLogger:
    """获取调试日志实例"""
    return debug_logger


# 便捷函数
def debug_log(message: str, module: str = ""):
    """调试日志便捷函数"""
    debug_logger.debug(message, module)


def info_log(message: str, module: str = ""):
    """信息日志便捷函数"""
    debug_logger.info(message, module)


def warning_log(message: str, module: str = ""):
    """警告日志便捷函数"""
    debug_logger.warning(message, module)


def error_log(message: str, module: str = ""):
    """错误日志便捷函数"""
    debug_logger.error(message, module)


def critical_log(message: str, module: str = ""):
    """严重错误日志便捷函数"""
    debug_logger.critical(message, module)