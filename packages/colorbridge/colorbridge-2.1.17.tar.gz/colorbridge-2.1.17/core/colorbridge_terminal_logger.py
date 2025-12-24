#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终端消息日志模块 - ColorBridge
专门记录终端显示的消息（发送和接收）
与运行日志和调试日志分离
"""

import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class TerminalLogger:
    """终端消息日志管理器"""
    
    def __init__(self, log_dir: str = None, enabled: bool = False):
        """
        初始化终端日志管理器
        
        Args:
            log_dir: 日志目录路径
            enabled: 是否启用日志记录
        """
        self.enabled = enabled
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs', 'terminal')
        self.current_log_file = None
        self.session_start_time = datetime.now()
        
        # 性能优化：消息缓冲区
        self._message_buffer = []
        self._buffer_size = 50  # 缓冲区大小
        self._buffer_flush_interval = 2.0  # 缓冲区刷新间隔（秒）
        self._last_flush_time = time.time()
        
        # 线程安全
        self._lock = threading.Lock()
        
        # 确保日志目录存在
        self.ensure_log_directory()
        
        # 如果启用，创建会话日志文件
        if self.enabled:
            self.create_session_log()
    
    def ensure_log_directory(self):
        """确保日志目录存在"""
        try:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[TERMINAL LOGGER ERROR] 无法创建日志目录: {e}")
            # 使用备用目录
            self.log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    def create_session_log(self):
        """创建当前会话的日志文件"""
        if not self.enabled:
            return
            
        try:
            timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"terminal_{timestamp}.log"
            self.current_log_file = os.path.join(self.log_dir, filename)
            
            # 写入文件头
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                f.write(f"# ColorBridge 终端消息日志\n")
                f.write(f"# 会话开始时间: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 日志格式: [时间戳] 方向 消息内容\n")
                f.write(f"# 方向: SEND=发送, RECV=接收\n")
                f.write(f"#\n")
                f.write(f"# 注意：此日志仅记录终端显示的消息，与调试日志分离\n")
                f.write(f"#\n")
            
            print(f"[TERMINAL LOGGER] 终端日志文件已创建: {self.current_log_file}")
            
        except Exception as e:
            print(f"[TERMINAL LOGGER ERROR] 创建日志文件失败: {e}")
            self.current_log_file = None
    
    def enable(self):
        """启用终端日志记录"""
        if self.enabled:
            return
            
        self.enabled = True
        self.create_session_log()
        print("[TERMINAL LOGGER] 终端日志记录已启用")
    
    def disable(self):
        """禁用终端日志记录"""
        if not self.enabled:
            return
            
        self.enabled = False
        print("[TERMINAL LOGGER] 终端日志记录已禁用")
    
    def log_message(self, direction: str, message: str, msg_type: str = None):
        """
        记录终端消息（带缓冲机制）
        
        Args:
            direction: 消息方向 ('send' 或 'receive')
            message: 消息内容
            msg_type: 消息类型（可选）
        """
        if not self.enabled or not self.current_log_file:
            return
            
        try:
            # 清理消息（移除HTML标签，但保持换行和格式）
            clean_message = self._clean_message(message)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 毫秒级
            
            # 确定方向标签（根据命令实际执行效果.txt格式）
            if direction.lower() == 'send':
                dir_prefix = '发送→'
            elif direction.lower() == 'receive':
                dir_prefix = '接收←'
            else:
                dir_prefix = f'{direction.upper()} '
            
            # 构建日志行（根据命令实际执行效果.txt格式）
            # 格式: [时间戳]发送→消息内容 或 [时间戳]接收←消息内容
            log_line = f"[{timestamp}]{dir_prefix}{clean_message}\n"
            
            # 性能优化：使用缓冲区减少文件I/O
            with self._lock:
                self._message_buffer.append(log_line)
                
                # 检查是否需要刷新缓冲区
                current_time = time.time()
                buffer_full = len(self._message_buffer) >= self._buffer_size
                time_elapsed = current_time - self._last_flush_time >= self._buffer_flush_interval
                
                if buffer_full or time_elapsed:
                    self._flush_buffer()
                    self._last_flush_time = current_time
                    
        except Exception as e:
            print(f"[TERMINAL LOGGER ERROR] 记录消息失败: {e}")
    
    def _flush_buffer(self):
        """刷新缓冲区到文件"""
        if not self._message_buffer:
            return
            
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.writelines(self._message_buffer)
            self._message_buffer.clear()
        except Exception as e:
            print(f"[TERMINAL LOGGER ERROR] 刷新缓冲区失败: {e}")
            # 保留缓冲区内容，下次尝试
    
    def _clean_message(self, message: str) -> str:
        """
        清理消息内容，移除HTML标签但保持原始格式
        
        Args:
            message: 原始消息
            
        Returns:
            清理后的消息（保持换行和缩进）
        """
        if not message:
            return ""
        
        # 移除HTML标签
        import re
        clean = re.sub(r'<[^>]+>', '', message)
        
        # 替换HTML实体（但保持换行符）
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('<br>', '\n')  # 将HTML换行标签转换为实际换行符
        
        # 不清理多余的空格和换行符，保持原始格式
        # 但需要移除消息开头和结尾的空白字符
        clean = clean.strip()
        
        # 限制长度（防止过长的消息），但保持最后一部分
        if len(clean) > 5000:
            # 保留前2000字符和后2000字符
            clean = clean[:2000] + "\n...[中间内容已截断]...\n" + clean[-2000:]
        
        return clean
    
    def log_send(self, message: str, msg_type: str = None):
        """记录发送的消息"""
        self.log_message('send', message, msg_type)
    
    def log_receive(self, message: str, msg_type: str = None):
        """记录接收的消息"""
        self.log_message('receive', message, msg_type)
    
    def get_log_file_path(self) -> Optional[str]:
        """获取当前日志文件路径"""
        return self.current_log_file
    
    def get_log_directory(self) -> str:
        """获取日志目录路径"""
        return self.log_dir
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            'enabled': self.enabled,
            'log_file': self.current_log_file,
            'log_dir': self.log_dir,
            'session_start': self.session_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'session_duration': str(datetime.now() - self.session_start_time),
            'buffer_size': len(self._message_buffer)
        }
    
    def flush(self):
        """强制刷新缓冲区到文件"""
        with self._lock:
            self._flush_buffer()


# 全局终端日志管理器实例
_terminal_logger_instance = None

def get_terminal_logger(log_dir: str = None, enabled: bool = False) -> TerminalLogger:
    """
    获取终端日志管理器实例（单例模式）
    
    Args:
        log_dir: 日志目录路径
        enabled: 是否启用日志记录
        
    Returns:
        TerminalLogger实例
    """
    global _terminal_logger_instance
    
    if _terminal_logger_instance is None:
        _terminal_logger_instance = TerminalLogger(log_dir, enabled)
    
    return _terminal_logger_instance

def log_terminal_send(message: str, msg_type: str = None):
    """记录发送的消息（便捷函数）"""
    logger = get_terminal_logger()
    if logger.is_enabled():
        logger.log_send(message, msg_type)

def log_terminal_receive(message: str, msg_type: str = None):
    """记录接收的消息（便捷函数）"""
    logger = get_terminal_logger()
    if logger.is_enabled():
        logger.log_receive(message, msg_type)