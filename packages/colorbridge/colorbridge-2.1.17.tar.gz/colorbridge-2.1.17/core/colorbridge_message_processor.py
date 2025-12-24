#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理核心模块 - ColorBridge (清理版本)
解决消息重复、分段不完整、边界识别、无限递归、消息风暴等问题
集成错误恢复和智能监控机制
"""

import time
import re
import threading
import hashlib
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from .colorbridge_error_recovery import ErrorRecoveryManager, ErrorEvent, ErrorCategory, ErrorSeverity


class MessageType(Enum):
    """消息类型枚举"""
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class MessagePacket:
    """消息数据包"""
    content: str
    timestamp: float
    message_type: MessageType
    sequence_id: Optional[int] = None
    is_complete: bool = False
    command_context: Optional[str] = None


class CommandDeduplicator:
    """命令去重器 - 解决消息重复显示问题"""
    
    # 预编译正则表达式提升性能
    _timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}')
    _time_pattern = re.compile(r'时间:\s*\d+\s*周期')
    _hex_pattern = re.compile(r'0x[0-9a-fA-F]+')
    _compile_pattern = re.compile(r'编译:\s*\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2}:\d{2}')
    _current_time_pattern = re.compile(r'当前时间:\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}')
    _whitespace_pattern = re.compile(r'\s+')
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.recent_commands: Dict[str, float] = {}
        self.recent_responses: Dict[str, float] = {}
        self.recent_device_info: Dict[str, float] = {}  # 新增设备信息去重
        self.dedup_window = 0.5  # 0.5秒去重窗口，更快过滤重复消息
        self.device_info_window = 3.0  # 设备信息更长的去重窗口
        
    def is_duplicate_command(self, command: str) -> bool:
        """检查是否为重复命令"""
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_commands(current_time)
        
        # 检查重复
        if command in self.recent_commands:
            if current_time - self.recent_commands[command] < self.dedup_window:
                if self.debug_mode:
                    print(f"[DEBUG] 过滤重复命令: {command}")
                return True
        
        return False
    
    def is_duplicate_response(self, response: str) -> bool:
        """检查是否为重复响应（优化版 - 改进去重逻辑）"""
        current_time = time.time()
        
        # 专门处理设备信息去重
        if self.is_duplicate_device_info(response):
            return True
        
        # 清理过期记录
        self._cleanup_expired_responses(current_time)
        
        # 生成响应指纹（忽略时间戳等变化内容）
        response_fingerprint = self._generate_response_fingerprint(response)
        
        # 检查是否为设备信息更新消息 - 这些消息允许更频繁
        device_info_patterns = [
            '设备信息已更新',
            'MCU:', '时钟:', 'Flash:', 'XRAM已用:', '内部RAM:'
        ]
        
        is_device_info = any(pattern in response for pattern in device_info_patterns)
        
        # 设备信息消息使用更长的去重窗口
        dedup_window = 2.0 if is_device_info else 0.5
        
        if response_fingerprint in self.recent_responses:
            time_diff = current_time - self.recent_responses[response_fingerprint]
            if time_diff < dedup_window:
                if self.debug_mode:
                    print(f"[DEBUG] 过滤重复响应: {response_fingerprint[:50]}... (间隔: {time_diff:.2f}s)")
                return True
        
        return False
    
    def record_command(self, command: str):
        """记录命令"""
        current_time = time.time()
        self.recent_commands[command] = current_time
    
    def record_response(self, response: str):
        """记录响应"""
        current_time = time.time()
        fingerprint = self._generate_response_fingerprint(response)
        self.recent_responses[fingerprint] = current_time
    
    def _generate_response_fingerprint(self, response: str) -> str:
        """生成响应指纹，忽略时间戳等变化内容（使用预编译正则表达式）"""
        # 移除时间戳信息
        cleaned = self._timestamp_pattern.sub('', response)
        # 移除执行时间等变化内容
        cleaned = self._time_pattern.sub('时间: X周期', cleaned)
        # 移除内存地址等变化内容
        cleaned = self._hex_pattern.sub('0xXXXX', cleaned)
        # 移除编译时间等变化内容
        cleaned = self._compile_pattern.sub('编译: XXXX', cleaned)
        # 移除当前时间等变化内容
        cleaned = self._current_time_pattern.sub('当前时间: XXXX', cleaned)
        # 标准化空白字符
        cleaned = self._whitespace_pattern.sub(' ', cleaned)
        
        return cleaned.strip()
    
    def _cleanup_expired_commands(self, current_time: float):
        """清理过期的命令记录"""
        expired = [cmd for cmd, timestamp in self.recent_commands.items() 
                  if current_time - timestamp > self.dedup_window]
        for cmd in expired:
            del self.recent_commands[cmd]
    
    def _cleanup_expired_responses(self, current_time: float):
        """清理过期的响应记录"""
        expired = [resp for resp, timestamp in self.recent_responses.items() 
                  if current_time - timestamp > self.dedup_window]
        for resp in expired:
            del self.recent_responses[resp]
    
    def is_duplicate_device_info(self, response: str) -> bool:
        """专门处理设备信息去重"""
        device_info_patterns = [
            '设备信息已更新', 'MCU:', '时钟:', 'Flash:', 'XRAM已用:', '内部RAM:'
        ]
        
        is_device_info = any(pattern in response for pattern in device_info_patterns)
        if not is_device_info:
            return False
            
        # 生成内容指纹
        content_fingerprint = self._generate_device_info_fingerprint(response)
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_device_info(current_time)
        
        # 检查重复
        if content_fingerprint in self.recent_device_info:
            if current_time - self.recent_device_info[content_fingerprint] < self.device_info_window:
                if self.debug_mode:
                    print(f"[DEBUG] 过滤重复设备信息: {content_fingerprint[:30]}...")
                return True
        
        self.recent_device_info[content_fingerprint] = current_time
        return False
        
    def _generate_device_info_fingerprint(self, response: str) -> str:
        """生成设备信息指纹，忽略时间戳变化"""
        # 移除时间戳相关内容
        cleaned = self._timestamp_pattern.sub('[TIME]', response)
        cleaned = self._current_time_pattern.sub('', cleaned)
        # 移除空白字符
        cleaned = self._whitespace_pattern.sub(' ', cleaned).strip()
        try:
            # 检查hashlib是否可用
            import hashlib
            return hashlib.md5(cleaned.encode()).hexdigest()[:8]
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] hashlib不可用，使用备用哈希: {e}")
            # 备用哈希方案
            import time
            import hashlib
            return f"{hashlib.md5(f'{cleaned}_{int(time.time())}'.encode()).hexdigest()[:8]}"
        
    def _cleanup_expired_device_info(self, current_time: float):
        """清理过期的设备信息记录"""
        expired_keys = [
            key for key, timestamp in self.recent_device_info.items()
            if current_time - timestamp > self.device_info_window * 2
        ]
        for key in expired_keys:
            del self.recent_device_info[key]


class PacketReassembler:
    """数据包重组器 - 解决数据分段不完整问题（支持动态缓冲区管理）"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.partial_packets: Dict[str, List[str]] = {}
        self.packet_timeouts: Dict[str, float] = {}  # 记录超时时间
        self.packet_timeout = 5.0  # 增加到5秒超时，支持长测试输出
        
        # 优化的动态缓冲区管理 - 改进版本
        self.min_packet_size = 10240   # 10KB最小缓冲区，提高处理效率
        self.max_packet_size = 51200  # 50KB最大缓冲区，减少内存占用
        self.current_packet_size = 20480  # 当前缓冲区大小，默认20KB
        self.max_fragments = 30  # 进一步减少到30个片段，提高处理效率
        
        # 优化的动态调整参数 - 更智能的调整策略
        self.usage_history = deque(maxlen=3)  # 减少历史记录数量，更快响应
        self.adjustment_threshold = 0.8  # 80%使用率触发调整，减少频繁调整
        self.last_adjustment_time = 0
        self.adjustment_interval = 10  # 减少到10秒调整间隔，更及时优化
        
    def add_fragment(self, data: str, context_id: str = "default") -> Optional[str]:
        """添加数据片段，尝试重组完整消息"""
        import time
        
        # 检查是否是完整消息
        if self._is_complete_message(data):
            if self.debug_mode:
                print(f"[DEBUG] 检测到完整消息: {data[:50]}...")
            return data
        
        # 添加到部分消息缓冲区
        if context_id not in self.partial_packets:
            self.partial_packets[context_id] = []
            self.packet_timeouts[context_id] = time.time()
        
        self.partial_packets[context_id].append(data)
        
        # 检查是否可以重组
        reassembled = self._try_reassemble(context_id)
        if reassembled:
            if self.debug_mode:
                print(f"[DEBUG] 重组完成消息: {reassembled[:50]}...")
            self.partial_packets[context_id] = []  # 清空缓冲区
            if context_id in self.packet_timeouts:
                del self.packet_timeouts[context_id]
            return reassembled
        
        # 检查超时和片段数限制
        self._check_timeout(context_id)
        
        return None
    
    def _is_complete_message(self, data: str) -> bool:
        """检查是否为完整消息"""
        # 检查命令提示符
        if data.startswith('> '):
            return True
        
        # 检查系统消息结束标志
        complete_indicators = [
            '测试完成！',
            '性能基准测试完成',
            '所有计算均为实时执行',
            'clockinfo完成'
        ]
        
        for indicator in complete_indicators:
            if indicator in data:
                return True
        
        # 检查分隔线结束标志
        if data.strip().endswith('========================================'):
            return True
        
        # 检查是否包含完整的命令帮助信息
        if ('可用命令:' in data and 
            'help - 显示帮助信息' in data and 
            'neofetch' in data):  # 确保包含最后一个命令
            return True
        
        # 检查是否包含完整的系统信息
        if ('系统信息:' in data and 
            '微控制器:' in data and 
            'Flash大小:' in data and 
            'XRAM大小:' in data and
            '内部RAM:' in data):  # 确保包含完整信息
            return True
        
        return False
    
    def _try_reassemble(self, context_id: str) -> Optional[str]:
        """尝试重组消息（使用动态缓冲区）"""
        if context_id not in self.partial_packets:
            return None
        
        fragments = self.partial_packets[context_id]
        if not fragments:
            return None
        
        # 合并所有片段
        combined = ''.join(fragments)
        combined_size = len(combined)
        
        # 计算当前使用率并调整缓冲区大小
        usage_rate = combined_size / self.current_packet_size
        self._adjust_buffer_size(usage_rate)
        
        # 检查大小限制（使用动态大小）
        if combined_size > self.current_packet_size:
            if self.debug_mode:
                print(f"[DEBUG] 消息过大，截断处理: {combined_size} -> {self.current_packet_size}")
            combined = combined[-self.current_packet_size:]
        
        # 检查是否形成完整消息
        if self._is_complete_message(combined):
            return combined
        
        return None
    
    def _adjust_buffer_size(self, current_usage: float):
        """优化的动态调整缓冲区大小"""
        current_time = time.time()
        
        # 检查调整间隔
        if current_time - self.last_adjustment_time < self.adjustment_interval:
            return
        
        # 记录使用率历史
        self.usage_history.append(current_usage)
        
        # 计算平均使用率
        if len(self.usage_history) >= 3:
            avg_usage = sum(self.usage_history) / len(self.usage_history)
            
            old_size = self.current_packet_size
            
            # 更激进的扩容策略：使用率超过70%
            if avg_usage > self.adjustment_threshold and self.current_packet_size < self.max_packet_size:
                self.current_packet_size = min(int(self.current_packet_size * 1.3), self.max_packet_size)
                self.last_adjustment_time = current_time
                
                if self.debug_mode:
                    print(f"[DEBUG] 缓冲区扩容: {old_size/1024:.1f}KB -> {self.current_packet_size/1024:.1f}KB (使用率: {avg_usage:.1%})")
            
            # 更积极的缩容策略：使用率低于40%
            elif avg_usage < 0.4 and self.current_packet_size > self.min_packet_size:
                self.current_packet_size = max(int(self.current_packet_size * 0.7), self.min_packet_size)
                self.last_adjustment_time = current_time
                
                if self.debug_mode:
                    print(f"[DEBUG] 缓冲区缩容: {old_size/1024:.1f}KB -> {self.current_packet_size/1024:.1f}KB (使用率: {avg_usage:.1%})")
    
    def _check_timeout(self, context_id: str):
        """检查超时并清理"""
        import time
        
        if context_id not in self.partial_packets:
            return
        
        current_time = time.time()
        fragment_count = len(self.partial_packets[context_id])
        
        # 检查时间超时
        if context_id in self.packet_timeouts:
            if current_time - self.packet_timeouts[context_id] > self.packet_timeout:
                if self.debug_mode:
                    print(f"[DEBUG] 清理超时的部分消息: {context_id}")
                del self.partial_packets[context_id]
                del self.packet_timeouts[context_id]
                return
        
        # 检查片段数超限
        if fragment_count > self.max_fragments:
            if self.debug_mode:
                print(f"[DEBUG] 清理片段过多的部分消息: {context_id} ({fragment_count} 片段)")
            del self.partial_packets[context_id]
            if context_id in self.packet_timeouts:
                del self.packet_timeouts[context_id]


