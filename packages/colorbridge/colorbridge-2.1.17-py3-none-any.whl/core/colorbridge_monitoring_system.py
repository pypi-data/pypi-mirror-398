#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控系统模块 - ColorBridge
系统健康监控、性能指标追踪和智能预警
"""

import time
import threading
import psutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from .colorbridge_log_analyzer import LogAnalyzer, ErrorEvent, ErrorCategory, ErrorSeverity


# 常量定义
class MonitoringConstants:
    """监控系统常量"""
    NORMAL_THRESHOLD_BYTES_PER_SECOND = 1000  # 正常阈值：1000 bytes/s


class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"
    # 串口专用指标
    SERIAL_READ_RATE = "serial_read_rate"
    SERIAL_WRITE_RATE = "serial_write_rate"
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_CLOSED = "connection_closed"
    CONNECTION_STABILITY = "connection_stability"


@dataclass
class Metric:
    """监控指标"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """预警信息"""
    level: AlertLevel
    title: str
    message: str


@dataclass
class SystemHealth:
    """系统健康状态"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: float = 0.0
    process_count: int = 0
    thread_count: int = 0
    uptime: float = 0.0
    overall_status: str = "healthy"


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率（跨平台兼容）
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:\\')
            else:  # Unix/Linux
                disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = network.bytes_sent + network.bytes_recv
            
            # 进程数
            process_count = len(psutil.pids())
            
            # 线程数
            thread_count = sum(len(p.threads()) for p in psutil.process_iter(['threads']))
            
            # 运行时间
            uptime = time.time() - self.start_time
            
            # 整体状态评估
            overall_status = "healthy"
            if cpu_usage > 80 or memory_usage > 80 or disk_usage > 80:
                overall_status = "warning"
            if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
                overall_status = "critical"
            
            return SystemHealth(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                thread_count=thread_count,
                uptime=uptime,
                overall_status=overall_status
            )
            
        except Exception as e:
            return SystemHealth(
                overall_status="error",
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io=0.0,
                process_count=0,
                thread_count=0,
                uptime=0.0
            )
    timestamp: float = field(default_factory=time.time)
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    resolved: bool = False
    resolve_timestamp: Optional[float] = None


@dataclass
class SystemHealth:
    """系统健康状态"""
    overall_status: str  # healthy, warning, critical
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    uptime: float
    timestamp: float = field(default_factory=time.time)


class MetricCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(lambda: deque(maxlen=100))
        
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """增加计数器"""
        self.counters[name] += value
        self._record_metric(name, MetricType.COUNTER, self.counters[name], labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        self.gauges[name] = value
        self._record_metric(name, MetricType.GAUGE, value, labels)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图数据"""
        self.histograms[name].append(value)
        self._record_metric(name, MetricType.HISTOGRAM, value, labels)
    
    def _record_metric(self, name: str, metric_type: MetricType, value: float, labels: Dict[str, str] = None):
        """记录指标"""
        if labels is None:
            labels = {}
        
        metric = Metric(
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels
        )
        
        self.metrics[name].append(metric)
    
    def get_metric_value(self, name: str, metric_type: MetricType) -> Optional[float]:
        """获取指标值"""
        if metric_type == MetricType.COUNTER:
            return self.counters.get(name)
        elif metric_type == MetricType.GAUGE:
            return self.gauges.get(name)
        elif metric_type == MetricType.HISTOGRAM:
            values = list(self.histograms.get(name, []))
            return sum(values) / len(values) if values else None
        return None
    
    def get_metric_history(self, name: str, duration_seconds: int = 300) -> List[Metric]:
        """获取指标历史"""
        if name not in self.metrics:
            return []
        
        current_time = time.time()
        cutoff_time = current_time - duration_seconds
        
        return [m for m in self.metrics[name] if m.timestamp >= cutoff_time]


class AlertManager:
    """预警管理器"""
    
    def __init__(self):
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_callbacks = []
        
    def add_alert_rule(self, name: str, metric_name: str, condition: str, 
                      threshold: float, level: AlertLevel, message_template: str):
        """添加预警规则"""
        self.alert_rules[name] = {
            'metric_name': metric_name,
            'condition': condition,
            'threshold': threshold,
            'level': level,
            'message_template': message_template
        }
    
    def check_alerts(self, metrics: Dict[str, float]) -> List[Alert]:
        """检查预警条件"""
        new_alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            metric_value = metrics.get(rule['metric_name'])
            if metric_value is None:
                continue
            
            # 检查预警条件
            triggered = self._evaluate_condition(metric_value, rule['condition'], rule['threshold'])
            
            alert_key = f"{rule_name}_{rule['metric_name']}"
            
            if triggered and alert_key not in self.active_alerts:
                # 创建新预警
                alert = Alert(
                    level=rule['level'],
                    title=f"{rule_name} - {rule['metric_name']}",
                    message=rule['message_template'].format(
                        metric_name=rule['metric_name'],
                        threshold=rule['threshold'],
                        current_value=metric_value
                    ),
                    metric_name=rule['metric_name'],
                    threshold=rule['threshold'],
                    current_value=metric_value
                )
                
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                new_alerts.append(alert)
                
            elif not triggered and alert_key in self.active_alerts:
                # 解决预警
                alert = self.active_alerts[alert_key]
                alert.resolved = True
                alert.resolve_timestamp = time.time()
                
                del self.active_alerts[alert_key]
                self.alert_history.append(alert)
        
        return new_alerts
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估条件"""
        if condition == '>':
            return value > threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<':
            return value < threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return abs(value - threshold) < 0.001
        elif condition == '!=':
            return abs(value - threshold) >= 0.001
        return False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加预警回调"""
        self.alert_callbacks.append(callback)
    
    def trigger_callbacks(self, alerts: List[Alert]):
        """触发预警回调"""
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"[DEBUG] 预警回调异常: {e}")


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        
    def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率（跨平台兼容）
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:\\')
            else:  # Unix/Linux
                disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # 进程和线程数
            process_count = len(psutil.pids())
            thread_count = self.process.num_threads()
            
            # 运行时间
            uptime = time.time() - psutil.boot_time()
            
            # 确定整体状态
            if cpu_usage > 90 or memory_usage > 90 or disk_usage > 90:
                overall_status = "critical"
            elif cpu_usage > 70 or memory_usage > 70 or disk_usage > 70:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return SystemHealth(
                overall_status=overall_status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                thread_count=thread_count,
                uptime=uptime
            )
            
        except Exception as e:
            return SystemHealth(
                overall_status="error",
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                thread_count=0,
                uptime=0.0
            )


class MonitoringSystem(QObject):
    """实时监控系统（带递归保护）"""
    
    # 信号定义
    alert_triggered = pyqtSignal(Alert)
    metric_recorded = pyqtSignal(Metric)
    metric_updated = pyqtSignal(str, float)  # metric_name, value
    system_health_updated = pyqtSignal(SystemHealth)
    performance_report_generated = pyqtSignal(dict)
    
    def __init__(self, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        
        # 递归保护
        self._monitoring_lock = threading.RLock()
        self._recursion_depth = 0
        self._max_recursion_depth = 5
        self._last_alerts = {}  # 防重复预警
        self._alert_cooldown = 5.0  # 5秒预警冷却
        
        # 核心组件
        self.metric_collector = MetricCollector()
        self.log_analyzer = None  # 可选的日志分析器
        
        # 系统监控器
        self.system_monitor = SystemMonitor()
        
        # 预警管理器
        self.alert_manager = AlertManager()
        
        # 监控状态
        self.is_monitoring = False
        self.monitoring_interval = 1.0  # 1秒监控间隔
        self.start_time = time.time()
        
        # 预警规则
        self.alert_rules = self._setup_default_alert_rules()
        
        # 定时器
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self._monitoring_loop)
        
        # 健康检查定时器
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self._check_system_health)
        self.health_check_timer.start(30000)  # 30秒健康检查，减少CPU占用
        
        # 性能报告定时器
        self.report_timer = QTimer()
        self.report_timer.timeout.connect(self._generate_performance_report)
        self.report_timer.start(300000)  # 5分钟性能报告，减少CPU占用
    
    def _setup_default_alert_rules(self):
        """设置默认预警规则"""
        # CPU使用率预警
        self.alert_manager.add_alert_rule(
            name="CPU高使用率",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            level=AlertLevel.WARNING,
            message_template="CPU使用率过高: {current_value:.1f}% (阈值: {threshold}%)"
        )
        
        self.alert_manager.add_alert_rule(
            name="CPU严重使用率",
            metric_name="cpu_usage",
            condition=">",
            threshold=95.0,
            level=AlertLevel.CRITICAL,
            message_template="CPU使用率严重过高: {current_value:.1f}% (阈值: {threshold}%)"
        )
        
        # 内存使用率预警
        self.alert_manager.add_alert_rule(
            name="内存高使用率",
            metric_name="memory_usage",
            condition=">",
            threshold=80.0,
            level=AlertLevel.WARNING,
            message_template="内存使用率过高: {current_value:.1f}% (阈值: {threshold}%)"
        )
        
        # 错误率预警
        self.alert_manager.add_alert_rule(
            name="错误率过高",
            metric_name="error_rate",
            condition=">",
            threshold=0.1,  # 10%
            level=AlertLevel.ERROR,
            message_template="错误率过高: {current_value:.1%} (阈值: {threshold:.1%})"
        )
        
        # 消息处理延迟预警
        self.alert_manager.add_alert_rule(
            name="处理延迟过高",
            metric_name="processing_latency",
            condition=">",
            threshold=0.1,  # 100ms
            level=AlertLevel.WARNING,
            message_template="消息处理延迟过高: {current_value:.3f}s (阈值: {threshold}s)"
        )
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.start_time = time.time()
        
        # 启动定时器
        self.monitoring_timer.start(5000)  # 5秒收集指标，平衡监控和性能
        # health_check_timer和report_timer已在__init__中启动
        
        if self.debug_mode:
            print("[DEBUG] 监控系统已启动")
    
    def stop_monitoring(self):
        """停止监控（修复卡死问题的版本）"""
        try:
            if self.debug_mode:
                print("[DEBUG] 正在停止监控系统...")
            
            # 设置停止标志
            self.is_monitoring = False
            self._is_stopping = True
            self._monitoring_active = False  # 强制设置活动标志为False
            
            # 立即停止所有定时器，不等待
            try:
                if hasattr(self, 'monitoring_timer'):
                    self.monitoring_timer.stop()
                    self.monitoring_timer.deleteLater()  # 彻底删除定时器
                if hasattr(self, 'health_check_timer'):
                    self.health_check_timer.stop()
                    self.health_check_timer.deleteLater()
                if hasattr(self, 'report_timer'):
                    self.report_timer.stop()
                    self.report_timer.deleteLater()
            except Exception as timer_error:
                if self.debug_mode:
                    print(f"[DEBUG] 停止定时器失败: {timer_error}")
            
            # 不等待监控循环完成，直接清理资源
            # 这样可以避免程序关闭时卡死
            
            # 清理资源
            self._cleanup_monitoring_resources()
            
            if self.debug_mode:
                print("[DEBUG] 监控系统已强制停止")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 停止监控系统失败: {e}")
    
    def _cleanup_monitoring_resources(self):
        """清理监控资源"""
        try:
            # 清理指标收集器
            if hasattr(self, 'metric_collector'):
                self.metric_collector.metrics.clear()
            
            # 清理预警管理器
            if hasattr(self, 'alert_manager'):
                self.alert_manager.active_alerts.clear()
            
            # 清理系统监控器
            if hasattr(self, 'system_monitor'):
                # 重置系统监控器状态
                if hasattr(self.system_monitor, '_is_monitoring'):
                    self.system_monitor._is_monitoring = False
            
            # 重置停止标志
            self._is_stopping = False
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 清理监控资源失败: {e}")
    
    def _collect_metrics(self):
        """收集指标（带递归保护和停止检查）"""
        # 检查是否正在停止
        if hasattr(self, '_is_stopping') and self._is_stopping:
            return
        
        # 递归深度保护
        if self._recursion_depth >= self._max_recursion_depth:
            return
        
        # 设置活跃标志
        self._monitoring_active = True
        
        with self._monitoring_lock:
            self._recursion_depth += 1
            try:
                # 再次检查是否正在停止（可能在等待锁期间被设置）
                if hasattr(self, '_is_stopping') and self._is_stopping:
                    return
                
                # 收集系统指标（带超时保护）
                import time
                start_time = time.time()
                timeout = 0.5  # 最多等待0.5秒
                
                health = self.system_monitor.get_system_health()
                
                # 检查超时
                if time.time() - start_time > timeout:
                    if self.debug_mode:
                        print("[DEBUG] 系统健康检查超时")
                    return
                
                self.metric_collector.set_gauge("cpu_usage", health.cpu_usage, {"unit": "percent"})
                self.metric_collector.set_gauge("memory_usage", health.memory_usage, {"unit": "percent"})
                self.metric_collector.set_gauge("disk_usage", health.disk_usage, {"unit": "percent"})
                self.metric_collector.set_gauge("process_count", health.process_count)
                self.metric_collector.set_gauge("thread_count", health.thread_count)
                
                # 发出指标更新信号（快速检查停止状态）
                if not (hasattr(self, '_is_stopping') and self._is_stopping):
                    self.metric_updated.emit("cpu_usage", health.cpu_usage)
                    self.metric_updated.emit("memory_usage", health.memory_usage)
                
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 指标收集异常: {e}")
            finally:
                self._recursion_depth -= 1
                self._monitoring_active = False
    
    def _monitoring_loop(self):
        """监控主循环（带递归保护）"""
        if not self.is_monitoring:
            return
            
        # 递归深度保护
        if self._recursion_depth >= self._max_recursion_depth:
            if self.debug_mode:
                print(f"[DEBUG] 监控循环递归深度超限: {self._recursion_depth}")
            return
        
        with self._monitoring_lock:
            self._recursion_depth += 1
            try:
                # 收集指标
                self._collect_metrics()
                
                # 检查预警
                self._check_alerts()
                
                # 更新系统健康状态
                self._update_system_health()
                
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 监控循环异常: {e}")
            finally:
                self._recursion_depth -= 1
    
    def _check_alerts(self):
        """检查预警（带递归保护和防重复）"""
        import time
        
        # 递归深度保护
        if self._recursion_depth >= self._max_recursion_depth:
            return
        
        with self._monitoring_lock:
            self._recursion_depth += 1
            try:
                current_time = time.time()
                
                # 获取当前指标值
                current_metrics = {}
                
                for metric_name in ["cpu_usage", "memory_usage", "error_rate", "processing_latency"]:
                    value = self.metric_collector.get_metric_value(metric_name, MetricType.GAUGE)
                    if value is not None:
                        current_metrics[metric_name] = value
                
                # 检查预警
                new_alerts = self.alert_manager.check_alerts(current_metrics)
                
                # 过滤重复预警
                filtered_alerts = []
                for alert in new_alerts:
                    alert_key = f"{alert.level.value}_{alert.metric_name}"
                    
                    # 检查冷却时间
                    if alert_key in self._last_alerts:
                        if current_time - self._last_alerts[alert_key] < self._alert_cooldown:
                            continue  # 在冷却期内，跳过
                    
                    # 记录预警时间
                    self._last_alerts[alert_key] = current_time
                    filtered_alerts.append(alert)
                
                # 触发预警回调
                if filtered_alerts:
                    self.alert_manager.trigger_callbacks(filtered_alerts)
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 预警检查异常: {e}")
            finally:
                self._recursion_depth -= 1
    
    def _check_system_health(self):
        """检查系统健康状态（带递归保护）"""
        # 递归深度保护
        if self._recursion_depth >= self._max_recursion_depth:
            return
        
        with self._monitoring_lock:
            self._recursion_depth += 1
            try:
                # 更新系统健康状态
                self._update_system_health()
                
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 系统健康检查异常: {e}")
            finally:
                self._recursion_depth -= 1
    
    def _update_system_health(self):
        """更新系统健康状态"""
        try:
            health = self.system_monitor.get_system_health()
            self.system_health_updated.emit(health)
            
            # 记录健康状态指标
            self.metric_collector.set_gauge("system_health_score", 
                                          100 if health.overall_status == "healthy" else
                                          50 if health.overall_status == "warning" else 0)
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 系统健康更新异常: {e}")
    
    def _generate_performance_report(self):
        """生成性能报告"""
        try:
            uptime = time.time() - self.start_time
            
            # 定期执行内存清理，每100次报告（约8小时）执行一次
            report_count = getattr(self, '_report_count', 0) + 1
            self._report_count = report_count
            
            if report_count % 100 == 0:
                try:
                    import gc
                    gc.collect()
                    if self.debug_mode:
                        print("[DEBUG] 执行定期内存清理")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 内存清理失败: {e}")
            
            report = {
                'uptime': uptime,
                'timestamp': time.time(),
                'metrics_summary': self._get_metrics_summary(),
                'active_alerts': len(self.alert_manager.active_alerts),
                'total_alerts': len(self.alert_manager.alert_history),
                'system_health': self.system_monitor.get_system_health().__dict__
            }
            
            self.performance_report_generated.emit(report)
            
            if self.debug_mode:
                print(f"[DEBUG] 性能报告生成完成 (运行时间: {uptime:.1f}s)")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 性能报告生成异常: {e}")
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        for metric_name in ["cpu_usage", "memory_usage", "error_rate", "processing_latency"]:
            history = self.metric_collector.get_metric_history(metric_name, 300)  # 最近5分钟
            
            if history:
                values = [m.value for m in history]
                summary[metric_name] = {
                    'current': values[-1] if values else 0,
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return summary
    
    def _on_alert_triggered(self, alert: Alert):
        """预警触发回调"""
        self.alert_triggered.emit(alert)
        
        if self.debug_mode:
            print(f"[DEBUG] 预警触发: [{alert.level.value}] {alert.title} - {alert.message}")
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = None, 
                       labels: Dict[str, str] = None):
        """记录指标 - 兼容旧接口（优化版本）"""
        if metric_type is None:
            metric_type = MetricType.GAUGE
        
        # 智能指标记录，减少不必要的开销
        if not self._should_record_metric(name, value):
            return
        
        # 误报检测机制
        if self._is_false_positive(name, value, labels):
            if self.debug_mode:
                print(f"[DEBUG] 过滤性能监控误报: {name}={value}")
            return
        
        if metric_type == MetricType.COUNTER:
            self.metric_collector.increment_counter(name, value, labels)
        elif metric_type == MetricType.GAUGE:
            self.metric_collector.set_gauge(name, value, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self.metric_collector.record_histogram(name, value, labels)
    
    def _should_record_metric(self, metric_name: str, value: float) -> bool:
        """智能指标记录，减少不必要的开销"""
        # 只记录重要指标或变化显著的指标
        if metric_name in ['error_rate', 'cpu_usage', 'memory_usage']:
            return True
        
        # 对于其他指标，只记录变化超过10%的情况
        if not hasattr(self, '_last_metric_values'):
            self._last_metric_values = {}
            
        if metric_name in self._last_metric_values:
            last_value = self._last_metric_values[metric_name]
            if abs(value - last_value) / max(abs(last_value), 1) < 0.1:
                return False
        
        self._last_metric_values[metric_name] = value
        return True
    
    def record_custom_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                           labels: Dict[str, str] = None):
        """记录自定义指标"""
        self.record_metric(name, value, metric_type, labels)
    
    def _is_false_positive(self, metric_name: str, value: float, labels: Dict[str, str] = None) -> bool:
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
            r'测试时间'
        ]
        
        # 检查是否为硬件测试输出
        if labels and 'context' in labels:
            context = labels.get('context', '').lower()
            if any(pattern in context for pattern in ['mdu32', 'tfpu', 'hwtest', 'benchmark']):
                # 硬件测试期间，放宽性能阈值
                if metric_name in ['performance_low', 'data_receive_rate'] and value < MonitoringConstants.NORMAL_THRESHOLD_BYTES_PER_SECOND:
                    return True
                if metric_name == 'error_spike' and value < 5:  # 错误率小于5认为是正常的测试波动
                    return True
                if metric_name == 'buffer_overflow' and value < 3:  # 测试期间少量缓冲区溢出是正常的
                    return True
        
        # 检查恢复频率限制
        if metric_name == 'recovery_triggered':
            if not hasattr(self, '_recovery_timestamps'):
                self._recovery_timestamps = deque(maxlen=10)
            
            current_time = time.time()
            recent_recoveries = [t for t in self._recovery_timestamps if current_time - t < 300]  # 5分钟内
            if len(recent_recoveries) > 3:  # 5分钟内超过3次恢复，可能是误报
                return True
            
            self._recovery_timestamps.append(current_time)
        
        # 检查系统启动初期的误报
        if metric_name in ['cpu_usage', 'memory_usage']:
            if not hasattr(self, '_startup_time'):
                self._startup_time = time.time()
            
            if time.time() - self._startup_time < 30:  # 启动后30秒内
                if metric_name == 'cpu_usage' and value < 50:  # 启动期间CPU使用率较低是正常的
                    return True
                if metric_name == 'memory_usage' and value < 60:  # 启动期间内存使用率较低是正常的
                    return True
        
        # 新增：串口数据接收正常模式检测
        if metric_name == 'data_receive_rate':
            if not hasattr(self, '_data_receive_baseline'):
                self._data_receive_baseline = deque(maxlen=20)
            
            # 记录当前值作为基线
            self._data_receive_baseline.append(value)
            
            # 如果基线数据不足，不触发误报
            if len(self._data_receive_baseline) < 5:
                return False
            
            # 计算基线平均值
            baseline_avg = sum(self._data_receive_baseline) / len(self._data_receive_baseline)
            
            # 如果当前值在基线的合理范围内（±30%），认为是正常的
            if baseline_avg > 0 and abs(value - baseline_avg) / baseline_avg < 0.3:
                return True
        
        # 新增：错误率正常波动检测
        if metric_name == 'error_rate':
            if not hasattr(self, '_error_rate_history'):
                self._error_rate_history = deque(maxlen=30)
            
            self._error_rate_history.append(value)
            
            # 如果历史数据不足，不触发误报
            if len(self._error_rate_history) < 10:
                return False
            
            # 计算移动平均
            recent_avg = sum(list(self._error_rate_history)[-10:]) / 10
            
            # 如果当前值接近移动平均（±0.05），认为是正常的波动
            if abs(value - recent_avg) < 0.05:
                return True
        
        return False
        
        # 发出指标更新信号
        self.metric_updated.emit(name, value)
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """获取监控仪表板数据"""
        return {
            'system_health': self.system_monitor.get_system_health().__dict__,
            'metrics_summary': self._get_metrics_summary(),
            'active_alerts': [alert.__dict__ for alert in self.alert_manager.active_alerts.values()],
            'recent_alerts': [alert.__dict__ for alert in list(self.alert_manager.alert_history)[-10:]],
            'uptime': time.time() - self.start_time if self.is_monitoring else 0,
            'is_monitoring': self.is_monitoring
        }
    
    def add_custom_alert_rule(self, name: str, metric_name: str, condition: str, 
                            threshold: float, level: AlertLevel, message_template: str):
        """添加自定义预警规则"""
        self.alert_manager.add_alert_rule(name, metric_name, condition, threshold, level, message_template)
        
        if self.debug_mode:
            print(f"[DEBUG] 添加自定义预警规则: {name}")