#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析器模块 - ColorBridge
自动检测和分类错误，提供智能诊断和修复建议
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""
    SERIAL_CONNECTION = "serial_connection"
    MESSAGE_PROCESSING = "message_processing"
    BUFFER_MANAGEMENT = "buffer_management"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """错误事件"""
    timestamp: float
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    count: int = 1
    first_occurrence: float = field(init=False)
    
    def __post_init__(self):
        self.first_occurrence = self.timestamp


@dataclass
class LogAnalysis:
    """日志分析结果"""
    total_errors: int = 0
    error_counts: Dict[ErrorCategory, int] = field(default_factory=lambda: defaultdict(int))
    severity_counts: Dict[ErrorSeverity, int] = field(default_factory=lambda: defaultdict(int))
    recent_errors: List[ErrorEvent] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class LogPatternMatcher:
    """日志模式匹配器"""
    
    def __init__(self):
        # 定义错误模式
        self.error_patterns = {
            ErrorCategory.SERIAL_CONNECTION: [
                (r'SerialPortError\.(\w+)', ErrorSeverity.HIGH),
                (r'串口连接失败', ErrorSeverity.HIGH),
                # 只有在非正常关闭时的"串口已断开"才报错
                (r'串口已断开.*(?:错误|异常|失败)', ErrorSeverity.MEDIUM),
                (r'串口对象已被删除', ErrorSeverity.MEDIUM),
                (r'重试中.*\(\d+/\d+\)', ErrorSeverity.MEDIUM)
            ],
            
            ErrorCategory.MESSAGE_PROCESSING: [
                (r'消息处理错误.*(?:mdu32|tfpu)', ErrorSeverity.LOW),  # 测试命令错误降级
                (r'消息处理错误', ErrorSeverity.MEDIUM),  # 其他消息处理错误降级
                (r'响应数据处理错误', ErrorSeverity.MEDIUM),
                (r'过滤重复.*', ErrorSeverity.LOW)
                # 移除"检测到.*命令"和"消息处理完成"的误报匹配
            ],
            
            ErrorCategory.BUFFER_MANAGEMENT: [
                (r'缓冲区溢出', ErrorSeverity.HIGH),
                (r'清理超时的部分消息', ErrorSeverity.MEDIUM),
                (r'清理片段过多的部分消息', ErrorSeverity.MEDIUM),
                (r'智能清理缓冲区', ErrorSeverity.MEDIUM),
                (r'缓冲策略配置', ErrorSeverity.LOW)
            ],
            
            ErrorCategory.PERFORMANCE: [
                (r'数据过长.*字符', ErrorSeverity.MEDIUM),
                # 降低性能测试数据的误报 - 只有在明确包含"错误"、"失败"、"异常"时才报错
                (r'平均每次.*时钟周期.*(?:错误|失败|异常|error|fail|exception)', ErrorSeverity.MEDIUM)
                # 移除"性能统计.*bytes/s.*msg/s"和"接收速率.*bytes/s"的误报匹配
            ],
            
            ErrorCategory.SYSTEM: [
                # 移除所有系统日志的误报匹配，只保留真正的错误
                # 系统启动和正常操作日志不应该被标记为错误
            ]
        }
        
        # 定义问题模式
        self.problem_patterns = {
            'infinite_recursion': [
                r'重复.*重复.*重复',
                r'(过滤重复.*响应.*){3,}',
                r'(接收数据.*\.\.\.){10,}'
            ],
            'message_storm': [
                r'(接收数据.*\.\.\.){20,}',
                r'DEBUG.*接收数据.*DEBUG.*接收数据'
            ],
            'connection_instability': [
                r'(串口连接失败.*重试中){2,}',
                r'(串口连接成功.*串口已断开){2,}'
            ],
            'buffer_overflow': [
                r'(缓冲区溢出.*智能清理缓冲区){2,}',
                r'缓冲区大小.*\d+.*bytes'
            ]
        }
    
    def match_error(self, log_line: str) -> Optional[Tuple[ErrorCategory, ErrorSeverity]]:
        """匹配错误模式（带白名单保护）"""
        # 白名单：这些是正常的调试信息，不应该被标记为错误
        whitelist_patterns = [
            r'串口接收到原始数据',
            r'解析设备信息',
            r'DeviceInfoManager.*解析',
            r'SerialReaderThread.*串口接收到',
            r'DEBUG.*ColorBridge.*\[SerialReaderThread\]',
            r'DEBUG.*ColorBridge.*\[DeviceInfoManager\]',
            r'启动修复版本的串口读取线程',
            r'串口读取线程已结束',
            r'性能统计',
            r'接收速率',
            r'bytes/s',
            r'msg/s',
            r'检测到.*命令',
            r'消息处理完成',
            r'AutoInstaller',
            r'环境检测通过',
            r'启动.*窗口',
            r'发现串口'
        ]
        
        # 检查是否在白名单中
        for pattern in whitelist_patterns:
            if re.search(pattern, log_line, re.IGNORECASE):
                return None
        
        # 匹配错误模式
        for category, patterns in self.error_patterns.items():
            for pattern, severity in patterns:
                if re.search(pattern, log_line, re.IGNORECASE):
                    return category, severity
        return None
    
    def detect_problem_pattern(self, log_lines: List[str]) -> List[str]:
        """检测问题模式"""
        detected_patterns = []
        full_log = '\n'.join(log_lines)
        
        for pattern_name, patterns in self.problem_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_log, re.IGNORECASE | re.MULTILINE):
                    detected_patterns.append(pattern_name)
                    break
        
        return detected_patterns