class CommandResponseTracker:
    """命令响应跟踪器 - 解决消息边界识别问题"""
    
    # 预编译正则表达式提升性能
    _command_patterns = {
        'help': re.compile(r'^help\s*$', re.IGNORECASE),
        'info': re.compile(r'^info\s*$', re.IGNORECASE),
        'clear': re.compile(r'^clear\s*$', re.IGNORECASE),
        'reset': re.compile(r'^reset\s*$', re.IGNORECASE),
        'settime': re.compile(r'^settime\s+', re.IGNORECASE),
        'setdate': re.compile(r'^setdate\s+', re.IGNORECASE),
        'voltage': re.compile(r'^voltage\s*$', re.IGNORECASE),
        'neofetch': re.compile(r'^neofetch\s*$', re.IGNORECASE),
        'hwtest': re.compile(r'^hwtest\s*$', re.IGNORECASE),
        'mdu32': re.compile(r'^mdu32\s*$', re.IGNORECASE),
        'tfpu': re.compile(r'^tfpu\s*$', re.IGNORECASE),
        'benchmark': re.compile(r'^benchmark\s*$', re.IGNORECASE),
        'clockinfo': re.compile(r'^clockinfo\s*$', re.IGNORECASE)
    }
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.active_commands: Dict[str, float] = {}
        self.response_end_patterns = {
            'help': [r'neofetch\s+-\s+显示系统信息\(ASCII艺术\)', r'>\s*$'],
            'info': [r'内部RAM:\s+\d+\s+字节', r'>\s*$'],
            'hwtest': [r'硬件加速测试完成！', r'>\s*$'],
            'mdu32': [r'MDU32测试完成！', r'>\s*$'],
            'tfpu': [r'TFPU测试完成！', r'>\s*$'],
            'benchmark': [r'性能基准测试完成！', r'>\s*$'],
            'clockinfo': [r'时钟信息显示完成！', r'>\s*$']
        }
        
    def identify_command(self, message: str) -> Optional[str]:
        """识别命令类型（使用预编译正则表达式）"""
        message = message.strip()
        
        # 检查命令提示符
        if message.startswith('> '):
            command = message[2:].strip()
            
            for cmd_name, pattern in self._command_patterns.items():
                if pattern.match(command):
                    return cmd_name
        
        return None
    
    def is_response_start(self, message: str, command: Optional[str] = None) -> bool:
        """检查是否为响应开始"""
        if not command:
            return False
        
        # 特定命令的响应开始模式
        start_patterns = {
            'help': [r'^可用命令:', r'^help\s*$'],
            'info': [r'^系统信息:', r'^info\s*$'],
            'hwtest': [r'^========================================', r'^AI8051U\s+硬件加速单元测试'],
            'mdu32': [r'^========================================', r'^MDU32\s+硬件乘除单元详细测试'],
            'tfpu': [r'^========================================', r'^TFPU\s+浮点运算单元详细测试'],
            'benchmark': [r'^========================================', r'^AI8051U\s+硬件加速性能基准测试'],
            'clockinfo': [r'^========================================', r'^AI8051U氢原子系统']
        }
        
        if command in start_patterns:
            for pattern in start_patterns[command]:
                if re.search(pattern, message, re.IGNORECASE | re.MULTILINE):
                    return True
        
        return False
    
    def is_response_end(self, message: str, command: Optional[str] = None) -> bool:
        """检查是否为响应结束"""
        if not command:
            return False
        
        if command in self.response_end_patterns:
            for pattern in self.response_end_patterns[command]:
                if re.search(pattern, message, re.IGNORECASE | re.MULTILINE):
                    return True
        
        return False
    
    def start_command_tracking(self, command: str):
        """开始命令跟踪"""
        current_time = time.time()
        self.active_commands[command] = current_time
        
        if self.debug_mode:
            print(f"[DEBUG] 开始跟踪命令: {command}")
    
    def end_command_tracking(self, command: str):
        """结束命令跟踪"""
        if command in self.active_commands:
            del self.active_commands[command]
            
            if self.debug_mode:
                print(f"[DEBUG] 结束跟踪命令: {command}")
    
    def get_active_commands(self) -> List[str]:
        """获取活跃命令列表"""
        return list(self.active_commands.keys())


