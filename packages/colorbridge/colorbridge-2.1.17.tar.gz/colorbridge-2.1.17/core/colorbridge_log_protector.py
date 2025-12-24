#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志保护器模块 - ColorBridge
保护重要日志文件不被误删
"""

import os
import time
import stat
from pathlib import Path
from typing import List, Dict, Any


class LogProtector:
    """日志保护器 - 防止重要日志文件被误删"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs')
        self.protected_files = set()
        
        # 受保护的文件模式
        self.protected_patterns = [
            'colorbridge_*.log',      # 主日志文件
            'error_*.log',            # 错误日志
            'performance_*.log',      # 性能日志
            'session_*.log',          # 会话日志
            'crash_*.log',            # 崩溃日志
            'debug_*.log'             # 调试日志
        ]
        
        # 保护最近7天的日志
        self.protection_days = 7
        
        # 初始化保护
        self.setup_protection()
    
    def setup_protection(self):
        """设置文件保护"""
        try:
            # 确保日志目录存在
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
            
            # 查找需要保护的文件
            self.find_protected_files()
            
            # 设置文件属性（在Windows上设置为只读）
            self.set_file_protection()
            
            print(f"[INFO] 日志保护已启用，保护 {len(self.protected_files)} 个文件")
            
        except Exception as e:
            print(f"[ERROR] 日志保护设置失败: {e}")
    
    def find_protected_files(self):
        """查找需要保护的文件"""
        self.protected_files.clear()
        
        try:
            # 获取当前正在使用的日志文件（避免保护当前文件）
            current_log_file = self._get_current_log_file()
            
            for pattern in self.protected_patterns:
                for file_path in Path(self.log_dir).glob(pattern):
                    # 跳过当前正在使用的日志文件
                    if str(file_path) == current_log_file:
                        continue
                    
                    # 检查文件是否在保护期内且不是最近修改的（避免保护活跃文件）
                    if self.is_within_protection_period(file_path) and self._is_inactive_file(file_path):
                        self.protected_files.add(str(file_path))
            
            # 也保护当前运行日志（只读状态）
            current_log = os.path.join(self.log_dir, '运行日志.txt')
            if os.path.exists(current_log):
                self.protected_files.add(current_log)
                
        except Exception as e:
            print(f"[ERROR] 查找保护文件失败: {e}")
    
    def _get_current_log_file(self) -> str:
        """获取当前正在使用的日志文件路径（避免循环依赖）"""
        # 避免循环依赖，不直接调用logger_manager
        # 使用时间戳推断当前日志文件
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y%m%d")
            
            # 查找今天最新的日志文件作为当前文件
            latest_file = ""
            latest_time = 0
            
            for file_path in Path(self.log_dir).glob(f"colorbridge_{current_time}_*.log"):
                try:
                    file_time = file_path.stat().st_mtime
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = str(file_path)
                except Exception:
                    continue
            
            return latest_file
        except Exception:
            return ""
    
    def _is_inactive_file(self, file_path: Path) -> bool:
        """检查文件是否为非活跃文件（超过10分钟未修改）"""
        try:
            file_stat = file_path.stat()
            file_time = file_stat.st_mtime
            current_time = time.time()
            
            # 超过10分钟未修改的文件被认为是非活跃的
            inactive_cutoff = current_time - (10 * 60)  # 10分钟
            return file_time < inactive_cutoff
            
        except Exception:
            return True  # 如果无法确定，默认为非活跃
    
    def is_within_protection_period(self, file_path: Path) -> bool:
        """检查文件是否在保护期内"""
        try:
            file_stat = file_path.stat()
            file_time = file_stat.st_mtime
            current_time = time.time()
            
            # 保护期内的文件
            protection_cutoff = current_time - (self.protection_days * 24 * 3600)
            return file_time >= protection_cutoff
            
        except Exception:
            return False
    
    def set_file_protection(self):
        """设置文件保护属性"""
        try:
            for file_path in self.protected_files:
                if os.path.exists(file_path):
                    # Windows: 设置为只读
                    if os.name == 'nt':
                        # 使用基础的读写权限保护，不依赖win32api
                        try:
                            # 移除写权限，设置为只读
                            current_mode = os.stat(file_path).st_mode
                            # 保留读取权限，移除写权限
                            new_mode = current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
                            os.chmod(file_path, new_mode)
                        except Exception as e:
                            print(f"[ERROR] 设置文件权限失败: {e}")
                    else:
                        # Unix/Linux: 移除写权限
                        current_mode = os.stat(file_path).st_mode
                        os.chmod(file_path, current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
                        
        except Exception as e:
            print(f"[ERROR] 设置文件保护失败: {e}")
    
    def remove_protection(self, file_path: str = None):
        """移除文件保护"""
        try:
            if file_path:
                files_to_unprotect = [file_path]
            else:
                files_to_unprotect = list(self.protected_files)
            
            for file_path in files_to_unprotect:
                if os.path.exists(file_path):
                    # Windows: 移除只读属性
                    if os.name == 'nt':
                        # 使用基础的读写权限恢复，不依赖win32api
                        try:
                            # 恢复写权限
                            current_mode = os.stat(file_path).st_mode
                            # 恢复读写权限
                            new_mode = current_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
                            os.chmod(file_path, new_mode)
                        except Exception as e:
                            print(f"[ERROR] 恢复文件权限失败: {e}")
            
            if file_path in self.protected_files:
                self.protected_files.remove(file_path)
                
        except Exception as e:
            print(f"[ERROR] 移除文件保护失败: {e}")
    
    def is_protected(self, file_path: str) -> bool:
        """检查文件是否受保护"""
        return file_path in self.protected_files
    
    def cleanup_old_logs(self, force: bool = False):
        """清理旧日志文件"""
        try:
            cutoff_time = time.time() - (self.protection_days * 24 * 3600)
            cleaned_count = 0
            protected_count = 0
            
            for file_path in Path(self.log_dir).glob("*.log"):
                if file_path.stat().st_mtime < cutoff_time:
                    if str(file_path) in self.protected_files and not force:
                        protected_count += 1
                        continue
                    
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        print(f"[ERROR] 删除日志文件失败 {file_path}: {e}")
            
            print(f"[INFO] 清理完成: 删除 {cleaned_count} 个文件，保护 {protected_count} 个文件")
            return cleaned_count
            
        except Exception as e:
            print(f"[ERROR] 清理旧日志失败: {e}")
            return 0
    
    def get_protection_status(self) -> Dict[str, Any]:
        """获取保护状态"""
        try:
            total_size = 0
            file_details = []
            
            for file_path in self.protected_files:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    total_size += stat.st_size
                    file_details.append({
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
            
            return {
                'protected_count': len(self.protected_files),
                'total_size': total_size,
                'protection_days': self.protection_days,
                'files': file_details
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def add_protection(self, file_path: str):
        """添加文件保护"""
        if os.path.exists(file_path):
            self.protected_files.add(file_path)
            self.set_file_protection()


# 全局日志保护器实例
_log_protector = None

def get_log_protector() -> LogProtector:
    """获取全局日志保护器实例"""
    global _log_protector
    if _log_protector is None:
        _log_protector = LogProtector()
    return _log_protector

def init_log_protector(log_dir: str = None) -> LogProtector:
    """初始化全局日志保护器"""
    global _log_protector
    _log_protector = LogProtector(log_dir=log_dir)
    return _log_protector