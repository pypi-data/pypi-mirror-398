#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口管理核心模块 - ColorBridge (优化版本)
解决程序关闭无响应、数据发送失败等关键问题
集成错误恢复和智能监控机制
"""

import time
import threading
import hashlib
import os
from collections import deque
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition, QTimer, QMutexLocker
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from serial import SerialException
from .colorbridge_logger_manager import LoggerManager
from .colorbridge_error_recovery import ErrorRecoveryManager, ErrorEvent, ErrorCategory, ErrorSeverity
from .colorbridge_monitoring_system import MonitoringSystem, MetricType, AlertLevel
from .colorbridge_message_processor import ColorBridgeMessageProcessor
from .colorbridge_debug_logger import get_debug_logger, debug_log, info_log, warning_log, error_log

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class DebugLogger:
    """简化的日志级别控制"""
    def __init__(self, level=LogLevel.INFO):
        self.level = level
    
    def debug(self, message):
        if self.level <= LogLevel.DEBUG:
            debug_log(message, "SerialManager")
    
    def info(self, message):
        if self.level <= LogLevel.INFO:
            info_log(message, "SerialManager")
    
    def warning(self, message):
        if self.level <= LogLevel.WARNING:
            warning_log(message, "SerialManager")
    
    def error(self, message):
        if self.level <= LogLevel.ERROR:
            error_log(message, "SerialManager")

# 常量定义
class SerialConstants:
    """串口相关常量"""
    # 等待时间常量
    BASE_WAIT_TIME = 5  # 基础等待时间(ms)
    MAX_WAIT_TIME = 50  # 最大等待时间(ms)
    
    # 缓冲区大小常量
    MIN_BUFFER_SIZE = 10240  # 10KB最小缓冲区
    MAX_BUFFER_SIZE = 307200  # 300KB最大缓冲区
    DEFAULT_BUFFER_SIZE = 50000  # 默认缓冲区大小，50KB
    
    # 响应超时常量 - 仅在发送命令后检测响应
    RESPONSE_TIMEOUT = 10.0  # 发送命令后10秒无响应认为超时
    
    # 错误处理常量
    MAX_EMPTY_READS = 3  # 最大空读取次数
    MAX_ERRORS = 5  # 最大错误计数
    ERROR_RETRY_DELAY = 3.0  # 错误重试延迟(秒)
    
    # 批处理常量
    BATCH_SIZE = 10  # 批量处理大小
    BUFFER_HISTORY_LENGTH = 10  # 缓冲区使用率历史长度
    
    # 健康检查常量
    HEALTH_CHECK_INTERVAL = 2.0  # 健康检查间隔(秒)

class SerialReaderThread(QThread):
    """增强稳定的串口读取线程"""
    message_received = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)  # is_stable
    buffer_overflow_warning = pyqtSignal(int)  # buffer_size
    
    def __init__(self, serial_port, monitoring_system: MonitoringSystem = None, debug_mode: bool = False):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        self.debug_mode = debug_mode  # 使用传入的调试模式设置
        self.logger = DebugLogger(LogLevel.DEBUG if debug_mode else LogLevel.INFO)
        
        # 监控系统集成
        self.monitoring_system = monitoring_system
        
        # 性能优化参数
        self.wait_time = SerialConstants.BASE_WAIT_TIME
        self.max_wait_time = SerialConstants.MAX_WAIT_TIME
        self.batch_size = SerialConstants.BATCH_SIZE
        self.buffer_size = 0
        self.last_data_time = time.time()
        
        # 动态缓冲区管理
        self.min_buffer_size = SerialConstants.MIN_BUFFER_SIZE
        self.max_buffer_size = SerialConstants.MAX_BUFFER_SIZE
        self.current_buffer_size = SerialConstants.DEFAULT_BUFFER_SIZE
        self.buffer_usage_history = deque(maxlen=SerialConstants.BUFFER_HISTORY_LENGTH)
        
        # 连接稳定性监控 - 简化版本
        self.last_activity_time = time.time()
        self.connection_timeout = SerialConstants.RESPONSE_TIMEOUT
        self.last_send_time = 0  # 记录最后发送时间
        self.response_received = False  # 标记是否收到响应
        
        # 线程安全
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        
    def run(self):
        """主读取循环 - 修复卡死问题的版本"""
        self.logger.debug("启动修复版本的串口读取线程")
            
        data_buffer = ""
        consecutive_empty_reads = 0
        max_empty_reads = SerialConstants.MAX_EMPTY_READS
        error_count = 0
        max_errors = SerialConstants.MAX_ERRORS
        last_error_time = 0
        last_activity_time = time.time()
        
        # 添加线程健康检查
        health_check_interval = SerialConstants.HEALTH_CHECK_INTERVAL
        last_health_check = time.time()
        
        while self.running:
            try:
                # 检查串口是否仍然有效
                if not self.serial_port or not self.serial_port.isOpen():
                    if self.debug_mode:
                        self.logger.debug("串口已关闭，退出读取线程")
                    break
                
                # 健康检查 - 防止线程卡死
                current_time = time.time()
                if current_time - last_health_check > health_check_interval:
                    last_health_check = current_time
                    # 简化健康检查，只依赖串口模块的连接状态
                    if not self.serial_port.isOpen():
                        if self.debug_mode:
                            self.logger.warning("串口连接已断开")
                        break
                
                # 简化的错误处理机制
                if error_count >= max_errors:
                    if current_time - last_error_time < SerialConstants.ERROR_RETRY_DELAY:
                        self.logger.warning(f"错误过多，暂停读取 {error_count} 个错误")
                        time.sleep(0.1)  # 大幅减少暂停时间
                        error_count = 0  # 重置错误计数
                        continue
                    
                # 使用非阻塞方式读取数据，避免"等待的操作过时"错误
                bytes_available = self.serial_port.bytesAvailable()
                if bytes_available > 0:
                    # 有数据可读，直接读取
                    data = self.serial_port.readAll()
                    if data:
                        data_str = bytes(data).decode('utf-8', errors='ignore')
                        if self.debug_mode:
                            debug_log(f"串口接收到原始数据: {repr(data_str)} (长度: {len(data_str)})", "SerialReaderThread")
                        data_buffer += data_str
                        self.buffer_size = len(data_buffer)
                        self.last_data_time = current_time
                        consecutive_empty_reads = 0
                        error_count = 0  # 重置错误计数
                        
                        # 标记已收到响应
                        if hasattr(self, 'last_send_time') and self.last_send_time > 0:
                            self.response_received = True
                            if self.debug_mode:
                                response_time = time.time() - self.last_send_time
                                print(f"[DEBUG] 收到响应，耗时: {response_time:.3f}秒")
                            # 不重置发送时间，让超时检测继续工作
                            # 超时检测会在检测到超时后重置
                        
                        # 更新连接稳定性 - 已禁用状态监控
                        # self.stable_connection_count += 1
                        # self.unstable_connection_count = 0  # 重置不稳定计数
                        # if self.stable_connection_count >= self.stability_threshold:
                        #     if self.current_status != True:
                        #         self.connection_status_changed.emit(True)
                        #         self.current_status = True
                            
                        # 智能缓冲区管理 - 分级清理策略
                        data_buffer, buffer_cleaned = self._smart_buffer_management(data_buffer)
                        
                        # 改进的消息分割检测和处理
                        # 检查是否有完整的消息（以换行符分隔）
                        while '\n' in data_buffer:
                            # 找到第一个换行符
                            newline_pos = data_buffer.find('\n')
                            # 提取完整消息（包含换行符）
                            complete_message = data_buffer[:newline_pos + 1]
                            # 从缓冲区移除已处理的部分
                            data_buffer = data_buffer[newline_pos + 1:]
                            
                            if self.debug_mode:
                                print(f"[DEBUG] 提取完整消息，长度: {len(complete_message)}")
                            
                            # 处理完整消息
                            self._process_data_batch(complete_message)
                        
                        # 如果缓冲区有数据但超过1秒没有新数据，强制处理
                        if len(data_buffer) > 0 and time.time() - self.last_data_time > 1.0:
                            if self.debug_mode:
                                print(f"[DEBUG] 超时强制处理数据，缓冲区长度: {len(data_buffer)}")
                            self._process_data_batch(data_buffer)
                            data_buffer = ""
                        
                        # 检查发送命令后的响应超时
                        if (hasattr(self, 'last_send_time') and self.last_send_time > 0 and 
                            not self.response_received and
                            time.time() - self.last_send_time > SerialConstants.RESPONSE_TIMEOUT):
                            if self.debug_mode:
                                print(f"[DEBUG] 发送命令后响应超时: {time.time() - self.last_send_time:.1f}秒")
                            # 发送超时信号
                            self.error_occurred.emit(f"命令响应超时: {time.time() - self.last_send_time:.1f}秒")
                            # 重置发送时间和响应标记
                            self.last_send_time = 0
                            self.response_received = False
                            
                            # 记录性能指标
                            if self.monitoring_system:
                                self.monitoring_system.record_metric(
                                    MetricType.SERIAL_READ_RATE, 
                                    len(data_str)
                                )
                else:
                    # 无数据可读，使用非常短暂的等待，避免卡死
                    time.sleep(0.005)  # 5ms超短等待，减少阻塞时间
                    consecutive_empty_reads += 1
                    last_activity_time = current_time  # 更新活动时间，即使无数据
                    
                    if consecutive_empty_reads >= max_empty_reads:
                        # 动态调整等待时间，但限制最大值
                        self.wait_time = min(self.wait_time + 1, 20)  # 最大20ms
                        consecutive_empty_reads = 0
                        
                        # 检查连接稳定性 - 已禁用状态监控
                        
                        # if self.unstable_connection_count >= 8 and self.current_status != False:  # 提高阈值
                        #     self.connection_status_changed.emit(False)
                        #     self.current_status = False
                    
                    # 状态检查已完全禁用以提升性能
                        
                # 简化的缓冲区管理
                if self.buffer_size > self.max_buffer_size:
                    if self.debug_mode:
                        print(f"[DEBUG] 缓冲区溢出: {self.buffer_size} 字节")
                    data_buffer = ""
                    self.buffer_size = 0
                    
            except (SerialException, OSError, IOError) as e:
                error_count += 1
                last_error_time = current_time
                
                # 特殊处理串口相关错误
                if "等待的操作过时" in str(e) or "timeout" in str(e).lower():
                    self.logger.debug(f"忽略超时错误 #{error_count}: {e}")
                elif "Permission denied" in str(e):
                    self.logger.error(f"串口权限错误 #{error_count}: {e}")
                    self.error_occurred.emit(f"串口权限被拒绝，请检查设备权限")
                    break
                elif "device not found" in str(e).lower():
                    self.logger.error(f"设备未找到错误 #{error_count}: {e}")
                    self.error_occurred.emit(f"串口设备未找到，请检查设备连接")
                    break
                else:
                    self.logger.error(f"串口读取错误 #{error_count}: {e}")
                
                # 检查错误计数
                if error_count >= max_errors:
                    if current_time - last_error_time < SerialConstants.ERROR_RETRY_DELAY:
                        self.logger.error(f"串口读取错误过多，停止读取线程")
                        self.error_occurred.emit(f"串口读取错误过多: {error_count} 个错误")
                        break
            except Exception as e:
                # 捕获其他未预期的错误
                self.logger.error(f"串口读取未知错误: {e}")
                self.error_occurred.emit(f"串口读取发生未知错误: {e}")
                break
                
        if self.debug_mode:
            self.logger.debug("串口读取线程已结束")
            
    def _smart_buffer_management(self, data_buffer: str) -> tuple:
        """智能缓冲区管理，返回处理后的缓冲区和是否发生了清理"""
        buffer_size = len(data_buffer)
        buffer_cleaned = False
        
        # 动态调整缓冲区大小，基于测试模式
        if self._is_test_mode_active(data_buffer):
            # 测试模式下增大缓冲区限制
            force_clean_threshold = 100000  # 100KB
            gentle_clean_threshold = 50000  # 50KB
            keep_size = 5000  # 保留5KB
        else:
            # 正常模式使用较小缓冲区
            force_clean_threshold = 50000  # 50KB
            gentle_clean_threshold = 20000  # 20KB
            keep_size = 2000  # 保留2KB
        
        # 分级清理策略
        if buffer_size > force_clean_threshold:  # 强制清理
            if self.debug_mode:
                self.logger.warning(f"缓冲区过大，强制清理: {buffer_size} 字节")
            data_buffer = data_buffer[-keep_size:]  # 只保留最后部分
            buffer_cleaned = True
            self.buffer_overflow_warning.emit(buffer_size)
            
        elif buffer_size > gentle_clean_threshold:  # 温和清理
            if self.debug_mode:
                self.logger.info(f"缓冲区较大，执行温和清理: {buffer_size} 字节")
            # 移除重复的设备信息段落
            lines = data_buffer.split('\n')
            cleaned_lines = []
            seen_patterns = set()
            
            for line in lines:
                # 检查是否为重复的设备信息行
                if any(pattern in line for pattern in [
                    '设备信息已更新', 'MCU:', '时钟:', 'Flash:', 'XRAM已用:'
                ]):
                    try:
                        # 检查hashlib是否可用
                        import hashlib
                        line_hash = hashlib.md5(line.encode()).hexdigest()[:8]
                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] hashlib不可用，使用备用哈希: {e}")
                        # 备用哈希方案
                        import time
                        import hashlib
                        line_hash = f"{hashlib.md5(f'{line}_{int(time.time())}'.encode()).hexdigest()[:8]}"
                    
                    if line_hash in seen_patterns:
                        continue  # 跳过重复行
                    seen_patterns.add(line_hash)
                
                cleaned_lines.append(line)
                
            data_buffer = '\n'.join(cleaned_lines)
            if len(data_buffer) != buffer_size:
                buffer_cleaned = True
                
        return data_buffer, buffer_cleaned
    
    def _is_test_mode_active(self, data_buffer: str) -> bool:
        """检测是否为测试模式，基于缓冲区内容"""
        test_indicators = [
            '硬件加速单元测试',
            '硬件乘除单元详细测试', 
            '浮点运算单元详细测试',
            '性能基准测试',
            'MDU32测试完成',
            'TFPU测试完成',
            'mdu32', 'tfpu', 'hwtest', 'benchmark'
        ]
        
        # 检查缓冲区中是否包含测试相关内容
        for indicator in test_indicators:
            if indicator in data_buffer:
                return True
        return False
    
    def _process_data_batch(self, data_buffer: str):
        """批量处理数据 - 保持原始格式，优化重复数据处理"""
        # 检查是否为空数据
        if not data_buffer.strip():
            return
        
        # 记录接收到的数据用于调试
        if self.debug_mode:
            print(f"[DEBUG] 接收数据块: {repr(data_buffer[:100])}...")
        
        # 立即发送完整消息，不分割，不添加时间戳
        # 时间戳由主窗口统一添加
        try:
            self.message_received.emit(data_buffer)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 消息发送失败: {e}")
                    
    def stop(self):
        """简化的安全停止线程方法"""
        self.logger.debug("正在停止读取线程...")
        
        # 1. 立即设置停止标志
        self.running = False
        
        # 2. 唤醒等待线程
        try:
            self.wait_condition.wakeAll()
        except Exception:
            pass  # 忽略唤醒失败
        
        # 3. 等待线程自然退出
        if self.isRunning():
            try:
                self.wait(500)  # 只等待0.5秒
            except Exception:
                pass
        
        # 4. 清理资源
        try:
            self.quit()
        except Exception:
            pass
        
        self.logger.debug("线程停止完成")
            
    def is_alive(self):
        """检查线程是否存活"""
        return self.isRunning()
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "buffer_size": self.buffer_size,
            "wait_time": self.wait_time,
            "stable_count": self.stable_connection_count,
            "unstable_count": self.unstable_connection_count,
            "last_data_time": self.last_data_time
        }

class ColorBridgeSerialManager(QObject):
    """增强稳定的串口管理器"""
    message_received = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    # 串口管理器常量
    WRITE_TIMEOUT = 5000  # 5秒写入超时
    MAX_WRITE_RETRIES = 3
    MAX_CONNECTION_ATTEMPTS = 5
    THREAD_WAIT_TIMEOUT = 500  # 线程等待超时(ms)
    
    def __init__(self, monitoring_system: MonitoringSystem = None, debug_mode: bool = False):
        super().__init__()
        self.serial_port = QSerialPort()
        self.reader_thread = None
        self.debug_mode = debug_mode  # 使用传入的调试模式设置
        self.logger = DebugLogger(LogLevel.DEBUG if debug_mode else LogLevel.INFO)
        
        # 连接信号
        self.serial_port.errorOccurred.connect(self.on_error)
        
        # 监控系统集成
        self.monitoring_system = monitoring_system
        
        # 错误恢复管理器
        try:
            self.error_recovery = ErrorRecoveryManager()
        except Exception as e:
            self.logger.warning(f"无法初始化错误恢复管理器: {e}")
            self.error_recovery = None
        
        # 消息处理器
        try:
            self.message_processor = ColorBridgeMessageProcessor()
        except Exception as e:
            self.logger.warning(f"无法初始化消息处理器: {e}")
            self.message_processor = None
        
        # 连接状态管理
        self._is_disconnecting = False
        self.connection_attempts = 0
        self.max_connection_attempts = self.MAX_CONNECTION_ATTEMPTS
        
        # 性能监控
        self.last_connect_time = None
        self.connection_success_rate = 0.0
        
        # 线程安全和超时机制 - 优化版本
        self.write_mutex = QMutex()
        self.write_timeout = self.WRITE_TIMEOUT
        self.max_write_retries = self.MAX_WRITE_RETRIES
        self._write_in_progress = False
        self._write_lock = threading.Lock()  # 添加线程锁确保写入操作的原子性
        
        # 发送队列和间隔控制
        self._send_queue = deque()
        self._last_send_time = 0
        self._min_send_interval = 0.2  # 最小发送间隔200ms
        self._queue_processing = False  # 队列处理标志
        self._last_command_hash = None  # 最近发送命令的哈希值
        self._command_dedup_window = 0.5  # 命令去重窗口500ms
        
    def get_available_ports(self):
        """获取可用串口列表"""
        ports = []
        for port_info in QSerialPortInfo.availablePorts():
            port_name = port_info.portName()
            port_description = port_info.description()
            if port_description:
                ports.append(f"{port_name} - {port_description}")
            else:
                ports.append(port_name)
        return sorted(ports)
        
    def connect(self, port_name, baud_rate=115200, max_retries=5):
        """连接串口，支持增强的自动重试机制（修复OpenError处理）"""
        # 提取纯端口名（去掉描述部分）
        if " - " in port_name:
            port_name = port_name.split(" - ")[0]
        
        # 平台检测和日志
        import platform
        current_platform = platform.system()
        if self.debug_mode:
            self.logger.debug(f"连接串口: {port_name}, 平台: {current_platform}")
        
        for attempt in range(max_retries):
            # 预先检查端口是否可用
            available_ports = [port.portName() for port in QSerialPortInfo.availablePorts()]
            if port_name not in available_ports:
                if self.debug_mode:
                    self.logger.debug(f"端口 {port_name} 不可用，跳过连接尝试")
                
                # 在Linux下，检查是否有常见的USB串口设备
                if current_platform == "Linux" and attempt == 0:
                    if self.debug_mode:
                        self.logger.debug("在Linux下，检查常见USB串口设备...")
                    # 检查常见的Linux串口设备
                    common_linux_ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]
                    for common_port in common_linux_ports:
                        if os.path.exists(common_port):
                            if self.debug_mode:
                                self.logger.debug(f"发现Linux串口设备: {common_port}")
                            # 检查权限
                            try:
                                import stat
                                st = os.stat(common_port)
                                if not (st.st_mode & stat.S_IROTH) or not (st.st_mode & stat.S_IWOTH):
                                    if self.debug_mode:
                                        self.logger.debug(f"设备 {common_port} 权限不足，需要dialout组权限")
                                    self.error_occurred.emit(f"Linux设备 {common_port} 权限不足，请确保用户已加入dialout组")
                            except Exception as e:
                                if self.debug_mode:
                                    self.logger.debug(f"检查设备权限失败: {e}")
                
                continue
            
            self.serial_port.setPortName(port_name)
            self.serial_port.setBaudRate(baud_rate)
            self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
            self.serial_port.setParity(QSerialPort.Parity.NoParity)
            self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
            self.serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
            
            # 尝试打开串口，增加错误处理（优化版本）
            try:
                # 预先检查串口状态
                if self.serial_port.isOpen():
                    if self.debug_mode:
                        print("[DEBUG] 串口已打开，先关闭")
                    self.serial_port.close()
                    time.sleep(0.1)  # 短暂等待
                
                # 尝试打开串口
                open_result = self.serial_port.open(QSerialPort.OpenModeFlag.ReadWrite)
                
                if open_result:
                    if self.debug_mode:
                        print(f"[DEBUG] 串口连接成功: {port_name} (尝试 {attempt + 1}/{max_retries})")
                    
                    # 创建并启动读取线程
                    try:
                        if self.debug_mode:
                            print("[DEBUG] 开始创建读取线程...")
                        self.reader_thread = SerialReaderThread(self.serial_port, self.monitoring_system, self.debug_mode)
                        if self.debug_mode:
                            print(f"[DEBUG] 读取线程对象创建完成: {self.reader_thread}")
                        
                        # 连接信号
                        self.reader_thread.message_received.connect(self.message_received.emit)
                        self.reader_thread.connection_status_changed.connect(self._on_connection_stability_changed)
                        self.reader_thread.buffer_overflow_warning.connect(self._on_buffer_overflow)
                        
                        if self.debug_mode:
                            print("[DEBUG] 开始启动读取线程...")
                        self.reader_thread.start()
                        
                        # 等待线程启动
                        if self.debug_mode:
                            print("[DEBUG] 等待线程启动...")
                        time.sleep(0.2)  # 增加等待时间
                        
                        # 验证线程是否正常启动
                        thread_running = self.reader_thread.isRunning()
                        if self.debug_mode:
                            print(f"[DEBUG] 线程运行状态检查: {thread_running}")
                        
                        if not thread_running:
                            if self.debug_mode:
                                print("[DEBUG] 读取线程启动失败")
                            self.serial_port.close()
                            raise Exception("读取线程启动失败")
                        else:
                            if self.debug_mode:
                                print("[DEBUG] 读取线程启动成功")
                            
                    except Exception as thread_error:
                        if self.debug_mode:
                            print(f"[DEBUG] 创建读取线程失败: {thread_error}")
                        self.serial_port.close()
                        raise thread_error
                    
                    # 记录连接成功
                    self.connection_attempts = attempt + 1
                    self.last_connect_time = time.time()
                    self.connection_success_rate = 1.0 / (attempt + 1)
                    
                    # 连接成功信号
                    self.connection_changed.emit(True)
                    
                    # 记录成功指标
                    if self.monitoring_system:
                        try:
                            self.monitoring_system.record_metric(
                                MetricType.CONNECTION_SUCCESS, 
                                attempt + 1
                            )
                        except Exception as metric_error:
                            if self.debug_mode:
                                print(f"[DEBUG] 记录指标失败: {metric_error}")
                    
                    return True
                else:
                    # 检查具体的错误原因
                    error = self.serial_port.error()
                    error_string = self.serial_port.errorString()
                    
                    if attempt < max_retries - 1:
                        # 根据错误类型调整重试策略
                        if error == QSerialPort.SerialPortError.PermissionError:
                            retry_delay = min(5 + attempt, 10)  # 权限错误使用更长延迟
                            if self.debug_mode:
                                self.logger.debug(f"权限错误，{retry_delay}秒后重试... ({attempt + 1}/{max_retries}): {error_string}")
                        elif error == QSerialPort.SerialPortError.ResourceError:
                            retry_delay = min(3 + attempt, 8)  # 资源错误使用中等延迟
                            if self.debug_mode:
                                self.logger.debug(f"资源错误，{retry_delay}秒后重试... ({attempt + 1}/{max_retries}): {error_string}")
                        else:
                            retry_delay = min(2 ** attempt, 5)  # 其他错误使用标准延迟
                            if self.debug_mode:
                                self.logger.debug(f"串口连接失败，{retry_delay}秒后重试... ({attempt + 1}/{max_retries}): {error_string}")
                        
                        time.sleep(retry_delay)
                        continue
                    else:
                        if self.debug_mode:
                            self.logger.debug(f"串口连接最终失败: {port_name} - {error_string}")
                        
                        # 提供Linux特定的错误信息
                        if current_platform == "Linux" and error == QSerialPort.SerialPortError.PermissionError:
                            self.error_occurred.emit(f"Linux串口权限被拒绝: {port_name}\n请确保用户已加入dialout组:\n  sudo usermod -a -G dialout $USER\n然后注销并重新登录")
                        elif current_platform == "Linux" and error == QSerialPort.SerialPortError.ResourceError:
                            self.error_occurred.emit(f"Linux串口资源错误: {port_name}\n设备可能被其他程序占用或不存在")
                        else:
                            self.error_occurred.emit(f"串口连接失败: {error_string}")
                        
                        self.connection_changed.emit(False)
                        return False
                        
            except Exception as e:
                # 特殊处理OpenError和权限错误
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["openerror", "permission denied", "access denied", "设备占用"]):
                    if self.debug_mode:
                        print(f"[DEBUG] 检测到设备占用问题: {e}")
                    # 对于设备占用问题，增加更长的重试间隔
                    if attempt < max_retries - 1:
                        retry_delay = min(5 + attempt * 2, 15)  # 占用问题使用更长延迟
                        if self.debug_mode:
                            print(f"[DEBUG] 设备占用重试，{retry_delay}秒后重试... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                else:
                    # 其他异常的正常处理
                    if attempt < max_retries - 1:
                        retry_delay = min(2 ** attempt, 5)  # 最多5秒延迟
                        if self.debug_mode:
                            print(f"[DEBUG] 串口连接异常，{retry_delay}秒后重试... ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        if self.debug_mode:
                            print(f"[DEBUG] 串口连接最终异常: {e}")
                        self.connection_changed.emit(False)
                        return False
        
        return False
            
    def disconnect(self):
        """简化的断开串口连接方法"""
        try:
            if self.debug_mode:
                print("[DEBUG] 正在断开串口连接...")
            
            # 设置断开标志
            self._is_disconnecting = True
            
            # 1. 立即停止写入操作 - 使用线程锁确保安全
            with self._write_lock:
                self._write_in_progress = False
            
            # 2. 快速停止读取线程（修复卡死问题）
            if self.reader_thread:
                try:
                    # 设置停止标志
                    self.reader_thread.running = False
                    
                    # 快速唤醒线程
                    try:
                        self.reader_thread.wait_condition.wakeAll()
                    except:
                        pass  # 忽略唤醒失败
                    
                    # 不等待线程结束，直接清理，避免卡死
                    # 如果线程是daemon，程序退出时会自动清理
                    if self.reader_thread.isRunning():
                        # 只等待很短时间，不阻塞程序关闭
                        try:
                            self.reader_thread.wait(self.THREAD_WAIT_TIMEOUT)  # 使用常量
                        except:
                            pass  # 忽略等待失败
                    
                    self.reader_thread = None
                    if self.debug_mode:
                        print("[DEBUG] 读取线程已快速停止")
                        
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 停止读取线程失败: {e}")
            
            # 3. 快速关闭串口
            if self.serial_port and self.serial_port.isOpen():
                try:
                    self.serial_port.close()
                    if self.debug_mode:
                        print("[DEBUG] 串口已关闭")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 关闭串口失败: {e}")
            
            # 4. 发出断开信号
            try:
                self.connection_changed.emit(False)
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 发出断开信号失败: {e}")
            
            if self.debug_mode:
                print("[DEBUG] 串口断开完成")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 断开串口时发生异常: {e}")
        finally:
            self._is_disconnecting = False
            self._write_in_progress = False  # 确保重置写入标志
            
    def send_command(self, command: str) -> bool:
        """发送命令到串口 - 兼容UI调用的方法（优化版本）"""
        return self.send_data(command)
        
    def send_data(self, data: str) -> bool:
        """发送数据到串口 - 增强超时和线程安全机制（优化版本）"""
        # 检查发送间隔
        current_time = time.time()
        time_since_last_send = current_time - self._last_send_time
        
        if time_since_last_send < self._min_send_interval:
            if self.debug_mode:
                print(f"[DEBUG] 发送间隔太短: {time_since_last_send:.3f}s，跳过发送（取消队列机制）")
            # 取消队列机制：直接返回False表示发送被拒绝
            # 不再加入队列，不再延迟发送
            return False  # 返回False表示发送被拒绝
        
        # 使用线程锁确保写入操作的原子性
        with self._write_lock:
            if self._write_in_progress:
                if self.debug_mode:
                    print("[DEBUG] 写入操作进行中，跳过本次发送")
                return False
            self._write_in_progress = True
        
        try:
            # 检查串口状态
            if not self.serial_port or not self.serial_port.isOpen():
                self.logger.warning("串口未连接，无法发送数据")
                return False
                
            # 确保数据以换行符结尾
            if not data.endswith('\n'):
                data += '\n'
                
            # 线程安全的写入操作
            with QMutexLocker(self.write_mutex):
                # 注意：PyQt6的QSerialPort不支持setWriteTimeout方法
                # 使用waitForBytesWritten()来处理写入超时
                
                # 重试机制
                for attempt in range(self.max_write_retries):
                    try:
                        # 转换为字节并发送
                        bytes_data = data.encode('utf-8')
                        bytes_written = self.serial_port.write(bytes_data)
                        
                        if bytes_written > 0:
                            # 等待写入完成（带超时）
                            if self.serial_port.waitForBytesWritten(self.write_timeout):
                                if self.debug_mode:
                                    print(f"[DEBUG] 发送数据成功: {data.strip()}")
                                # 记录发送时间和指标
                                self._last_send_time = time.time()
                                # 更新最后命令哈希
                                import hashlib
                                self._last_command_hash = hashlib.md5(data.strip().encode()).hexdigest()[:8]
                                if hasattr(self, 'reader_thread') and self.reader_thread:
                                    self.reader_thread.last_send_time = self._last_send_time
                                if self.monitoring_system:
                                    self.monitoring_system.record_metric(
                                        MetricType.SERIAL_WRITE_RATE, 
                                        bytes_written
                                    )
                                return True
                            else:
                                if self.debug_mode:
                                    print(f"[DEBUG] 写入超时，重试 {attempt + 1}/{self.max_write_retries}")
                                if attempt < self.max_write_retries - 1:
                                    time.sleep(0.1)  # 短暂延迟后重试
                                    continue
                        else:
                            if self.debug_mode:
                                print(f"[DEBUG] 发送数据失败: 写入0字节，重试 {attempt + 1}/{self.max_write_retries}")
                            if attempt < self.max_write_retries - 1:
                                time.sleep(0.1)  # 短暂延迟后重试
                                continue
                                
                    except (SerialException, OSError, IOError) as write_error:
                        if self.debug_mode:
                            print(f"[DEBUG] 写入异常 {attempt + 1}/{self.max_write_retries}: {write_error}")
                        
                        # 特殊处理串口写入错误
                        if "Permission denied" in str(write_error):
                            self.logger.error(f"串口写入权限错误: {write_error}")
                            self.error_occurred.emit(f"串口写入权限被拒绝")
                            return False
                        elif "device not found" in str(write_error).lower():
                            self.logger.error(f"串口设备未找到: {write_error}")
                            self.error_occurred.emit(f"串口设备未找到")
                            return False
                        
                        if attempt < self.max_write_retries - 1:
                            time.sleep(0.1)  # 短暂延迟后重试
                            continue
                        else:
                            self.logger.error(f"发送数据重试失败: {write_error}")
                            self.error_occurred.emit(f"发送数据失败: {write_error}")
                            return False
                    except (OSError, IOError, ValueError, TypeError) as write_error:
                        # 捕获具体的写入错误类型
                        self.logger.error(f"发送数据错误: {write_error}")
                        self.error_occurred.emit(f"发送数据失败: {write_error}")
                        return False
                    except Exception as write_error:
                        # 捕获其他未预期的写入错误
                        self.logger.error(f"发送数据未知错误: {write_error}")
                        self.error_occurred.emit(f"发送数据发生未知错误: {write_error}")
                        return False
                
                # 所有重试都失败
                if self.debug_mode:
                    print("[DEBUG] 发送数据最终失败：所有重试都已用尽")
                self.error_occurred.emit("发送数据失败：超时或写入错误")
                return False
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 发送数据严重异常: {e}")
            self.error_occurred.emit(f"发送数据失败: {e}")
            return False
        finally:
            # 在锁保护下重置写入标志
            with self._write_lock:
                self._write_in_progress = False
            
    def is_connected(self) -> bool:
        """检查串口是否连接"""
        # 简化的连接状态检查
        port_exists = self.serial_port is not None
        port_open = self.serial_port and self.serial_port.isOpen() if self.serial_port else False
        thread_exists = self.reader_thread is not None
        thread_running = self.reader_thread and self.reader_thread.isRunning() if self.reader_thread else False
        
        # 更可靠的连接状态检查：如果能发送数据，说明连接正常
        can_send_data = False
        if port_exists and port_open:
            try:
                # 检查串口是否可写（间接验证连接状态）
                can_send_data = self.serial_port.isWritable()
            except:
                can_send_data = False
        
        # 如果QSerialPort.isOpen()不准确，使用发送能力作为备用判断
        effective_port_open = port_open or can_send_data
        
        return (port_exists and effective_port_open and thread_exists and thread_running)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        stats = {
            "is_connected": self.is_connected(),
            "port_name": self.serial_port.portName() if self.serial_port else None,
            "baud_rate": self.serial_port.baudRate() if self.serial_port else None,
            "connection_attempts": self.connection_attempts,
            "success_rate": self.connection_success_rate,
            "last_connect_time": self.last_connect_time
        }
        
        # 添加读取线程性能统计
        if self.reader_thread:
            stats.update(self.reader_thread.get_performance_stats())
            
        return stats
        
    def on_error(self, error):
        """处理串口错误 - 简化版本"""
        # 过滤常见的非关键错误
        if error in [QSerialPort.SerialPortError.TimeoutError]:
            return
        
        error_string = f"串口错误: {self.serial_port.errorString()}"
        
        # 过滤"等待的操作过时"错误
        if "等待的操作过时" in error_string:
            return
        
        if self.debug_mode:
            print(f"[DEBUG] {error_string}")
        
        # 记录到监控系统（静默处理失败）
        if self.monitoring_system:
            try:
                self.monitoring_system.record_error(error)
            except:
                pass
        
        # 只对严重错误发出信号
        critical_errors = [
            QSerialPort.SerialPortError.ResourceError,
            QSerialPort.SerialPortError.PermissionError,
            QSerialPort.SerialPortError.DeviceNotFoundError,
            QSerialPort.SerialPortError.OpenError
        ]
        
        if error in critical_errors:
            self.error_occurred.emit(error_string)
        
    def _on_connection_stability_changed(self, is_stable: bool):
        """连接稳定性变化处理 - 简化版本"""
        # 简化连接状态检查逻辑，只记录关键状态变化
        if self.debug_mode and hasattr(self, '_last_connection_status'):
            if self._last_connection_status != is_stable:
                status = "稳定" if is_stable else "不稳定"
                print(f"[DEBUG] 连接状态变化: {status}")
                self._last_connection_status = is_stable
        elif not hasattr(self, '_last_connection_status'):
            self._last_connection_status = is_stable
            
        # 记录稳定性指标 - 降低频率
        if self.monitoring_system and is_stable != getattr(self, '_last_logged_status', None):
            self.monitoring_system.record_metric(
                MetricType.CONNECTION_STABILITY, 
                1 if is_stable else 0
            )
            self._last_logged_status = is_stable
            
    # 移除复杂的动态缓冲区调整逻辑，使用固定大小缓冲区
    
    def _on_buffer_overflow(self, buffer_size: int):
        """缓冲区溢出处理"""
        self.logger.warning(f"缓冲区溢出: {buffer_size} 字节")
        self.error_occurred.emit(f"缓冲区溢出: {buffer_size} 字节")
    
    def _process_send_queue(self):
        """处理发送队列（已禁用队列功能，仅清空可能残留的队列）"""
        try:
            # 如果队列中有残留数据，清空队列并记录警告
            if self._send_queue:
                queue_size = len(self._send_queue)
                if self.debug_mode:
                    print(f"[DEBUG] 清空残留的发送队列（{queue_size}个命令）")
                self._send_queue.clear()
                self.logger.warning(f"发送队列功能已禁用，清空{queue_size}个残留命令")
            self._queue_processing = False
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 清空发送队列时发生错误: {e}")
            self._queue_processing = False
        
    def reset_connection_stats(self):
        """重置连接统计"""
        self.connection_attempts = 0
        self.connection_success_rate = 0.0
        self.last_connect_time = None
    
    def reset_response_timeout(self):
        """重置响应超时检测"""
        if self.reader_thread:
            self.reader_thread.last_send_time = 0
            self.reader_thread.response_received = False
        self._last_command_hash = None
        
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled
        # 更新日志级别
        if enabled:
            self.logger.level = LogLevel.DEBUG
        else:
            self.logger.level = LogLevel.INFO
            
        if self.reader_thread:
            self.reader_thread.debug_mode = enabled
            self.reader_thread.logger.level = self.logger.level
    
    def __del__(self):
        """析构函数 - 确保资源正确释放"""
        try:
            if hasattr(self, 'serial_port') and self.serial_port:
                if self.serial_port.isOpen():
                    self.serial_port.close()
            if hasattr(self, 'reader_thread') and self.reader_thread:
                if self.reader_thread.isRunning():
                    self.reader_thread.running = False
                    self.reader_thread.wait(100)  # 短暂等待
        except Exception:
            pass  # 析构函数中忽略所有异常