class ColorBridgeMessageProcessor(QObject):
    """消息处理器主类 (清理版本)"""
    
    message_processed = pyqtSignal(str, str)  # message, message_type
    command_detected = pyqtSignal(str)  # command
    error_occurred = pyqtSignal(str)  # error_message
    storm_detected = pyqtSignal(bool)  # is_storm_active
    
    def __init__(self, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        
        # 初始化各个组件
        self.deduplicator = CommandDeduplicator(debug_mode)
        self.reassembler = PacketReassembler(debug_mode)
        self.tracker = CommandResponseTracker(debug_mode)
        
        # 错误恢复管理器
        self.error_recovery = ErrorRecoveryManager(debug_mode)
        self.error_recovery.recovery_completed.connect(self._on_recovery_completed)
        self.error_recovery.recovery_failed.connect(self._on_recovery_failed)
        
        # 当前命令上下文
        self.current_command: Optional[str] = None
        self.response_buffer: List[str] = []
        
        # 稳定性增强功能
        self.processing_lock = threading.RLock()
        self.message_queue = deque(maxlen=5000)  # 减少队列大小，防止内存占用过高
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self._process_message_queue)
        self.processing_timer.start(50)  # 延长到50ms处理间隔，减少CPU占用
        
        # 自适应消息风暴防护
        self.message_timestamps = deque(maxlen=1000)  # 增加容量
        self.base_storm_threshold = 100  # 基础风暴阈值
        self.storm_threshold = self.base_storm_threshold  # 当前动态阈值
        self.storm_active = False
        self.storm_start_time = None
        
        # 自适应调整参数
        self.storm_history = deque(maxlen=10)  # 风暴历史记录
        self.threshold_adjustment_factor = 1.2  # 阈值调整因子
        self.min_threshold = 50  # 最小阈值
        self.max_threshold = 500  # 最大阈值
        self.last_threshold_adjustment = 0
        self.threshold_adjustment_interval = 60  # 60秒调整间隔
        
        # 递归深度保护（增加限制）
        self.recursion_depth = 0
        self.max_recursion_depth = 20  # 增加到20，支持更复杂的处理
        
        # 性能监控
        self.processing_stats = {
            'total_processed': 0,
            'total_errors': 0,
            'average_processing_time': 0.0,
            'storm_events': 0
        }
        self.processing_times = deque(maxlen=100)
        
        # 健康检查定时器
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._health_check)
        self.health_check_timer.start(30000)  # 延长到30秒健康检查，进一步减少CPU占用
        
    def _is_test_mode_active(self) -> bool:
        """高效智能检测是否为测试模式 - 增强版"""
        test_commands = ['mdu32', 'tfpu', 'hwtest', 'benchmark', 'clockinfo', 'voltage']
        test_indicators = [
            '硬件加速单元测试',
            '硬件乘除单元详细测试', 
            '浮点运算单元详细测试',
            '性能基准测试',
            '硬件加速测试完成',
            'MDU32测试完成',
            'TFPU测试完成',
            '电源电压测量',
            'ADC原始值',
            '测量通道',
            '时钟系统详细信息',
            '时钟信息显示完成'
        ]
        
        # 只检查最近的消息，避免全队列转换
        recent_count = min(10, len(self.message_queue))
        for i in range(recent_count):
            if self.message_queue[i]:
                message = self.message_queue[i]
                
                # 检查测试命令
                for cmd in test_commands:
                    if cmd in message:
                        if self.debug_mode:
                            print(f"[DEBUG] 检测到测试命令: {cmd}")
                        return True
                
                # 检查测试输出特征
                for indicator in test_indicators:
                    if indicator in message:
                        if self.debug_mode:
                            print(f"[DEBUG] 检测到测试指示器: {indicator}")
                        return True
        
        # 检查当前命令上下文
        if self.current_command and self.current_command in test_commands:
            if self.debug_mode:
                print(f"[DEBUG] 当前命令为测试命令: {self.current_command}")
            return True
            
        return False
    
    def _is_long_output_test(self, command: str) -> bool:
        """检测是否为长输出测试命令"""
        long_output_commands = ['mdu32', 'tfpu', 'hwtest', 'benchmark', 'clockinfo']
        return command in long_output_commands
    
    def _get_optimal_batch_size(self) -> int:
        """根据测试模式获取最优批处理大小"""
        if self.storm_active:
            return 10  # 风暴期间使用小批次
        
        if self._is_test_mode_active():
            if self._is_long_output_test(self.current_command or ""):
                return 20  # 长输出测试使用中等批次
            else:
                return 30  # 普通测试使用较大批次
        
        return 50  # 正常模式使用最大批次
    
    def _adaptive_adjust_storm_threshold(self, message_rate: float, current_time: float):
        """自适应调整风暴阈值"""
        # 检查调整间隔
        if current_time - self.last_threshold_adjustment < self.threshold_adjustment_interval:
            return
        
        # 记录风暴历史
        self.storm_history.append({
            'timestamp': current_time,
            'message_rate': message_rate,
            'was_storm': self.storm_active
        })
        
        # 如果有足够的历史数据，进行智能调整
        if len(self.storm_history) >= 5:
            recent_storms = [h for h in self.storm_history if h['was_storm']]
            avg_rate = sum(h['message_rate'] for h in self.storm_history) / len(self.storm_history)
            
            old_threshold = self.storm_threshold
            
            # 如果最近经常有风暴，提高阈值
            if len(recent_storms) >= 3:  # 最近5次中有3次风暴
                self.storm_threshold = min(
                    int(self.storm_threshold * self.threshold_adjustment_factor),
                    self.max_threshold
                )
                if self.debug_mode:
                    print(f"[DEBUG] 风暴频繁，提高阈值: {old_threshold} -> {self.storm_threshold}")
            
            # 如果很久没有风暴且平均消息率较低，可以适当降低阈值
            elif len(recent_storms) == 0 and avg_rate < self.base_storm_threshold * 0.5:
                self.storm_threshold = max(
                    int(self.storm_threshold / self.threshold_adjustment_factor),
                    self.min_threshold
                )
                if self.debug_mode:
                    print(f"[DEBUG] 风暴稀少，降低阈值: {old_threshold} -> {self.storm_threshold}")
            
            self.last_threshold_adjustment = current_time
    
    def _check_message_storm(self) -> bool:
        """优化的消息风暴检测"""
        current_time = time.time()
        self.message_timestamps.append(current_time)
        
        # 计算消息速率
        recent_messages = [t for t in self.message_timestamps if current_time - t < 2.0]
        message_rate = len(recent_messages) / 2.0
        
        # 智能阈值设置
        threshold = self._calculate_smart_threshold(message_rate)
        
        was_storm_active = self.storm_active
        self.storm_active = message_rate > threshold
        
        # 风暴状态变化处理
        if self.storm_active and not was_storm_active:
            self._on_storm_start(message_rate, threshold)
        elif not self.storm_active and was_storm_active:
            self._on_storm_end()
        
        return self.storm_active
    
    def _calculate_smart_threshold(self, current_rate: float) -> int:
        """计算智能阈值"""
        
        # 基础阈值
        base_threshold = 1000
        
        # 测试模式调整
        if self._is_test_mode_active():
            if self._is_long_output_test(self.current_command or ""):
                # 长输出测试：大幅提高阈值
                base_threshold = 50000  # 50000 msg/s
            else:
                # 普通测试：适度提高阈值
                base_threshold = 20000  # 20000 msg/s
        
        # 历史调整
        if len(self.storm_history) >= 3:
            recent_storms = sum(1 for h in self.storm_history[-3:] if h['was_storm'])
            
            if recent_storms >= 2:
                # 最近经常风暴，提高阈值
                base_threshold = int(base_threshold * 1.5)
            elif recent_storms == 0:
                # 最近无风暴，可以降低阈值
                base_threshold = int(base_threshold * 0.8)
        
        # 确保阈值在合理范围内
        return max(1000, min(base_threshold, 100000))
    
    def _on_storm_start(self, message_rate: float, threshold: int):
        """风暴开始处理"""
        current_time = time.time()
        self.storm_start_time = current_time
        self.processing_stats['storm_events'] += 1
        self.storm_detected.emit(True)
        
        # 降低错误级别，避免干扰
        if self.debug_mode:
            print(f"[DEBUG] 检测到消息风暴: {message_rate:.1f} msg/s (阈值: {threshold})")
        
        # 只在严重风暴时记录错误
        if message_rate > threshold * 2:
            error_event = ErrorEvent(
                timestamp=current_time,
                severity=ErrorSeverity.LOW,  # 降低到低级别
                category=ErrorCategory.MESSAGE_PROCESSING,
                message=f"严重消息风暴: {message_rate:.1f} msg/s",
                context={'message_rate': message_rate, 'threshold': threshold}
            )
            self.error_recovery.handle_error(error_event)
    
    def _on_storm_end(self):
        """风暴结束处理"""
        current_time = time.time()
        storm_duration = current_time - self.storm_start_time if self.storm_start_time else 0
        self.storm_detected.emit(False)
        
        if self.debug_mode:
            print(f"[DEBUG] 消息风暴结束，持续时间: {storm_duration:.1f}s")
    
    def process_message(self, raw_message: str) -> bool:
        """处理原始消息 (清理版本)"""
        if not raw_message or not raw_message.strip():
            return False
        
        # 递归深度保护 - 增强版本
        if self.recursion_depth >= self.max_recursion_depth:
            error_msg = f"消息处理递归深度超限: {self.recursion_depth}"
            self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, ErrorSeverity.HIGH)
            # 强制重置递归深度，防止永久阻塞
            self.recursion_depth = 0
            return False
        
        # 检查消息风暴
        if self._check_message_storm():
            return False
        
        # 添加到处理队列
        try:
            self.message_queue.append(raw_message)
            return True
        except Exception as e:
            error_msg = f"消息队列添加失败: {e}"
            self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, ErrorSeverity.MEDIUM)
            return False
    
    def _process_message_queue(self):
        """处理消息队列 - 改进的线程安全版本"""
        if not self.message_queue:
            return
        
        # 递归深度保护 - 增强版本
        if self.recursion_depth >= self.max_recursion_depth:
            if self.debug_mode:
                print(f"[DEBUG] 递归深度超限，强制重置: {self.recursion_depth}")
            self.recursion_depth = 0  # 强制重置
            return
        
        self.recursion_depth += 1
        
        # 使用带超时的锁，避免死锁
        lock_acquired = False
        try:
            lock_acquired = self.processing_lock.acquire(timeout=0.1)  # 100ms超时
            if not lock_acquired:
                # 锁获取失败，记录并跳过本次处理
                if self.debug_mode:
                    print("[DEBUG] 消息处理锁获取失败，跳过本次处理")
                self.recursion_depth -= 1
                return
            
            try:
                # 批量处理消息 (使用智能批处理大小)
                max_batch_size = self._get_optimal_batch_size()
                processed_count = 0
                
                # 添加内存使用检查
                if self._check_memory_usage():
                    # 内存使用过高，减少批处理大小
                    max_batch_size = max(1, max_batch_size // 4)
                    if self.debug_mode:
                        print(f"[DEBUG] 内存使用过高，限制批处理大小为: {max_batch_size}")
                
                while self.message_queue and processed_count < max_batch_size:
                    raw_message = self.message_queue.popleft()
                    
                    start_time = time.time()
                    
                    try:
                        success = self._process_single_message(raw_message)
                        
                        # 更新统计
                        processing_time = time.time() - start_time
                        self.processing_times.append(processing_time)
                        self.processing_stats['total_processed'] += 1
                        
                        if success:
                            self.processing_stats['total_errors'] = 0  # 重置错误计数
                        else:
                            self.processing_stats['total_errors'] += 1
                            
                    except Exception as e:
                        error_msg = f"单消息处理异常: {e}"
                        # 检查是否为测试命令相关的异常
                        if any(cmd in str(e) for cmd in ['mdu32', 'tfpu']):
                            self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, ErrorSeverity.LOW)
                        else:
                            self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, ErrorSeverity.MEDIUM)
                        self.processing_stats['total_errors'] += 1
                    
                    processed_count += 1
                    
                    # 在处理过程中定期检查锁状态，避免长时间阻塞
                    if processed_count % 10 == 0 and self.storm_active:
                        # 风暴期间更频繁地检查
                        break
                
                # 更新平均处理时间
                if self.processing_times:
                    self.processing_stats['average_processing_time'] = sum(self.processing_times) / len(self.processing_times)
            
            finally:
                self.processing_lock.release()
        
        finally:
            self.recursion_depth -= 1
    
    def _classify_exception(self, exception: Exception) -> tuple[ErrorSeverity, bool]:
        """异常分类器 - 精确分类异常类型和处理策略"""
        
        # 测试命令相关异常 - 最低级别，忽略处理
        test_command_exceptions = (
            KeyError, 
            AttributeError, 
            ValueError
        )
        
        # 检查是否为测试命令上下文
        if self._is_test_mode_active():
            if any(cmd in str(exception).lower() for cmd in ['mdu32', 'tfpu', 'hwtest', 'benchmark']):
                return ErrorSeverity.LOW, True  # 低级别，忽略处理
        
        # 设备信息解析异常 - 低级别，记录但不恢复
        device_info_patterns = [
            r'device_info',
            r'attribute.*error',
            r'key.*error', 
            r'value.*error',
            r'index.*error'
        ]
        
        exception_str = str(exception).lower()
        if any(re.search(pattern, exception_str) for pattern in device_info_patterns):
            return ErrorSeverity.LOW, True  # 低级别，忽略处理
        
        # 编码错误 - 低级别，忽略处理
        if isinstance(exception, UnicodeDecodeError):
            return ErrorSeverity.LOW, True
        
        # 其他未知异常 - 中级别，需要恢复
        return ErrorSeverity.MEDIUM, False

    def _process_single_message(self, raw_message: str) -> bool:
        """处理单个消息（优化异常处理）"""
        try:
            # 0. 检查消息有效性
            if not raw_message or not raw_message.strip():
                return True
            
            # 1. 检查重复
            if self.deduplicator.is_duplicate_response(raw_message):
                return False
            
            # 2. 识别命令
            command = self.tracker.identify_command(raw_message)
            if command:
                # 检查重复命令
                if self.deduplicator.is_duplicate_command(command):
                    return False
                
                # 记录命令
                self.deduplicator.record_command(command)
                self.tracker.start_command_tracking(command)
                self.current_command = command
                self.response_buffer = []
                
                # 发出命令信号
                self.command_detected.emit(command)
                
                if self.debug_mode:
                    print(f"[DEBUG] 检测到命令: {command}")
                
                return True
            
            # 3. 处理响应数据
            return self._process_response_data(raw_message)
            
        except KeyError as e:
            # 专门处理KeyError，提供更详细的错误信息
            missing_key = str(e).strip("'\"")
            if self.debug_mode:
                print(f"[DEBUG] 字段缺失错误: {missing_key}")
                # 提供上下文信息帮助调试
                print(f"[DEBUG] 消息内容: {raw_message[:100]}...")
            
            # 对于硬件测试相关的字段缺失，使用低严重级别
            if missing_key in ['mdu32', 'tfpu', 'benchmark', 'multiply', 'divide', 'sin']:
                if self.debug_mode:
                    print(f"[DEBUG] 硬件测试字段缺失: {missing_key}，跳过处理")
                return True  # 跳过处理但不报错
            else:
                # 其他KeyError使用中等严重级别
                error_msg = f"字段缺失: {missing_key}"
                self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, ErrorSeverity.MEDIUM)
                return False
                
        except Exception as e:
            # 使用异常分类器
            severity, should_ignore = self._classify_exception(e)
            
            if should_ignore:
                # 忽略的异常只记录调试信息
                if self.debug_mode:
                    print(f"[DEBUG] 忽略异常 ({severity.name}): {e}")
                return False
            else:
                # 需要处理的异常触发恢复机制
                error_msg = f"消息处理错误: {e}"
                self._handle_error(error_msg, ErrorCategory.MESSAGE_PROCESSING, severity)
                return False
    
    def _handle_error(self, error_message: str, category: ErrorCategory, severity: ErrorSeverity):
        """处理错误"""
        # 发出错误信号
        self.error_occurred.emit(error_message)
        
        # 创建错误事件
        error_event = ErrorEvent(
            timestamp=time.time(),
            severity=severity,
            category=category,
            message=error_message,
            context={
                'recursion_depth': self.recursion_depth,
                'queue_size': len(self.message_queue),
                'storm_active': self.storm_active
            }
        )
        
        # 尝试错误恢复
        recovery_success = self.error_recovery.handle_error(error_event)
        
        if self.debug_mode:
            print(f"[DEBUG] 错误处理: {error_message} (恢复: {'成功' if recovery_success else '失败'})")
    
    def _on_recovery_completed(self, result):
        """恢复完成回调"""
        if self.debug_mode:
            print(f"[DEBUG] 错误恢复完成: {result.strategy_name} (耗时: {result.duration:.2f}s)")
    
    def _on_recovery_failed(self, strategy_name, error_message):
        """恢复失败回调"""
        if self.debug_mode:
            print(f"[DEBUG] 错误恢复失败: {strategy_name} - {error_message}")
    
    def _health_check(self):
        """健康检查"""
        current_time = time.time()
        
        # 清理过期的处理时间记录
        if len(self.processing_times) > 0:
            # 保留最近100条记录
            cutoff_time = current_time - 3600  # 1小时
            # 这里简化处理，实际可以使用更精确的时间过滤
        
        if self.debug_mode and len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            print(f"[DEBUG] 健康检查: 平均处理时间 {avg_time:.3f}ms, 队列长度: {len(self.message_queue)}")
            
        # 定期内存清理
        self._perform_memory_cleanup()
    
    def _check_memory_usage(self) -> bool:
        """检查内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 检查内存使用是否超过阈值 (50MB)
            if memory_info.rss > 50 * 1024 * 1024:  # 50MB
                if self.debug_mode:
                    print(f"[DEBUG] 内存使用过高: {memory_info.rss / 1024 / 1024:.1f}MB")
                return True
            return False
        except Exception:
            # 如果无法获取内存信息，返回False
            return False
    
    def _perform_memory_cleanup(self):
        """执行内存清理"""
        try:
            # 清理过大的队列
            if len(self.message_queue) > 1000:
                # 只保留最近500条消息
                while len(self.message_queue) > 500:
                    self.message_queue.popleft()
                if self.debug_mode:
                    print("[DEBUG] 已清理消息队列，保留最新500条")
            
            # 清理过长的处理时间记录
            while len(self.processing_times) > 50:
                self.processing_times.popleft()
                
            # 强制垃圾回收（偶尔执行）
            if len(self.message_queue) % 100 == 0:  # 每100次检查执行一次
                import gc
                gc.collect()
                if self.debug_mode:
                    print("[DEBUG] 执行垃圾回收")
                    
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 内存清理失败: {e}")
    
    def _process_response_data(self, data: str) -> bool:
        """处理响应数据（修复版 - 支持长消息显示）"""
        try:
            # 检查数据是否为空
            if not data or not data.strip():
                return True
            
            # 大幅提高数据长度限制，支持完整的硬件测试输出
            if len(data) > 100000:  # 提高到100KB
                if self.debug_mode:
                    print(f"[DEBUG] 数据过长，直接处理: {len(data)} 字符")
                self.message_processed.emit(data, "response")
                return True
            
            # 简化数据包重组逻辑，优先直接处理
            reassembled = self.reassembler.add_fragment(data, self.current_command or "default")
            
            if reassembled:
                # 检查是否为响应开始
                if self.current_command and self.tracker.is_response_start(reassembled, self.current_command):
                    self.response_buffer.append(reassembled)
                    
                    if self.debug_mode:
                        print(f"[DEBUG] 响应开始: {self.current_command}")
                    
                    return True
                
                # 添加到响应缓冲区
                self.response_buffer.append(reassembled)
                
                # 检查是否为响应结束
                if self.current_command and self.tracker.is_response_end(reassembled, self.current_command):
                    # 合并完整响应
                    complete_response = '\n'.join(self.response_buffer)
                    
                    # 记录响应
                    self.deduplicator.record_response(complete_response)
                    
                    # 发出处理完成信号
                    self.message_processed.emit(complete_response, "response")
                    
                    # 结束命令跟踪
                    self.tracker.end_command_tracking(self.current_command)
                    self.current_command = None
                    self.response_buffer = []
                    
                    if self.debug_mode:
                        print(f"[DEBUG] 响应完成，长度: {len(complete_response)}")
                    
                    return True
            
            # 优化信号发送机制：减少不必要的信号发送
            self.response_buffer.append(data)
            
            # 降低立即处理阈值，更快显示消息
            if len(data) > 50 or len(self.response_buffer) > 5:  # 50字符或5行就处理
                # 合并当前缓冲区内容
                if self.response_buffer:
                    complete_response = '\n'.join(self.response_buffer)
                    # 记录响应
                    self.deduplicator.record_response(complete_response)
                    # 优化信号发送：检查是否为重复内容
                    if not self._is_duplicate_signal(complete_response):
                        self.message_processed.emit(complete_response, "response")
                    self.response_buffer = []  # 清空缓冲区
                else:
                    # 直接处理单个数据
                    if not self._is_duplicate_signal(data):
                        self.message_processed.emit(data, "response")
            else:
                # 短数据也立即处理，不等待
                if not self._is_duplicate_signal(data):
                    self.message_processed.emit(data, "response")
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 响应数据处理错误: {e}")
            # 出错时直接处理原始数据
            try:
                self.message_processed.emit(data, "response")
            except:
                pass
            return True
    
    def reset(self):
        """重置处理器状态 - 使用非阻塞锁"""
        lock_acquired = self.processing_lock.acquire(timeout=0.1)  # 100ms超时
        if not lock_acquired:
            if self.debug_mode:
                print("[DEBUG] 重置时锁获取失败，跳过重置")
            return
        
        try:
            self.current_command = None
            self.response_buffer = []
            
            # 清理消息队列
            self.message_queue.clear()
            
            # 重置风暴状态
            self.storm_active = False
            self.storm_start_time = None
            self.message_timestamps.clear()
            
            # 重置递归深度
            self.recursion_depth = 0
            
            # 清理各个组件
            self.reassembler.partial_packets.clear()
            for command in list(self.tracker.active_commands.keys()):
                self.tracker.end_command_tracking(command)
            
            # 重置统计信息
            self.processing_stats = {
                'total_processed': 0,
                'total_errors': 0,
                'average_processing_time': 0.0,
                'storm_events': 0
            }
            self.processing_times.clear()
            
            if self.debug_mode:
                print("[DEBUG] 消息处理器已重置")
        finally:
            self.processing_lock.release()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'processing_stats': self.processing_stats.copy(),
            'queue_size': len(self.message_queue),
            'storm_active': self.storm_active,
            'storm_duration': time.time() - self.storm_start_time if self.storm_start_time else 0,
            'recursion_depth': self.recursion_depth,
            'recovery_stats': self.error_recovery.get_recovery_statistics()
        }
    
    def configure_storm_threshold(self, threshold: int):
        """配置消息风暴阈值"""
        self.storm_threshold = threshold
        if self.debug_mode:
            print(f"[DEBUG] 消息风暴阈值设置为: {threshold} msg/s")
    
    def enable_emergency_mode(self):
        """启用紧急模式"""
        # 降低处理频率
        self.processing_timer.setInterval(50)  # 50ms处理间隔
        
        # 降低风暴阈值
        self.storm_threshold = max(10, self.storm_threshold // 2)
        
        if self.debug_mode:
            print("[DEBUG] 已启用紧急模式")
    
    def disable_emergency_mode(self):
        """禁用紧急模式"""
        # 恢复正常处理频率
        self.processing_timer.setInterval(10)  # 10ms处理间隔
        
        # 恢复正常风暴阈值
        self.storm_threshold = 50
        
        if self.debug_mode:
            print("[DEBUG] 已禁用紧急模式")
    
    def _is_duplicate_signal(self, data: str) -> bool:
        """检查是否为重复信号内容，减少不必要的信号发送"""
        if not hasattr(self, '_last_signal_data'):
            self._last_signal_data = {}
            return False
        
        # 对于设备信息更新消息，使用更严格的去重策略
        device_info_patterns = [
            '设备信息已更新',
            '设备信息已更新（等待用户手动刷新显示）',
            '设备信息已更新（非用户触发，不刷新显示）'
        ]
        
        is_device_info = any(pattern in data for pattern in device_info_patterns)
        if is_device_info:
            # 设备信息消息使用更长的去重时间
            dedup_time = 2.0  # 2秒去重时间
        else:
            dedup_time = 0.1  # 普通消息0.1秒去重时间
        
        # 生成数据指纹
        data_hash = hash(data)
        current_time = time.time()
        
        # 检查是否为重复数据
        if data_hash in self._last_signal_data:
            last_time = self._last_signal_data[data_hash]
            if current_time - last_time < dedup_time:
                if self.debug_mode:
                    print(f"[DEBUG] 过滤重复信号: {data[:30]}... (间隔: {current_time - last_time:.2f}s)")
                return True
        
        # 更新记录
        self._last_signal_data[data_hash] = current_time
        
        # 清理过期记录
        expired_hashes = [h for h, t in self._last_signal_data.items() 
                         if current_time - t > dedup_time * 2]  # 2倍去重时间过期
        for h in expired_hashes:
            del self._last_signal_data[h]
        
        return False
    
    def close(self):
        """关闭消息处理器"""
        try:
            self.processing_timer.stop()
            self.health_check_timer.stop()
            self.reset()
            
            if self.debug_mode:
                print("[DEBUG] 消息处理器已关闭")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 关闭消息处理器失败: {e}")