class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)  # 保留最近1000个错误
        self.error_frequency = defaultdict(lambda: defaultdict(int))
        self.last_analysis_time = time.time()
        
    def analyze_error(self, error: ErrorEvent) -> Dict[str, Any]:
        """分析单个错误"""
        current_time = time.time()
        
        # 更新错误历史
        self.error_history.append(error)
        
        # 更新频率统计
        time_window = int((current_time // 60))  # 按分钟分组
        self.error_frequency[time_window][error.category] += 1
        
        # 检测错误趋势
        trend_analysis = self._analyze_trends()
        
        # 生成建议
        recommendations = self._generate_recommendations(error, trend_analysis)
        
        return {
            'trend_analysis': trend_analysis,
            'recommendations': recommendations,
            'error_frequency': dict(self.error_frequency[time_window])
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析错误趋势"""
        current_time = time.time()
        current_window = int((current_time // 60))
        
        # 统计最近5分钟的错误
        recent_counts = defaultdict(int)
        for i in range(5):
            window = current_window - i
            for category, count in self.error_frequency[window].items():
                recent_counts[category] += count
        
        # 检测上升趋势
        trends = {}
        for category in ErrorCategory:
            if category == ErrorCategory.UNKNOWN:
                continue
                
            recent_count = recent_counts[category]
            if recent_count > 10:
                trends[category] = "high_frequency"
            elif recent_count > 5:
                trends[category] = "medium_frequency"
            elif recent_count > 0:
                trends[category] = "low_frequency"
            else:
                trends[category] = "no_recent_errors"
        
        return trends
    
    def _generate_recommendations(self, error: ErrorEvent, trends: Dict[str, Any]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 基于错误类别的建议
        if error.category == ErrorCategory.SERIAL_CONNECTION:
            if "重试" in error.message:
                recommendations.append("检查串口连接稳定性，考虑增加重试间隔")
                recommendations.append("验证串口驱动程序是否正常工作")
            else:
                recommendations.append("检查串口权限和设备连接状态")
                recommendations.append("确认设备是否被其他程序占用")
        
        elif error.category == ErrorCategory.MESSAGE_PROCESSING:
            if "重复" in error.message:
                recommendations.append("优化消息去重算法，调整去重窗口时间")
                recommendations.append("检查消息处理器是否陷入循环")
            else:
                recommendations.append("增强消息处理异常处理机制")
                recommendations.append("添加消息处理超时保护")
        
        elif error.category == ErrorCategory.BUFFER_MANAGEMENT:
            recommendations.append("调整缓冲区大小配置")
            recommendations.append("优化缓冲区清理策略")
            recommendations.append("考虑实现分块处理机制")
        
        elif error.category == ErrorCategory.PERFORMANCE:
            # 优化性能错误检测，减少误报
            if "DEBUG" in error.message and "串口接收到原始数据" in error.message:
                # 这是正常的调试信息，不是性能问题
                recommendations.append("调试信息显示正常，无需处理")
            else:
                recommendations.append("监控性能指标，优化处理算法")
                recommendations.append("考虑实现异步处理机制")
        
        # 基于趋势的建议
        for category, trend in trends.items():
            if trend == "high_frequency":
                if category == ErrorCategory.SERIAL_CONNECTION:
                    recommendations.append("串口连接问题频发，建议检查硬件连接")
                elif category == ErrorCategory.MESSAGE_PROCESSING:
                    recommendations.append("消息处理问题频发，建议检查处理逻辑")
        
        return recommendations


class LogAnalyzer(QObject):
    """日志分析器主类"""
    
    # 信号定义
    error_detected = pyqtSignal(ErrorEvent)
    analysis_completed = pyqtSignal(LogAnalysis)
    recommendation_generated = pyqtSignal(list)
    
    def __init__(self, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        self.pattern_matcher = LogPatternMatcher()
        self.error_analyzer = ErrorAnalyzer()
        
        # 实时分析状态
        self.is_analyzing = False
        self.analysis_thread = None
        self.log_buffer = deque(maxlen=500)  # 保留最近500行日志
        
        # 分析配置
        self.analysis_interval = 30  # 30秒分析一次
        self.error_threshold = 5  # 5个同类错误触发警告
        
        # 统计信息
        self.total_lines_processed = 0
        self.total_errors_detected = 0
        self.start_time = time.time()
    
    def add_log_line(self, log_line: str):
        """添加日志行进行分析"""
        if not log_line or not log_line.strip():
            return
        
        self.total_lines_processed += 1
        self.log_buffer.append(log_line)
        
        # 实时错误检测
        error_info = self.pattern_matcher.match_error(log_line)
        if error_info:
            category, severity = error_info
            
            # 创建错误事件
            error_event = ErrorEvent(
                timestamp=time.time(),
                severity=severity,
                category=category,
                message=log_line.strip(),
                context={'line_number': self.total_lines_processed}
            )
            
            # 检查是否为重复错误
            self._check_duplicate_error(error_event)
            
            # 发出错误检测信号
            self.error_detected.emit(error_event)
            
            # 分析错误
            analysis = self.error_analyzer.analyze_error(error_event)
            
            # 发出建议信号
            if analysis['recommendations']:
                self.recommendation_generated.emit(analysis['recommendations'])
            
            self.total_errors_detected += 1
            
            if self.debug_mode:
                print(f"[DEBUG] 检测到错误: {category.value} - {severity.value}")
                print(f"[DEBUG] 错误消息: {log_line.strip()[:100]}...")
    
    def _check_duplicate_error(self, error: ErrorEvent):
        """检查重复错误并更新计数"""
        # 查找最近的相似错误
        for recent_error in list(self.error_analyzer.error_history)[-10:]:
            if (recent_error.category == error.category and 
                recent_error.severity == error.severity and
                abs(recent_error.timestamp - error.timestamp) < 5.0):  # 5秒内
                
                # 检查消息相似度
                if self._calculate_similarity(recent_error.message, error.message) > 0.8:
                    error.count = recent_error.count + 1
                    error.first_occurrence = recent_error.first_occurrence
                    break
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的相似度计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def start_realtime_analysis(self):
        """启动实时分析"""
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        if self.debug_mode:
            print("[DEBUG] 启动实时日志分析")
    
    def stop_realtime_analysis(self):
        """停止实时分析（修复卡死问题）"""
        self.is_analyzing = False
        if self.analysis_thread:
            # 不等待线程完成，直接设置daemon=True让程序退出时自动清理
            # 这样可以避免程序关闭时因等待分析线程而卡死
            try:
                if self.analysis_thread.is_alive():
                    # 只等待很短时间，不阻塞程序关闭
                    self.analysis_thread.join(timeout=0.1)
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 停止分析线程失败: {e}")
        
        if self.debug_mode:
            print("[DEBUG] 停止实时日志分析")
    
    def _analysis_loop(self):
        """分析循环"""
        while self.is_analyzing:
            try:
                # 执行周期性分析
                analysis = self.perform_analysis()
                
                if analysis.total_errors > 0:
                    self.analysis_completed.emit(analysis)
                
                # 等待下次分析
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 分析循环错误: {e}")
                time.sleep(5)  # 错误后等待5秒
    
    def perform_analysis(self) -> LogAnalysis:
        """执行完整的日志分析"""
        analysis = LogAnalysis()
        
        # 获取最近的日志行
        recent_logs = list(self.log_buffer)
        
        # 检测问题模式
        analysis.patterns = self.pattern_matcher.detect_problem_pattern(recent_logs)
        
        # 统计错误信息
        for error in self.error_analyzer.error_history:
            analysis.error_counts[error.category] += error.count
            analysis.severity_counts[error.severity] += error.count
            analysis.total_errors += error.count
        
        # 获取最近的错误
        analysis.recent_errors = list(self.error_analyzer.error_history)[-10:]
        
        # 生成综合建议
        analysis.recommendations = self._generate_comprehensive_recommendations(analysis)
        
        return analysis
    
    def _generate_comprehensive_recommendations(self, analysis: LogAnalysis) -> List[str]:
        """生成综合修复建议"""
        recommendations = []
        
        # 基于错误总数的建议
        if analysis.total_errors > 50:
            recommendations.append("错误数量过多，建议立即检查系统状态")
        elif analysis.total_errors > 20:
            recommendations.append("错误数量较多，建议关注系统稳定性")
        
        # 基于错误类别的建议
        for category, count in analysis.error_counts.items():
            if count > 10:
                if category == ErrorCategory.SERIAL_CONNECTION:
                    recommendations.append("串口连接问题严重，建议检查硬件和驱动")
                elif category == ErrorCategory.MESSAGE_PROCESSING:
                    recommendations.append("消息处理问题频发，建议优化处理逻辑")
                elif category == ErrorCategory.BUFFER_MANAGEMENT:
                    recommendations.append("缓冲区管理问题，建议调整配置参数")
        
        # 基于问题模式的建议
        if 'infinite_recursion' in analysis.patterns:
            recommendations.append("检测到无限递归模式，建议添加递归深度限制")
        
        if 'message_storm' in analysis.patterns:
            recommendations.append("检测到消息风暴，建议实现流量控制机制")
        
        if 'connection_instability' in analysis.patterns:
            recommendations.append("检测到连接不稳定，建议增强重连机制")
        
        if 'buffer_overflow' in analysis.patterns:
            recommendations.append("检测到缓冲区溢出，建议优化内存管理")
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        elapsed_time = time.time() - self.start_time
        
        return {
            'total_lines_processed': self.total_lines_processed,
            'total_errors_detected': self.total_errors_detected,
            'analysis_runtime': elapsed_time,
            'lines_per_second': self.total_lines_processed / elapsed_time if elapsed_time > 0 else 0,
            'errors_per_minute': (self.total_errors_detected / elapsed_time) * 60 if elapsed_time > 0 else 0,
            'buffer_size': len(self.log_buffer),
            'is_analyzing': self.is_analyzing
        }
    
    def export_analysis_report(self, filename: str = None) -> str:
        """导出分析报告"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"colorbridge_log_analysis_{timestamp}.txt"
        
        analysis = self.perform_analysis()
        stats = self.get_statistics()
        
        report = f"""
ColorBridge 日志分析报告
========================

生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

统计信息:
- 总处理行数: {stats['total_lines_processed']}
- 总检测错误: {stats['total_errors_detected']}
- 分析运行时间: {stats['analysis_runtime']:.2f}秒
- 处理速度: {stats['lines_per_second']:.2f}行/秒
- 错误频率: {stats['errors_per_minute']:.2f}错误/分钟

错误统计:
"""
        
        for category, count in analysis.error_counts.items():
            report += f"- {category.value}: {count}次\n"
        
        report += "\n严重程度统计:\n"
        for severity, count in analysis.severity_counts.items():
            report += f"- {severity.value}: {count}次\n"
        
        if analysis.patterns:
            report += "\n检测到的问题模式:\n"
            for pattern in analysis.patterns:
                report += f"- {pattern}\n"
        
        if analysis.recommendations:
            report += "\n修复建议:\n"
            for i, rec in enumerate(analysis.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        if analysis.recent_errors:
            report += "\n最近的错误事件:\n"
            for error in analysis.recent_errors[-5:]:  # 只显示最近5个
                report += f"- [{error.severity.value}] {error.category.value}: {error.message[:80]}...\n"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            if self.debug_mode:
                print(f"[DEBUG] 分析报告已导出: {filename}")
            
            return filename
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 导出报告失败: {e}")
            return None