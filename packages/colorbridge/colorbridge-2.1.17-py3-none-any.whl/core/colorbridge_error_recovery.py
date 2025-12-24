#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误恢复机制模块 - ColorBridge
智能错误恢复和系统自愈功能
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import gc
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from .colorbridge_log_analyzer import ErrorEvent, ErrorCategory, ErrorSeverity


class RecoveryAction(Enum):
    """恢复动作类型"""
    RESET_COMPONENT = "reset_component"
    RESTART_CONNECTION = "restart_connection"
    CLEAR_BUFFER = "clear_buffer"
    ADJUST_PARAMETERS = "adjust_parameters"
    GARBAGE_COLLECT = "garbage_collect"
    EMERGENCY_STOP = "emergency_stop"
    RETRY_OPERATION = "retry_operation"
    FALLBACK_MODE = "fallback_mode"


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    name: str
    actions: List[RecoveryAction]
    max_retries: int = 3
    retry_delay: float = 1.0
    cooldown_period: float = 30.0
    success_rate: float = 0.0
    total_attempts: int = 0
    successful_attempts: int = 0


@dataclass
class RecoveryResult:
    """恢复结果"""
    strategy_name: str
    success: bool
    actions_taken: List[RecoveryAction]
    duration: float
    error_message: Optional[str] = None
    retry_count: int = 0


class SimpleRecursionGuard:
    """简化的递归保护器"""
    
    def __init__(self, max_depth: int = 20):
        self.max_depth = max_depth
        self.call_count = 0
        self.last_reset_time = time.time()
        self.reset_interval = 30  # 30秒重置计数器
        
    def check_recursion(self, function_name: str) -> bool:
        """检查递归深度，返回True表示安全，False表示超出限制"""
        current_time = time.time()
        
        # 定期重置计数器
        if current_time - self.last_reset_time > self.reset_interval:
            self.call_count = 0
            self.last_reset_time = current_time
        
        self.call_count += 1
        
        # 简单的深度检查
        if self.call_count > self.max_depth:
            return False
        
        return True
    
    def reset(self):
        """重置计数器"""
        self.call_count = 0
        self.last_reset_time = time.time()


class MessageStormDetector:
    """消息风暴检测器"""
    
    def __init__(self, threshold_messages_per_second: int = 50, window_size: int = 5):
        self.threshold = threshold_messages_per_second
        self.window_size = window_size
        self.message_timestamps = deque(maxlen=self.threshold * self.window_size)
        self.lock = threading.Lock()
        self.storm_detected = False
        self.storm_start_time = None
        
    def add_message(self):
        """添加消息记录"""
        with self.lock:
            current_time = time.time()
            self.message_timestamps.append(current_time)
            
            # 检测消息风暴
            recent_messages = [t for t in self.message_timestamps 
                             if current_time - t < self.window_size]
            
            messages_per_second = len(recent_messages) / self.window_size
            
            if messages_per_second > self.threshold:
                if not self.storm_detected:
                    self.storm_detected = True
                    self.storm_start_time = current_time
                    return True  # 风暴开始
            else:
                if self.storm_detected:
                    self.storm_detected = False
                    self.storm_start_time = None
                    return False  # 风暴结束
            
            return None  # 状态无变化
    
    def is_storm_active(self) -> bool:
        """检查是否处于消息风暴状态"""
        return self.storm_detected
    
    def get_storm_duration(self) -> float:
        """获取风暴持续时间"""
        if self.storm_start_time:
            return time.time() - self.storm_start_time
        return 0.0


class ConnectionStabilityMonitor:
    """连接稳定性监控器"""
    
    def __init__(self, instability_threshold: int = 3, monitoring_window: int = 60):
        self.instability_threshold = instability_threshold
        self.monitoring_window = monitoring_window
        self.connection_events = deque(maxlen=100)
        self.lock = threading.Lock()
        
    def record_connection_event(self, connected: bool):
        """记录连接事件"""
        with self.lock:
            current_time = time.time()
            self.connection_events.append((current_time, connected))
    
    def is_connection_unstable(self) -> bool:
        """检查连接是否不稳定"""
        with self.lock:
            if not self.connection_events:
                return False
            
            current_time = time.time()
            recent_events = [(t, c) for t, c in self.connection_events 
                           if current_time - t < self.monitoring_window]
            
            # 统计断开连接次数
            disconnections = sum(1 for _, connected in recent_events if not connected)
            
            return disconnections >= self.instability_threshold
    
    def get_connection_uptime(self) -> float:
        """获取连接正常运行时间百分比"""
        with self.lock:
            if not self.connection_events:
                return 0.0
            
            current_time = time.time()
            recent_events = [(t, c) for t, c in self.connection_events 
                           if current_time - t < self.monitoring_window]
            
            if len(recent_events) < 2:
                return 100.0 if recent_events and recent_events[0][1] else 0.0
            
            total_time = 0.0
            uptime = 0.0
            
            for i in range(len(recent_events) - 1):
                time_diff = recent_events[i + 1][0] - recent_events[i][0]
                total_time += time_diff
                if recent_events[i][1]:  # 如果是连接状态
                    uptime += time_diff
            
            return (uptime / total_time * 100.0) if total_time > 0 else 0.0


