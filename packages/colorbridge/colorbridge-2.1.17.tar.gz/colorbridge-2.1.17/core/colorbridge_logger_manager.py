#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器模块 - ColorBridge
统一的日志创建、保存和管理功能
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class LoggerManager:
    """日志管理器 - 统一管理所有日志输出"""
    
    def __init__(self, log_dir: str = None, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs')
        self.ensure_log_directory()
        
        # 日志文件路径
        self.current_log_file = None
        self.session_start_time = datetime.now()
        
        # 线程安全
        self._lock = threading.Lock()
        
        # 性能监控阈值（避免误报）
        self.performance_thresholds = {
            'min_receive_rate': 1.0,      # 最小接收速率 1 bytes/s（降低阈值）
            'min_message_rate': 0.05,    # 最小消息速率 0.05 msg/s（降低阈值）
            'max_processing_latency': 1.0  # 最大处理延迟 1s（提高阈值）
        }
        
        # 创建当前会话日志文件
        self.create_session_log()
        
        # 重定向标准输出
        self.setup_log_redirection()
    
    def ensure_log_directory(self):
        """确保日志目录存在"""
        try:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] 无法创建日志目录: {e}")
            # 使用备用目录
            self.log_dir = os.path.join(os.getcwd(), 'logs')
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    def create_session_log(self):
        """创建当前会话的日志文件"""
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.log_dir, f"colorbridge_{timestamp}.log")
        
        # 创建文件时直接设置写权限（简化版本）
        try:
            # 创建空文件
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                pass  # 创建空文件
            
            # 只在Unix/Linux系统上设置文件权限
            if os.name != 'nt':  # 非Windows系统
                import stat
                current_mode = stat.S_IWUSR | stat.S_IRUSR | stat.S_IWGRP | stat.S_IRGRP
                os.chmod(self.current_log_file, current_mode)
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 创建日志文件失败: {e}")
            # 尝试使用备用文件名
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                self.current_log_file = os.path.join(temp_dir, f"colorbridge_{timestamp}.log")
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    pass
                if self.debug_mode:
                    print(f"[DEBUG] 使用备用日志文件: {self.current_log_file}")
            except Exception as e2:
                if self.debug_mode:
                    print(f"[DEBUG] 备用日志文件创建失败: {e2}")
                self.current_log_file = None
        
        # 写入会话开始信息
        session_info = f"""
========================================
ColorBridge 会话日志
========================================
会话开始时间: {self.session_start_time.strftime("%Y-%m-%d %H:%M:%S")}
日志文件: {self.current_log_file}
系统平台: {sys.platform}
Python版本: {sys.version}
工作目录: {os.getcwd()}
========================================

"""
        self.write_to_log_file(session_info)
        
        if self.debug_mode:
            print(f"[DEBUG] 日志文件已创建: {self.current_log_file}")
    
    def write_to_log_file(self, message: str):
        """写入日志文件（带重试机制）"""
        if not self.current_log_file:
            return
        
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with self._lock:
                    # 每次写入前确保文件可写
                    if attempt > 0:
                        self._ensure_file_writable()
                    
                    with open(self.current_log_file, 'a', encoding='utf-8') as f:
                        # 添加时间戳
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        formatted_message = f"[{timestamp}] {message}"
                        f.write(formatted_message + '\n')
                        f.flush()
                        return  # 成功写入，退出函数
                        
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # 权限错误，等待后重试
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    # 最后一次尝试失败
                    print(f"[ERROR] 写入日志文件权限错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                    # 尝试创建新的日志文件
                    self._create_emergency_log_file()
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"[ERROR] 写入日志文件失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    break
    
    def _create_emergency_log_file(self):
        """创建紧急日志文件（当原文件无法写入时）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_file = os.path.join(self.log_dir, f"colorbridge_emergency_{timestamp}.log")
            
            # 确保新文件可写
            self.current_log_file = emergency_file
            self._ensure_file_writable()
            
            # 通知日志保护器
            self._notify_current_log_file()
            
            print(f"[INFO] 已切换到紧急日志文件: {emergency_file}")
            
        except Exception as e:
            print(f"[ERROR] 创建紧急日志文件失败: {e}")

    
    def setup_log_redirection(self):
        """设置日志重定向"""
        try:
            import sys
            from io import StringIO
            
            class LogRedirector:
                def __init__(self, logger_manager, original_stream, stream_name):
                    self.logger_manager = logger_manager
                    self.original_stream = original_stream
                    self.stream_name = stream_name
                    self._buffer = []
                    self._last_flush = time.time()
                
                def write(self, text):
                    # 发送到原始流
                    self.original_stream.write(text)
                    self.original_stream.flush()
                    
                    # 添加到缓冲区
                    if text.strip():
                        self._buffer.append(text.strip())
                    
                    # 定期刷新到日志文件
                    current_time = time.time()
                    if current_time - self._last_flush > 1.0:  # 每秒刷新一次
                        self._flush_to_log()
                        self._last_flush = current_time
                
                def _flush_to_log(self):
                    """刷新缓冲区到日志文件"""
                    if self._buffer:
                        for line in self._buffer:
                            self.logger_manager.write_to_log_file(f"[{self.stream_name}] {line}")
                        self._buffer.clear()
                
                def flush(self):
                    """强制刷新"""
                    self._flush_to_log()
                    self.original_stream.flush()
            
            # 重定向stdout和stderr
            sys.stdout = LogRedirector(self, sys.stdout, "STDOUT")
            sys.stderr = LogRedirector(self, sys.stderr, "STDERR")
            
            if self.debug_mode:
                print("[DEBUG] 日志重定向已设置")
                
        except Exception as e:
            print(f"[ERROR] 日志重定向设置失败: {e}")
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """记录性能指标"""
        with self._lock:
            try:
                # 检查性能指标是否在合理范围内
                issues = []
                
                receive_rate = metrics.get('receive_rate', 0)
                message_rate = metrics.get('message_rate', 0)
                processing_latency = metrics.get('processing_latency', 0)
                
                # 检查接收速率（串口通信正常范围：5-10000 bytes/s）
                if receive_rate < self.performance_thresholds['min_receive_rate']:
                    issues.append(f"接收速率较低: {receive_rate:.2f} bytes/s (正常范围: >5 bytes/s)")
                elif receive_rate > 10000:
                    issues.append(f"接收速率异常高: {receive_rate:.2f} bytes/s")
                
                # 检查消息速率（正常范围：0.1-100 msg/s）
                if message_rate < self.performance_thresholds['min_message_rate']:
                    issues.append(f"消息速率较低: {message_rate:.2f} msg/s (正常范围: >0.1 msg/s)")
                elif message_rate > 100:
                    issues.append(f"消息速率异常高: {message_rate:.2f} msg/s")
                
                # 检查处理延迟（正常范围：<500ms）
                if processing_latency > self.performance_thresholds['max_processing_latency']:
                    issues.append(f"处理延迟较高: {processing_latency:.3f}s (正常范围: <0.5s)")
                
                # 记录性能指标
                perf_info = f"""
性能指标报告:
========================================
接收速率: {receive_rate:.2f} bytes/s
消息速率: {message_rate:.2f} msg/s
处理延迟: {processing_latency:.3f}s
缓冲区大小: {metrics.get('buffer_size', 0)} bytes
总消息数: {metrics.get('total_messages', 0)}
"""
                if issues:
                    perf_info += "性能警告:\n"
                    for issue in issues:
                        perf_info += f"  ⚠️ {issue}\n"
                else:
                    perf_info += "✅ 所有性能指标正常\n"
                
                perf_info += "========================================\n"
                
                self.write_to_log_file(perf_info)
                
            except Exception as e:
                self.write_to_log_file(f"[ERROR] 性能指标记录失败: {e}")
    
    def log_system_event(self, event_type: str, message: str, level: str = "INFO"):
        """记录系统事件"""
        event_info = f"[{level}] {event_type}: {message}"
        self.write_to_log_file(event_info)
        
        if self.debug_mode:
            print(f"[DEBUG] 系统事件已记录: {event_type}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """记录错误信息"""
        error_info = f"""
[ERROR] {error_type}
错误消息: {error_message}
"""
        if context:
            error_info += "上下文信息:\n"
            for key, value in context.items():
                error_info += f"  {key}: {value}\n"
        
        error_info += "========================================\n"
        
        self.write_to_log_file(error_info)
        
        if self.debug_mode:
            print(f"[DEBUG] 错误已记录: {error_type}")
    
    def get_log_files(self, limit: int = 10) -> list:
        """获取最近的日志文件列表"""
        try:
            log_files = []
            for file_path in Path(self.log_dir).glob("colorbridge_*.log"):
                stat = file_path.stat()
                log_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            
            # 按修改时间排序
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            return log_files[:limit]
            
        except Exception as e:
            self.write_to_log_file(f"[ERROR] 获取日志文件列表失败: {e}")
            return []
    
    def cleanup_old_logs(self, keep_days: int = 7):
        """清理旧日志文件（尊重保护机制）"""
        try:
            from .colorbridge_log_protector import get_log_protector
            protector = get_log_protector()
            
            cutoff_time = time.time() - (keep_days * 24 * 3600)
            cleaned_count = 0
            protected_count = 0
            
            for file_path in Path(self.log_dir).glob("colorbridge_*.log"):
                if file_path.stat().st_mtime < cutoff_time:
                    if protector.is_protected(str(file_path)):
                        protected_count += 1
                        continue
                    
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        self.write_to_log_file(f"[INFO] 删除旧日志: {file_path.name}")
                    except Exception as e:
                        self.write_to_log_file(f"[ERROR] 删除日志文件失败 {file_path}: {e}")
            
            self.write_to_log_file(f"[INFO] 清理完成: 删除 {cleaned_count} 个文件，保护 {protected_count} 个文件")
                
        except Exception as e:
            self.write_to_log_file(f"[ERROR] 清理旧日志文件失败: {e}")
    
    def close(self):
        """关闭日志管理器"""
        try:
            # 写入会话结束信息
            session_end_info = f"""
========================================
会话结束时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
会话持续时间: {datetime.now() - self.session_start_time}
日志文件: {self.current_log_file}
========================================
"""
            self.write_to_log_file(session_end_info)
            
            if self.debug_mode:
                print(f"[DEBUG] 日志会话已结束: {self.current_log_file}")
                
        except Exception as e:
            print(f"[ERROR] 关闭日志管理器失败: {e}")


# 全局日志管理器实例
_logger_manager = None

def get_logger_manager() -> LoggerManager:
    """获取全局日志管理器实例"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager(debug_mode=True)
    return _logger_manager

def init_logger_manager(log_dir: str = None, debug_mode: bool = False) -> LoggerManager:
    """初始化全局日志管理器"""
    global _logger_manager
    _logger_manager = LoggerManager(log_dir=log_dir, debug_mode=debug_mode)
    return _logger_manager