class RecoveryActionExecutor:
    """恢复动作执行器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.action_handlers = {
            RecoveryAction.RESET_COMPONENT: self._reset_component,
            RecoveryAction.RESTART_CONNECTION: self._restart_connection,
            RecoveryAction.CLEAR_BUFFER: self._clear_buffer,
            RecoveryAction.ADJUST_PARAMETERS: self._adjust_parameters,
            RecoveryAction.GARBAGE_COLLECT: self._garbage_collect,
            RecoveryAction.EMERGENCY_STOP: self._emergency_stop,
            RecoveryAction.RETRY_OPERATION: self._retry_operation,
            RecoveryAction.FALLBACK_MODE: self._fallback_mode
        }
        self.component_callbacks = {}
        
    def register_component_callback(self, action: RecoveryAction, callback: Callable):
        """注册组件回调"""
        self.component_callbacks[action] = callback
    
    def execute_action(self, action: RecoveryAction, context: Dict[str, Any] = None) -> bool:
        """执行恢复动作"""
        if context is None:
            context = {}
        
        try:
            if action in self.component_callbacks:
                return self.component_callbacks[action](context)
            else:
                return self.action_handlers[action](context)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 执行恢复动作失败 {action.value}: {e}")
            return False
    
    def _reset_component(self, context: Dict[str, Any]) -> bool:
        """重置组件"""
        component_name = context.get('component_name', 'unknown')
        if self.debug_mode:
            print(f"[DEBUG] 重置组件: {component_name}")
        
        # 通用重置逻辑
        time.sleep(0.1)  # 短暂等待
        return True
    
    def _restart_connection(self, context: Dict[str, Any]) -> bool:
        """重启连接"""
        if self.debug_mode:
            print("[DEBUG] 重启连接")
        
        # 等待连接稳定
        time.sleep(2.0)
        return True
    
    def _clear_buffer(self, context: Dict[str, Any]) -> bool:
        """清理缓冲区"""
        buffer_name = context.get('buffer_name', 'unknown')
        if self.debug_mode:
            print(f"[DEBUG] 清理缓冲区: {buffer_name}")
        
        return True
    
    def _adjust_parameters(self, context: Dict[str, Any]) -> bool:
        """调整参数"""
        adjustments = context.get('adjustments', {})
        if self.debug_mode:
            print(f"[DEBUG] 调整参数: {adjustments}")
        
        return True
    
    def _garbage_collect(self, context: Dict[str, Any]) -> bool:
        """垃圾回收"""
        if self.debug_mode:
            print("[DEBUG] 执行垃圾回收")
        
        gc.collect()
        return True
    
    def _emergency_stop(self, context: Dict[str, Any]) -> bool:
        """紧急停止"""
        if self.debug_mode:
            print("[DEBUG] 紧急停止")
        
        return True
    
    def _retry_operation(self, context: Dict[str, Any]) -> bool:
        """重试操作"""
        operation = context.get('operation', 'unknown')
        if self.debug_mode:
            print(f"[DEBUG] 重试操作: {operation}")
        
        return True
    
    def _fallback_mode(self, context: Dict[str, Any]) -> bool:
        """降级模式"""
        if self.debug_mode:
            print("[DEBUG] 切换到降级模式")
        
        return True


class ErrorRecoveryManager(QObject):
    """错误恢复管理器"""
    
    # 信号定义
    recovery_started = pyqtSignal(str)  # strategy_name
    recovery_completed = pyqtSignal(RecoveryResult)
    recovery_failed = pyqtSignal(str, str)  # strategy_name, error_message
    emergency_stop_triggered = pyqtSignal()
    
    def __init__(self, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        
        # 初始化组件（使用简化的递归保护）
        self.recursion_guard = SimpleRecursionGuard()
        self.storm_detector = MessageStormDetector()
        self.connection_monitor = ConnectionStabilityMonitor()
        self.action_executor = RecoveryActionExecutor(debug_mode)
        
        # 恢复策略
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.strategy_cooldowns = defaultdict(float)
        
        # 统计信息
        self.recovery_history = deque(maxlen=100)
        self.active_recoveries = {}
        
        # 定时器
        self.cooldown_timer = QTimer()
        self.cooldown_timer.timeout.connect(self._update_cooldowns)
        self.cooldown_timer.start(5000)  # 每5秒检查一次冷却时间
        
        if self.debug_mode:
            print("[DEBUG] 错误恢复管理器已初始化")
    
    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, List[RecoveryStrategy]]:
        """初始化恢复策略"""
        strategies = {
            ErrorCategory.SERIAL_CONNECTION: [
                RecoveryStrategy(
                    name="serial_basic_recovery",
                    actions=[RecoveryAction.RETRY_OPERATION, RecoveryAction.RESTART_CONNECTION],
                    max_retries=3,
                    retry_delay=2.0
                ),
                RecoveryStrategy(
                    name="serial_advanced_recovery",
                    actions=[RecoveryAction.CLEAR_BUFFER, RecoveryAction.ADJUST_PARAMETERS, 
                            RecoveryAction.RESTART_CONNECTION],
                    max_retries=2,
                    retry_delay=5.0
                )
            ],
            
            ErrorCategory.MESSAGE_PROCESSING: [
                RecoveryStrategy(
                    name="message_basic_recovery",
                    actions=[RecoveryAction.RESET_COMPONENT, RecoveryAction.CLEAR_BUFFER],
                    max_retries=2,
                    retry_delay=1.0
                ),
                RecoveryStrategy(
                    name="message_advanced_recovery",
                    actions=[RecoveryAction.GARBAGE_COLLECT, RecoveryAction.RESET_COMPONENT,
                            RecoveryAction.FALLBACK_MODE],
                    max_retries=1,
                    retry_delay=3.0
                )
            ],
            
            ErrorCategory.BUFFER_MANAGEMENT: [
                RecoveryStrategy(
                    name="buffer_recovery",
                    actions=[RecoveryAction.CLEAR_BUFFER, RecoveryAction.ADJUST_PARAMETERS],
                    max_retries=3,
                    retry_delay=1.0
                )
            ],
            
            ErrorCategory.PERFORMANCE: [
                RecoveryStrategy(
                    name="performance_recovery",
                    actions=[RecoveryAction.GARBAGE_COLLECT, RecoveryAction.ADJUST_PARAMETERS],
                    max_retries=2,
                    retry_delay=2.0
                )
            ]
        }
        
        return strategies
    
    def handle_error(self, error: ErrorEvent) -> bool:
        """处理错误，尝试自动恢复 - 增强误报检测"""
        # 误报检测机制
        if self._is_false_positive(error):
            if self.debug_mode:
                print(f"[DEBUG] 过滤错误恢复误报: {error.category.value} - {error.message}")
            return True  # 返回True表示不需要恢复
        
        # 检查是否需要立即紧急停止
        if error.severity == ErrorSeverity.CRITICAL:
            return self._emergency_recovery(error)
        
        # 检查递归保护
        try:
            # 简化的递归检查
            if not self.recursion_guard.check_recursion(f"handle_error_{error.category.value}"):
                if self.debug_mode:
                    print(f"[DEBUG] 递归深度超限，跳过错误处理: {error.category.value}")
                return False
        except (RecursionError, RuntimeError) as e:
            if self.debug_mode:
                print(f"[DEBUG] 检测到递归问题: {e}")
            return self._emergency_recovery(error)
        
        try:
            # 获取适用的恢复策略
            strategies = self.recovery_strategies.get(error.category, [])
            
            for strategy in strategies:
                if self._can_execute_strategy(strategy):
                    result = self._execute_recovery_strategy(strategy, error)
                    
                    if result.success:
                        self._update_strategy_success(strategy, True)
                        return True
                    else:
                        self._update_strategy_success(strategy, False)
            
            return False
            
        finally:
            # 简化的递归保护不需要显式退出
            pass
    
    def _is_false_positive(self, error: ErrorEvent) -> bool:
        """检测是否为误报（增强版本）"""
        import re
        
        # 硬件测试相关的误报模式
        hardware_test_patterns = [
            r'平均每次: \d+\.?\d* 时钟周期',
            r'MDU32测试完成',
            r'TFPU测试完成',
            r'硬件加速测试完成',
            r'性能基准测试完成',
            r'接收数据: 平均每次: \d+\.?\d* 时钟周期',
            r'测试完成！',
            r'所有计算均为实时执行',
            r'性能对比',
            r'测试汇总',
            r'测试时间',
            r'平均性能',
            r'测试结果'
        ]
        
        # 设备信息解析相关的误报模式
        device_info_patterns = [
            r'设备信息解析.*错误',
            r'消息处理错误.*mdu32',
            r'消息处理错误.*tfpu',
            r'AttributeError.*device_info',
            r'KeyError.*device_info',
            r'ValueError.*device_info',
            r'message_processing.*low',
            r'检测到错误.*message_processing.*low'
        ]
        
        # 检查错误消息是否匹配硬件测试模式
        for pattern in hardware_test_patterns:
            if re.search(pattern, error.message):
                return True
        
        # 检查设备信息解析相关的误报
        for pattern in device_info_patterns:
            if re.search(pattern, error.message):
                # 设备信息解析错误通常是临时的，降低严重级别
                if error.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
                    return True
        
        # 检查恢复频率限制
        if not hasattr(self, '_recovery_history'):
            self._recovery_history = deque(maxlen=20)
        
        current_time = time.time()
        recent_recoveries = [t for t in self._recovery_history if current_time - t < 300]  # 5分钟内
        if len(recent_recoveries) > 5:  # 5分钟内超过5次恢复，可能是误报
            return True
        
        # 检查上下文信息
        if error.context and 'command_context' in error.context:
            command_context = error.context.get('command_context', '').lower()
            if any(cmd in command_context for cmd in ['mdu32', 'tfpu', 'hwtest', 'benchmark']):
                # 硬件测试期间，放宽错误检测
                if error.category == ErrorCategory.PERFORMANCE and error.severity != ErrorSeverity.CRITICAL:
                    return True
                # 缓冲区管理问题在测试期间也是正常的
                if error.category == ErrorCategory.BUFFER_MANAGEMENT and error.severity != ErrorSeverity.CRITICAL:
                    return True
        
        # 检查系统启动初期的误报
        if not hasattr(self, '_startup_time'):
            self._startup_time = time.time()
        
        if time.time() - self._startup_time < 60:  # 启动后60秒内
            # 启动期间的串口连接问题可能是正常的
            if error.category == ErrorCategory.SERIAL_CONNECTION and error.severity != ErrorSeverity.CRITICAL:
                if 'OpenError' in error.message or '连接失败' in error.message:
                    return True
        
        return False
    
    def _can_execute_strategy(self, strategy: RecoveryStrategy) -> bool:
        """检查是否可以执行策略"""
        current_time = time.time()
        last_execution = self.strategy_cooldowns.get(strategy.name, 0)
        
        return (current_time - last_execution) >= strategy.cooldown_period
    
    def _execute_recovery_strategy(self, strategy: RecoveryStrategy, error: ErrorEvent) -> RecoveryResult:
        """执行恢复策略"""
        start_time = time.time()
        actions_taken = []
        
        self.recovery_started.emit(strategy.name)
        
        if self.debug_mode:
            print(f"[DEBUG] 开始执行恢复策略: {strategy.name}")
        
        for attempt in range(strategy.max_retries):
            try:
                # 执行所有动作
                success = True
                for action in strategy.actions:
                    if not self.action_executor.execute_action(action, {'error': error}):
                        success = False
                        break
                    actions_taken.append(action)
                
                if success:
                    duration = time.time() - start_time
                    result = RecoveryResult(
                        strategy_name=strategy.name,
                        success=True,
                        actions_taken=actions_taken,
                        duration=duration,
                        retry_count=attempt
                    )
                    
                    self.recovery_completed.emit(result)
                    self.recovery_history.append(result)
                    
                    if self.debug_mode:
                        print(f"[DEBUG] 恢复策略成功: {strategy.name} (耗时: {duration:.2f}s)")
                    
                    return result
                
                # 如果失败，等待重试
                if attempt < strategy.max_retries - 1:
                    time.sleep(strategy.retry_delay)
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 恢复策略执行异常: {e}")
        
        # 所有重试都失败
        duration = time.time() - start_time
        result = RecoveryResult(
            strategy_name=strategy.name,
            success=False,
            actions_taken=actions_taken,
            duration=duration,
            error_message=f"所有{strategy.max_retries}次重试均失败",
            retry_count=strategy.max_retries - 1
        )
        
        self.recovery_failed.emit(strategy.name, result.error_message)
        self.recovery_history.append(result)
        
        if self.debug_mode:
            print(f"[DEBUG] 恢复策略失败: {strategy.name}")
        
        return result
    
    def _emergency_recovery(self, error: ErrorEvent) -> bool:
        """紧急恢复"""
        if self.debug_mode:
            print(f"[DEBUG] 执行紧急恢复: {error.category.value}")
        
        # 执行紧急恢复动作
        emergency_actions = [
            RecoveryAction.GARBAGE_COLLECT,
            RecoveryAction.CLEAR_BUFFER,
            RecoveryAction.EMERGENCY_STOP
        ]
        
        success_count = 0
        for action in emergency_actions:
            try:
                if self.action_executor.execute_action(action, {'error': error}):
                    success_count += 1
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 紧急恢复动作失败 {action.value}: {e}")
        
        self.emergency_stop_triggered.emit()
        
        return success_count > 0
    
    def _update_strategy_success(self, strategy: RecoveryStrategy, success: bool):
        """更新策略成功率"""
        strategy.total_attempts += 1
        if success:
            strategy.successful_attempts += 1
        
        strategy.success_rate = strategy.successful_attempts / strategy.total_attempts
        
        # 设置冷却时间
        self.strategy_cooldowns[strategy.name] = time.time()
    
    def _update_cooldowns(self):
        """更新冷却时间"""
        current_time = time.time()
        expired_strategies = []
        
        for strategy_name, last_execution in self.strategy_cooldowns.items():
            # 找到对应的策略
            for strategies in self.recovery_strategies.values():
                for strategy in strategies:
                    if strategy.name == strategy_name:
                        if (current_time - last_execution) >= strategy.cooldown_period:
                            expired_strategies.append(strategy_name)
                        break
        
        # 清理过期的冷却记录
        for strategy_name in expired_strategies:
            del self.strategy_cooldowns[strategy_name]
    
    def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        health_status = {
            'overall_health': 'good',
            'issues': [],
            'recommendations': []
        }
        
        # 检查消息风暴
        if self.storm_detector.is_storm_active():
            storm_duration = self.storm_detector.get_storm_duration()
            health_status['issues'].append(f"消息风暴持续 {storm_duration:.1f} 秒")
            health_status['recommendations'].append("启用流量控制机制")
            health_status['overall_health'] = 'poor'
        
        # 检查连接稳定性
        if self.connection_monitor.is_connection_unstable():
            uptime = self.connection_monitor.get_connection_uptime()
            health_status['issues'].append(f"连接不稳定，正常运行时间 {uptime:.1f}%")
            health_status['recommendations'].append("检查串口连接和驱动")
            if health_status['overall_health'] == 'good':
                health_status['overall_health'] = 'fair'
        
        # 检查恢复成功率
        recent_recoveries = list(self.recovery_history)[-10:]
        if recent_recoveries:
            success_rate = sum(1 for r in recent_recoveries if r.success) / len(recent_recoveries)
            if success_rate < 0.5:
                health_status['issues'].append(f"恢复成功率低: {success_rate:.1%}")
                health_status['recommendations'].append("检查恢复策略配置")
                health_status['overall_health'] = 'poor'
        
        return health_status
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r.success)
        
        strategy_stats = {}
        for strategies in self.recovery_strategies.values():
            for strategy in strategies:
                if strategy.total_attempts > 0:
                    strategy_stats[strategy.name] = {
                        'attempts': strategy.total_attempts,
                        'successes': strategy.successful_attempts,
                        'success_rate': strategy.success_rate
                    }
        
        return {
            'total_recoveries': total_recoveries,
            'successful_recoveries': successful_recoveries,
            'overall_success_rate': successful_recoveries / total_recoveries if total_recoveries > 0 else 0,
            'strategy_statistics': strategy_stats,
            'active_cooldowns': len(self.strategy_cooldowns)
        }
    
    def register_component_callback(self, action: RecoveryAction, callback: Callable):
        """注册组件回调"""
        self.action_executor.register_component_callback(action, callback)
        if self.debug_mode:
            print(f"[DEBUG] 注册组件回调: {action.value}")