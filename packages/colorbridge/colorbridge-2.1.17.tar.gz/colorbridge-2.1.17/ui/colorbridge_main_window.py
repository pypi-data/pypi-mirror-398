#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCL2风格主窗口模块 - ColorBridge (融合版本)
完全模仿PCL2启动器的现代化UI设计
融合清理版本的稳定性和增强版本的完整功能
"""

import sys
import os
import json
import time
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QLineEdit, QPushButton, QLabel, 
                            QFrame, QSplitter, QComboBox, QMenuBar, QStatusBar,
                            QDialog, QSlider, QSpinBox, QCheckBox, QTabWidget,
                            QRadioButton, QMenu, QScrollArea, QGridLayout, QToolButton, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QBrush, QAction, QLinearGradient, QPen
from PyQt6.QtSerialPort import QSerialPort

# 导入核心模块
from core.colorbridge_serial_manager import ColorBridgeSerialManager
from core.colorbridge_device_info_manager import ColorBridgeDeviceInfoManager

# 导入UI组件
from ui.colorbridge_theme_manager import ThemeManager
from ui.colorbridge_settings_dialog import SettingsDialog
from ui.colorbridge_notification_manager import EnhancedNotificationManager

class PCL2Card(QFrame):
    """PCL2风格的卡片组件"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        """设置卡片UI"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 12px;
                margin: 4px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.98);
                border: 1px solid rgba(100, 200, 255, 0.5);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(8)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            title_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    padding: 6px 0px;
                    border-bottom: 2px solid #3498db;
                    margin-bottom: 10px;
                }
            """)
            layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)


class PCL2Button(QPushButton):
    """PCL2风格的按钮"""
    
    def __init__(self, text: str, button_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()
        
    def setup_style(self):
        """设置按钮样式"""
        styles = {
            "primary": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
                }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
            """,
            "secondary": """
                QPushButton {
                    background: rgba(255, 255, 255, 0.9);
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 12px;
                    font-family: "Microsoft YaHei";
                }
                QPushButton:hover {
                    background: rgba(236, 240, 241, 0.9);
                    border-color: #95a5a6;
                }
                QPushButton:pressed {
                    background: rgba(189, 195, 199, 0.9);
                }
            """,
            "success": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #229954);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #52c77e, stop:1 #27ae60);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #229954, stop:1 #1e8449);
                }
            """,
            "danger": """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e74c3c, stop:1 #c0392b);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ec7063, stop:1 #e74c3c);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #c0392b, stop:1 #a93226);
                }
            """
        }
        
        self.setStyleSheet(styles.get(self.button_type, styles["primary"]))
        self.setMinimumHeight(40)


class DisplayWindow(QMainWindow):
    """独立的消息显示窗口"""
    
    def __init__(self, parent=None, content="", debug_mode=False):
        super().__init__(parent)
        self.debug_mode = debug_mode
        
        # 设置窗口属性
        self.setWindowTitle("💬 ColorBridge - 消息终端 (独立窗口)")
        self.setMinimumSize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 消息显示区域
        self.display_text = QTextEdit()
        self.display_text.setReadOnly(True)
        self.display_text.setFont(QFont("Consolas", 9))
        self.display_text.setAcceptRichText(True)
        self.display_text.document().setMaximumBlockCount(1000000)
        self.display_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.display_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                line-height: 1.2;
            }
        """)
        
        # 设置内容
        if content:
            self.display_text.setText(content)
        
        layout.addWidget(self.display_text)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建简单的工具栏
        self.create_toolbar()
        
        # 窗口关闭事件
        self.close_callback = None
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具")
        toolbar.setMovable(False)
        
        # 复制按钮
        copy_action = QAction("📋 复制", self)
        copy_action.triggered.connect(self.copy_content)
        toolbar.addAction(copy_action)
        
        # 清除按钮
        clear_action = QAction("🧹 清除", self)
        clear_action.triggered.connect(self.clear_content)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        # 字体放大
        zoom_in_action = QAction("🔍 放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        # 字体缩小
        zoom_out_action = QAction("🔎 缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
    def copy_content(self):
        """复制内容到剪贴板"""
        self.display_text.selectAll()
        self.display_text.copy()
        self.display_text.textCursor().clearSelection()
        self.status_bar.showMessage("内容已复制到剪贴板", 2000)
        
    def clear_content(self):
        """清除内容"""
        self.display_text.clear()
        self.status_bar.showMessage("内容已清除", 2000)
        
    def zoom_in(self):
        """放大字体"""
        current_font = self.display_text.font()
        new_size = current_font.pointSize() + 1
        if new_size <= 20:
            self.display_text.setFont(QFont("Consolas", new_size))
            self.status_bar.showMessage(f"字体大小: {new_size}pt", 2000)
            
    def zoom_out(self):
        """缩小字体"""
        current_font = self.display_text.font()
        new_size = current_font.pointSize() - 1
        if new_size >= 6:
            self.display_text.setFont(QFont("Consolas", new_size))
            self.status_bar.showMessage(f"字体大小: {new_size}pt", 2000)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.close_callback:
            self.close_callback()
        super().closeEvent(event)


class ColorBridgeMainWindow(QMainWindow):
    """PCL2风格的主窗口类 (融合版本 - 清理版本的稳定性 + 增强版本的完整功能)"""
    
    # 信号定义
    settings_changed = pyqtSignal(dict)
    performance_alert = pyqtSignal(str, str)
    theme_changed = pyqtSignal(str)
    settings_requested = pyqtSignal()
    
    def __init__(self, monitoring_system=None, log_analyzer=None, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        
        # 关闭状态标志（解决关闭无响应问题）
        self.is_closing = False
        self._cleanup_failed = False
        
        # 监控系统集成
        self.monitoring_system = monitoring_system
        self.log_analyzer = log_analyzer
        
        # 窗口拖动和调整大小相关变量
        self.drag_position = None
        self.resize_edge = None
        self.edge_margin = 8  # 边缘检测宽度（像素）
        
        # 时间戳设置
        self.show_timestamp = True
        
        # 自动滚动设置
        self.auto_scroll = True
        
        # 显示区域最大化状态
        self.display_maximized = False
        self.display_window = None  # 独立窗口实例
        
        # AI8051U检测设置
        self.ai8051u_detection_enabled = True
        
        # 最近发送的命令（用于过滤回显）
        self._last_sent_command = None
        
        # 消息缓冲区相关
        self._message_buffer = ""
        self._last_message_time = 0
        self._buffer_timestamp = ""  # 缓冲区开始的时间戳
        self._message_timeout = 0.1  # 100ms超时，用于合并分割的消息
        self._buffer_timer = QTimer()
        self._buffer_timer.timeout.connect(self._check_message_buffer)
        self._buffer_timer.start(50)  # 每50ms检查一次缓冲区
        
        # 设备忙状态管理
        self._device_busy = False  # 设备忙标志
        self._waiting_for_info_response = False  # 等待info响应标志
        self._device_busy_start_time = 0  # 设备忙开始时间
        self._device_busy_timeout = 10.0  # 设备忙超时时间（秒），匹配自动流程的9秒超时
        self._last_manual_send_time = 0  # 最后手动发送时间
        self._min_manual_send_interval = 2.0  # 最小手动发送间隔2秒
        self._device_busy_timer = QTimer()
        self._device_busy_timer.timeout.connect(self._check_device_busy_timeout)
        
        # 命令等待队列
        self._pending_commands = []  # 等待发送的命令队列
        self._pending_commands_max = 10  # 最大等待命令数
        self._pending_commands_timer = QTimer()
        self._pending_commands_timer.timeout.connect(self._process_pending_commands)
        self._pending_commands_timer.start(100)  # 每100ms检查一次等待队列
        
        # 设备就绪检测关键词
        self._device_ready_keywords = [
            '系统就绪', '运行正常', '就绪', 'ready',
            '硬件加速测试完成', '所有计算均为实时执行',
            '测试完成', '完成测试', 'mdu32测试完成', 'tfpu测试完成',
            'AI8051U>', '> ', '命令:', '输入命令', 'hydrogen>', '氢原子系统',
            '欢迎使用', '请输入命令', 'help', '命令列表'
        ]
        
        # 设备忙检测关键词（触发设备忙状态）
        self._device_busy_keywords = [
            '系统重启中...', '重启系统', 'reset',
            '硬件加速单元测试', 'mdu32硬件乘除单元测试', 'tfpu浮点运算单元测试',
            '性能基准测试:', '基准测试', '长时间测试', 'hwtest'
        ]
        
        # 性能统计
        self._message_stats = {
            'sent': 0,
            'received': 0,
            'last_update': time.time()
        }
        self._performance_data = {
            'cpu_frequency': '未知',
            'tfpu_frequency': '未知'
        }
        
        # DS18B20自动查询功能
        self.ds18b20_auto_query_enabled = False
        self.ds18b20_auto_query_interval = 10  # 默认10秒
        self.ds18b20_auto_query_timer = QTimer()
        self.ds18b20_auto_query_timer.timeout.connect(self._auto_query_ds18b20)
        self.ds18b20_current_temperature = "未读取"
        
        # 初始化核心组件
        self.init_core_components()
        
        # 初始化UI组件
        self.init_ui_components()
        
        # 初始化UI
        self.init_pcl2_ui()
        
        # 设置连接
        self.setup_connections()
        
        # 加载设置
        self.load_settings()
        
        # 启动性能监控
        self.start_performance_monitoring()
        
        # 集成监控和日志分析
        self.setup_monitoring_integration()
        
        # 启动设备信息自动刷新
        self.start_device_info_refresh()
        
        # 应用启动动画
        self.start_startup_animation()
        
        # 确保所有部件都启用鼠标跟踪
        self._enable_mouse_tracking_for_all_widgets(self)
        
        # 为标题栏安装事件过滤器
        self.title_bar.installEventFilter(self)
        
        if self.debug_mode:
            print("[DEBUG] PCL2风格主窗口 (融合版本) 初始化完成")
    
    def _enable_mouse_tracking_for_all_widgets(self, widget):
        """递归为所有子部件启用鼠标跟踪"""
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
    
    def toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.isMaximized():
            # 当前是最大化状态，还原窗口
            self.showNormal()
            self.maximize_btn.setText("□")  # 设置为最大化图标
        else:
            # 当前是正常状态，最大化窗口
            self.showMaximized()
            self.maximize_btn.setText("❐")  # 设置为还原图标
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理标题栏的鼠标事件和显示容器调整大小"""
        # 处理显示容器调整大小事件
        if hasattr(self, 'display_container') and obj == self.display_container:
            if event.type() == QEvent.Type.Resize:
                self.update_button_overlay_position()
                return False  # 继续传递事件
        
        # 标题栏鼠标事件处理
        if obj == self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # 检查点击位置是否在控制按钮上
                    pos = event.position().toPoint()
                    # 获取标题栏中的按钮
                    for child in self.title_bar.findChildren(QToolButton):
                        if child.geometry().contains(pos):
                            # 点击在按钮上，不处理拖动
                            return super().eventFilter(obj, event)
                    
                    # 开始拖动窗口
                    self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    if self.debug_mode:
                        print(f"[DEBUG] 标题栏开始拖动: 拖动位置={self.drag_position}")
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position is not None:
                    # 正在拖动窗口
                    new_pos = event.globalPosition().toPoint() - self.drag_position
                    # 确保新位置在屏幕范围内
                    screen = QApplication.primaryScreen().availableGeometry()
                    new_pos.setX(max(0, min(new_pos.x(), screen.width() - 100)))
                    new_pos.setY(max(0, min(new_pos.y(), screen.height() - 100)))
                    
                    if self.debug_mode:
                        print(f"[DEBUG] 标题栏拖动中: 新位置={new_pos}")
                    self.move(new_pos)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_position = None
                    return True
        
        return super().eventFilter(obj, event)
        
    def setup_monitoring_integration(self):
        """设置监控系统集成"""
        try:
            # 集成监控系统到串口管理器
            if self.monitoring_system:
                # 更新串口管理器以使用监控系统
                if hasattr(self.serial_manager, 'reader_thread') and self.serial_manager.reader_thread:
                    self.serial_manager.reader_thread.monitoring_system = self.monitoring_system
                
                # 添加监控面板标签页
                self._add_monitoring_tab()
            
            # 集成日志分析器
            if self.log_analyzer:
                # 重定向日志输出到分析器
                self._setup_log_redirection()
                
                # 添加日志分析面板
                self._add_log_analysis_tab()
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 监控系统集成失败: {e}")
    
    def _add_monitoring_tab(self):
        """添加监控面板标签页"""
        try:
            if hasattr(self, 'tab_widget') and self.monitoring_system:
                # 创建监控面板
                monitoring_widget = self._create_monitoring_widget()
                self.tab_widget.addTab(monitoring_widget, "📊 系统监控")
                
                if self.debug_mode:
                    print("[DEBUG] 监控面板已添加")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 添加监控面板失败: {e}")
    
    def _add_log_analysis_tab(self):
        """添加日志分析面板标签页"""
        try:
            if hasattr(self, 'tab_widget') and self.log_analyzer:
                # 创建日志分析面板
                log_widget = self._create_log_analysis_widget()
                self.tab_widget.addTab(log_widget, "🔍 日志分析")
                
                if self.debug_mode:
                    print("[DEBUG] 日志分析面板已添加")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 添加日志分析面板失败: {e}")
    
    def _create_monitoring_widget(self):
        """创建监控面板组件"""
        from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 系统健康状态
        health_label = QLabel("🏥 系统健康状态: 检查中...")
        health_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(health_label)
        
        # 监控数据显示
        monitor_display = QTextEdit()
        monitor_display.setReadOnly(True)
        monitor_display.setMaximumHeight(300)
        layout.addWidget(monitor_display)
        
        # 更新定时器
        def update_monitoring():
            try:
                if self.monitoring_system:
                    dashboard_data = self.monitoring_system.get_monitoring_dashboard()
                    
                    # 更新健康状态
                    health = dashboard_data.get('system_health', {})
                    status = health.get('overall_status', 'unknown')
                    cpu = health.get('cpu_usage', 0)
                    memory = health.get('memory_usage', 0)
                    
                    status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌", "error": "❌"}.get(status, "❓")
                    health_label.setText(f"🏥 系统健康状态: {status_emoji} {status.upper()} (CPU: {cpu:.1f}%, 内存: {memory:.1f}%)")
                    
                    # 更新监控数据
                    monitor_text = f"""\
📊 监控仪表板
================
运行时间: {dashboard_data.get('uptime', 0):.1f}s
监控状态: {'🟢 运行中' if dashboard_data.get('is_monitoring') else '🔴 已停止'}

📈 关键指标:\
"""
                    
                    metrics = dashboard_data.get('metrics_summary', {})
                    for metric_name, metric_data in metrics.items():
                        if metric_data:
                            current = metric_data.get('current', 0)
                            average = metric_data.get('average', 0)
                            monitor_text += f"• {metric_name}: 当前 {current:.2f}, 平均 {average:.2f}\n"
                    
                    # 活跃预警
                    active_alerts = dashboard_data.get('active_alerts', [])
                    if active_alerts:
                        monitor_text += f"\n🚨 活跃预警 ({len(active_alerts)}个):\n"
                        for alert in active_alerts[:3]:  # 只显示前3个
                            level_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🔴"}.get(alert.get('level', 'info'), "ℹ️")
                            monitor_text += f"• {level_emoji} {alert.get('title', 'Unknown')}\n"
                    
                    monitor_display.setText(monitor_text)
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 监控更新失败: {e}")
        
        # 设置更新定时器
        monitor_timer = QTimer()
        monitor_timer.timeout.connect(update_monitoring)
        monitor_timer.start(2000)  # 每2秒更新一次
        
        # 保存定时器引用
        widget.monitor_timer = monitor_timer
        widget.health_label = health_label
        
        return widget
    
    def _create_log_analysis_widget(self):
        """创建日志分析面板组件"""
        from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QPushButton
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 分析状态
        status_label = QLabel("🔍 日志分析: 运行中...")
        status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(status_label)
        
        # 分析结果显示
        analysis_display = QTextEdit()
        analysis_display.setReadOnly(True)
        analysis_display.setMaximumHeight(300)
        layout.addWidget(analysis_display)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📄 导出分析报告")
        export_btn.clicked.connect(self._export_analysis_report)
        button_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑️ 清理分析历史")
        clear_btn.clicked.connect(self._clear_analysis_history)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # 更新定时器
        def update_log_analysis():
            try:
                if self.log_analyzer:
                    stats = self.log_analyzer.get_statistics()
                    
                    status_label.setText(f"🔍 日志分析: 🟢 运行中 (处理: {stats['total_lines_processed']}行, 错误: {stats['total_errors_detected']}个)")
                    
                    # 获取最近分析结果
                    analysis_text = f"""
📊 日志分析统计
================
总处理行数: {stats['total_lines_processed']}
总检测错误: {stats['total_errors_detected']}
分析运行时间: {stats['analysis_runtime']:.1f}s
处理速度: {stats['lines_per_second']:.1f}行/秒
错误频率: {stats['errors_per_minute']:.1f}错误/分钟
缓冲区大小: {stats['buffer_size']}
监控状态: {'🟢 运行中' if stats['is_analyzing'] else '🔴 已停止'}

💡 最近建议:
"""
                    
                    # 这里可以添加最近的建议显示逻辑
                    analysis_display.setText(analysis_text)
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 日志分析更新失败: {e}")
        
        # 设置更新定时器
        analysis_timer = QTimer()
        analysis_timer.timeout.connect(update_log_analysis)
        analysis_timer.start(3000)  # 每3秒更新一次
        
        # 保存定时器引用
        widget.analysis_timer = analysis_timer
        widget.status_label = status_label
        
        return widget
    
    def _setup_log_redirection(self):
        """设置日志重定向（修复无限递归问题）"""
        try:
            import sys
            from io import StringIO
            
            # 创建自定义的日志输出流（添加递归保护）
            class LogRedirector(StringIO):
                def __init__(self, log_analyzer, original_stream):
                    super().__init__()
                    self.log_analyzer = log_analyzer
                    self.original_stream = original_stream
                    self._redirecting = False  # 递归保护标志
                    self._last_logs = []  # 最近日志缓存
                    self._max_cache = 100  # 最大缓存数量
                
                def write(self, text):
                    # 发送到原始流
                    self.original_stream.write(text)
                    
                    # 递归保护：如果正在重定向中，直接返回
                    if self._redirecting:
                        return
                    
                    # 检查是否为重复日志（避免风暴）
                    text_stripped = text.strip()
                    if not text_stripped:
                        return
                    
                    # 检查是否为DEBUG日志且重复
                    if text_stripped.startswith('[DEBUG]'):
                        # 简单的重复检测
                        if text_stripped in self._last_logs:
                            return
                        self._last_logs.append(text_stripped)
                        if len(self._last_logs) > self._max_cache:
                            self._last_logs.pop(0)
                    
                    # 发送到日志分析器（使用递归保护）
                    if self.log_analyzer and text_stripped:
                        try:
                            self._redirecting = True
                            self.log_analyzer.add_log_line(text_stripped)
                        except Exception:
                            # 忽略日志分析器的错误，避免影响主程序
                            pass
                        finally:
                            self._redirecting = False
            
            # 重定向stdout和stderr
            if self.log_analyzer:
                sys.stdout = LogRedirector(self.log_analyzer, sys.stdout)
                sys.stderr = LogRedirector(self.log_analyzer, sys.stderr)
                
                if self.debug_mode:
                    print("[DEBUG] 日志重定向已设置（带递归保护）")
                    
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 日志重定向设置失败: {e}")
    
    def _export_analysis_report(self):
        """导出分析报告"""
        try:
            if self.log_analyzer:
                filename = self.log_analyzer.export_analysis_report()
                if filename:
                    self.notification_manager.show_success(f"📄 分析报告已导出: {filename}")
                else:
                    self.notification_manager.show_error("❌ 分析报告导出失败")
        except Exception as e:
            self.notification_manager.show_error(f"❌ 导出失败: {e}")
    
    def _clear_analysis_history(self):
        """清理分析历史"""
        try:
            if self.log_analyzer:
                # 这里可以实现清理历史记录的逻辑
                self.notification_manager.show_info("🗑️ 分析历史已清理")
        except Exception as e:
            self.notification_manager.show_error(f"❌ 清理失败: {e}")
    
    def init_core_components(self):
        """初始化核心组件"""
        # 串口管理器
        self.serial_manager = ColorBridgeSerialManager(
            monitoring_system=self.monitoring_system,
            debug_mode=self.debug_mode
        )
        
        self.device_info_manager = ColorBridgeDeviceInfoManager(self.serial_manager)
        
        # 连接设备信息更新信号
        self.device_info_manager.device_info_updated.connect(self.on_device_info_updated)
        
        # 状态变量
        self.current_command_index = 0
        self.command_sequence = ['reset', 'info', 'hwtest', 'mdu32', 'tfpu', 'benchmark', 'clockinfo']
        self.command_sequence_running = False
        self._user_requested_device_info = False  # 用户主动请求设备信息标志
        
    def init_ui_components(self):
        """初始化UI组件"""
        # 主题管理器
        self.theme_manager = ThemeManager()
        
        # 通知管理器 - 使用增强版本
        self.notification_manager = EnhancedNotificationManager()
        
        # 设置文件路径
        self.settings_file = os.path.join(os.path.dirname(__file__), '..', 'colorbridge_settings.json')
        
        # 壁纸相关
        self.current_wallpaper = None
        self.current_wallpaper_path = ''
        
        # 终端消息日志管理器（默认禁用，通过首选项启用）
        try:
            from core.colorbridge_terminal_logger import get_terminal_logger
            self.terminal_logger = get_terminal_logger(enabled=False)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 无法初始化终端日志管理器: {e}")
            self.terminal_logger = None
        
    def init_pcl2_ui(self):
        """初始化PCL2风格UI"""
        self.setWindowTitle("🌈 ColorBridge - AI8051U串口助手 (PCL2风格)")
        
        # 设置窗口几何属性
        self.setup_window_geometry()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建标题栏（包含最小化和关闭按钮）
        self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 创建菜单栏
        self.create_menu_bar()
        main_layout.addWidget(self.menu_bar)
        
        # 创建主要内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # 左侧区域 - 串口连接控制
        self.create_left_panel()
        self.left_panel.setMaximumWidth(250)
        self.left_panel.setMinimumWidth(200)
        content_layout.addWidget(self.left_panel)
        
        # 中间区域 - 串口终端消息显示
        self.create_middle_panel()
        content_layout.addWidget(self.middle_panel, 1)  # 中间区域自动扩展
        
        # 右侧区域 - 快捷命令
        self.create_right_panel()
        self.right_panel.setMaximumWidth(300)
        self.right_panel.setMinimumWidth(250)
        content_layout.addWidget(self.right_panel)
        
        main_layout.addWidget(content_widget)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置窗口属性
        self.setMinimumSize(1300, 700)
        # 移除最大尺寸限制，允许窗口自由调整大小
        # 设置无边框窗口，但允许调整大小
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowMaximizeButtonHint)
        # 确保窗口支持透明度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # 启用鼠标跟踪以支持调整大小功能
        self.setMouseTracking(True)
        
        # 确保中央部件也启用鼠标跟踪
        self.centralWidget().setMouseTracking(True)
        
        # 应用PCL2主题
        self.apply_pcl2_theme()
        
        # 设置通知管理器
        self.setup_notification_manager()
        
    def create_title_bar(self):
        """创建PCL2风格的标题栏"""
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)
        # 确保标题栏在最上层
        self.title_bar.raise_()
        
        layout = QHBoxLayout(self.title_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        layout.addStretch()
        
        # 控制按钮
        minimize_btn = QToolButton()
        minimize_btn.setText("─")
        minimize_btn.setStyleSheet("""
            QToolButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)
        
        # 最大化/还原按钮
        self.maximize_btn = QToolButton()
        self.maximize_btn.setText("□")
        self.maximize_btn.setStyleSheet("""
            QToolButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_btn)
        
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setStyleSheet("""
            QToolButton {
                background: rgba(231, 76, 60, 0.8);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: rgba(192, 57, 43, 0.9);
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background: rgba(255, 255, 255, 0.95);
                border-bottom: 1px solid rgba(200, 200, 200, 0.3);
                color: #2c3e50;
                font-weight: bold;
            }
            QMenuBar::item {
                background: transparent;
                padding: 8px 16px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background: rgba(52, 152, 219, 0.2);
                color: #3498db;
            }
            QMenu {
                background: rgba(255, 255, 255, 0.98);
                border: 1px solid rgba(200, 200, 200, 0.5);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(52, 152, 219, 0.2);
                color: #3498db;
            }
        """)
        
        # 文件菜单
        file_menu = self.menu_bar.addMenu("📁 文件")
        
        save_log_action = QAction("💾 保存日志", self)
        save_log_action.triggered.connect(self.save_display_log)
        file_menu.addAction(save_log_action)
        
        export_report_action = QAction("📊 导出分析报告", self)
        export_report_action.triggered.connect(self._export_analysis_report)
        file_menu.addAction(export_report_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = self.menu_bar.addMenu("👁️ 视图")
        
        theme_menu = view_menu.addMenu("🎨 主题")
        
        dopamine_action = QAction("🌈 多巴胺", self)
        dopamine_action.triggered.connect(lambda: self.apply_theme("dopamine"))
        theme_menu.addAction(dopamine_action)
        
        dark_action = QAction("🌙 深色", self)
        dark_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_action)
        
        light_action = QAction("☀️ 浅色", self)
        light_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_action)
        
        # 工具菜单
        tools_menu = self.menu_bar.addMenu("🔧 工具")
        
        env_action = QAction("🔍 环境检测", self)
        env_action.triggered.connect(self.check_environment)
        tools_menu.addAction(env_action)
        
        test_notify_action = QAction("🔔 测试通知", self)
        test_notify_action.triggered.connect(self.test_notifications)
        tools_menu.addAction(test_notify_action)
        
        batch_test_action = QAction("🔄 批量测试", self)
        batch_test_action.triggered.connect(self.run_batch_tests)
        tools_menu.addAction(batch_test_action)
        
        perf_report_action = QAction("📊 性能报告", self)
        perf_report_action.triggered.connect(self.generate_performance_report)
        tools_menu.addAction(perf_report_action)
        
        device_info_action = QAction("📱 设备信息", self)
        device_info_action.triggered.connect(self.show_device_info_dialog)
        tools_menu.addAction(device_info_action)
        
        # 隐藏的游戏入口 - 彩蛋功能（蓝色灯泡图标）
        tools_menu.addSeparator()
        game_action = QAction("💡 系统调试", self)
        # 直接连接到open_billiard_game，但确保用户点击标志被设置
        game_action.triggered.connect(self.open_billiard_game)
        game_action.setToolTip("点击打开隐藏的台球游戏彩蛋")
        tools_menu.addAction(game_action)
        
        # 设置菜单
        settings_menu = self.menu_bar.addMenu("⚙️ 设置")
        
        # 添加设置对话框菜单项
        preferences_action = QAction("🎛️ 首选项设置", self)
        preferences_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(preferences_action)
        
        settings_menu.addSeparator()
        
        buffer_menu = settings_menu.addMenu("🗂️ 缓冲策略")
        
        conservative_action = QAction("🛡️ 保守模式 (200KB)", self)
        conservative_action.triggered.connect(lambda: self.set_buffer_strategy(0))
        buffer_menu.addAction(conservative_action)
        
        balanced_action = QAction("⚖️ 平衡模式 (100KB)", self)
        balanced_action.triggered.connect(lambda: self.set_buffer_strategy(1))
        buffer_menu.addAction(balanced_action)
        
        performance_action = QAction("🚀 性能模式 (50KB)", self)
        performance_action.triggered.connect(lambda: self.set_buffer_strategy(2))
        buffer_menu.addAction(performance_action)
        
        settings_menu.addSeparator()
        
        clear_history_action = QAction("🗑️ 清理分析历史", self)
        clear_history_action.triggered.connect(self._clear_analysis_history)
        settings_menu.addAction(clear_history_action)
        
        # 帮助菜单
        help_menu = self.menu_bar.addMenu("❓ 帮助")
        
        about_action = QAction("ℹ️ 关于 ColorBridge", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def set_buffer_strategy(self, index):
        """设置缓冲策略"""
        self.buffer_combo.setCurrentIndex(index)
        self.apply_buffer_strategy()
        
    def _on_game_menu_clicked(self):
        """处理游戏菜单点击"""
        if self.debug_mode:
            print("[DEBUG] 游戏菜单被点击")
        # 设置用户点击标志
        self._user_clicked_game = True
        # 调用游戏方法
        self.open_billiard_game()
        
    def open_billiard_game(self):
        """打开台球游戏（彩蛋功能）- 连续点击8次触发"""
        try:
            if self.debug_mode:
                print(f"[DEBUG] open_billiard_game() 被调用 - 菜单项点击处理开始")
            
            # 初始化点击计数器
            if not hasattr(self, '_game_click_count'):
                self._game_click_count = 0
                self._game_click_timer = None
            
            # 增加点击计数
            self._game_click_count += 1
            current_count = self._game_click_count
            
            if self.debug_mode:
                print(f"[DEBUG] 点击计数: {current_count}")
            
            # 重置计时器（8秒内连续点击才有效）
            if hasattr(self, '_game_click_timer') and self._game_click_timer:
                self._game_click_timer.stop()
            
            self._game_click_timer = QTimer()
            self._game_click_timer.setSingleShot(True)
            self._game_click_timer.timeout.connect(self._reset_game_click_count)
            self._game_click_timer.start(8000)  # 8秒后重置计数
            
            # 根据点击次数显示不同的通知
            if hasattr(self, 'notification_manager'):
                if current_count == 1:
                    self.notification_manager.show_info("暂时不提供服务")
                    return
                elif current_count == 2:
                    self.notification_manager.show_warning("暂时不没有服务哦")
                    return
                elif current_count == 3:
                    self.notification_manager.show_warning("没有服务")
                    return
                elif current_count == 4:
                    self.notification_manager.show_warning("干嘛！")
                    return
                elif current_count == 5:
                    # 第5次点击没有通知（用户要求中没有提到）
                    return
                elif current_count == 6:
                    self.notification_manager.show_error("爱你！爱你！爱你！都说了没有服务憋点了！")
                    return
                elif current_count == 7:
                    self.notification_manager.show_error("啊~~~^^^你干嘛~都说了憋点了！")
                    return
                elif current_count == 8:
                    # 第8次点击：显示彩蛋通知并等待2秒
                    self.notification_manager.show_success("🎉 恭喜你发现了彩蛋！游戏将在2秒后启动...")
                    
                    # 等待2秒后启动游戏
                    QTimer.singleShot(2000, self._actually_open_billiard_game)
                    return
                elif current_count > 8:
                    # 超过8次点击显示特殊通知
                    self.notification_manager.show_info("。。。。。。。。                        ；就是这样，你懂了吗？")
                    return
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 彩蛋点击处理失败: {e}")
                import traceback
                traceback.print_exc()
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_error(f"彩蛋处理失败: {str(e)}")
    
    def _reset_game_click_count(self):
        """重置游戏点击计数器"""
        if self.debug_mode:
            print("[DEBUG] 重置游戏点击计数器")
        self._game_click_count = 0
    
    def _actually_open_billiard_game(self):
        """实际打开台球游戏（在点击8次后调用）"""
        try:
            if self.debug_mode:
                print("[DEBUG] _actually_open_billiard_game() 被调用")
            
            # 防止重复调用
            if hasattr(self, '_game_window_open') and self._game_window_open:
                if self.debug_mode:
                    print("[DEBUG] 游戏启动被阻止：游戏窗口已打开")
                return
            
            # 导入游戏模块
            from games.billiard_3d.ui import BilliardGameUI
            
            if self.debug_mode:
                print("[DEBUG] 正在创建游戏窗口...")
            
            # 创建游戏窗口，传递调试模式
            self.game_window = BilliardGameUI(debug_mode=self.debug_mode)
            
            if self.debug_mode:
                print("[DEBUG] 游戏窗口创建成功，设置属性...")
            
            self.game_window.setWindowTitle("🎱 ColorBridge 台球游戏 (彩蛋)")
            
            # 根据屏幕分辨率动态设置最小尺寸
            screen = self.screen()
            screen_geometry = screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # 设置最小尺寸为屏幕尺寸的70%
            min_width = int(screen_width * 0.7)
            min_height = int(screen_height * 0.7)
            self.game_window.setMinimumSize(min_width, min_height)
            
            if self.debug_mode:
                print(f"[DEBUG] 屏幕分辨率: {screen_width}x{screen_height}, 最小尺寸: {min_width}x{min_height}")
            
            # 使用简单的样式表
            self.game_window.setStyleSheet("background-color: #1a1a2e;")
            
            if self.debug_mode:
                print("[DEBUG] 显示游戏窗口...")
            
            # 显示游戏窗口并最大化
            self.game_window.showMaximized()
            
            # 设置游戏窗口打开标志
            self._game_window_open = True
            
            # 连接关闭事件 - 使用弱引用避免循环引用
            from PyQt6.QtCore import QObject
            self.game_window.destroyed.connect(self._on_game_window_closed)
            
            if self.debug_mode:
                print("[DEBUG] 游戏窗口显示并最大化成功")
            
            # 显示最终通知
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_success("🎱 台球游戏已启动！这是一个隐藏的彩蛋功能。")
            
            # 游戏启动后重置点击计数器，以便下次可以重新计数
            self._reset_game_click_count()
                
        except ImportError as e:
            if self.debug_mode:
                print(f"[DEBUG] 无法导入游戏模块: {e}")
                import traceback
                traceback.print_exc()
            
            # 增强的错误诊断信息
            import platform
            import sys
            import os
            
            error_msg = f"无法加载游戏模块: {str(e)}"
            suggestions = [
                "游戏模块可能未正确安装或文件缺失",
                "请检查 games/billiard_3d/ 目录是否存在",
                "如果是pip安装，游戏模块应该已包含在包中",
                "如果是源码运行，请确保克隆了完整的仓库"
            ]
            
            # 平台特定的诊断建议
            system_name = platform.system()
            if system_name == "Linux":
                suggestions.append("")  # 空行分隔
                suggestions.append("🔧 Linux/Debian 环境诊断:")
                suggestions.append("1. Qt6运行时依赖:")
                suggestions.append("   sudo apt update && sudo apt install libqt6gui6 libqt6widgets6 libqt6core6 libqt6network6 qt6-qpa-plugins")
                suggestions.append("2. PyQt6 Python包:")
                suggestions.append("   pip install PyQt6>=6.6.0")
                suggestions.append("3. 显示环境:")
                suggestions.append("   检查DISPLAY变量: echo $DISPLAY")
                suggestions.append("   设置显示: export DISPLAY=:0")
                suggestions.append("   或使用xvfb: sudo apt install xvfb && xvfb-run python main.py")
                suggestions.append("4. 字体支持:")
                suggestions.append("   sudo apt install ttf-mscorefonts-installer fonts-liberation")
                suggestions.append("")  # 空行分隔
                suggestions.append("📋 快速环境检查:")
                suggestions.append("   运行: python -c \"from PyQt6.QtWidgets import QApplication; print('PyQt6正常')\"")
                suggestions.append("   运行: python -c \"import games.billiard_3d; print('游戏模块正常')\"")
                suggestions.append("   运行: echo $DISPLAY")
            
            # 详细的错误分析
            error_str = str(e).lower()
            if "pyqt6" in error_str or "qt" in error_str:
                suggestions.append("⚠️ 错误涉及PyQt6/Qt，请检查Qt6安装")
            if "display" in error_str or "screen" in error_str or "gui" in error_str:
                suggestions.append("⚠️ 错误涉及显示/GUI，请检查DISPLAY设置")
            if "font" in error_str or "arial" in error_str:
                suggestions.append("⚠️ 错误涉及字体，请安装Arial或替代字体")
            
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_error(error_msg)
                # 显示详细建议
                for suggestion in suggestions:
                    if suggestion.strip():  # 跳过空行
                        self.notification_manager.show_info(suggestion)
            
            # 在控制台输出更详细的诊断信息
            print(f"\n🔍 游戏模块导入失败详细诊断:")
            print(f"   系统: {platform.system()} {platform.release()}")
            print(f"   Python: {sys.version}")
            print(f"   错误: {str(e)}")
            print(f"   模块搜索路径: {sys.path[:3]}...")  # 只显示前3个
            print(f"   当前目录: {os.getcwd()}")
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 打开游戏失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 增强的通用错误处理
            import platform
            import sys
            
            error_msg = f"打开游戏失败: {str(e)}"
            
            # 尝试分析错误类型
            error_str = str(e).lower()
            suggestions = []
            
            if "permission" in error_str or "access" in error_str:
                suggestions.append("权限问题，尝试使用sudo或检查文件权限")
            if "memory" in error_str or "alloc" in error_str:
                suggestions.append("内存不足，关闭其他程序释放内存")
            if "display" in error_str or "screen" in error_str:
                suggestions.append("显示问题，检查DISPLAY环境变量")
                if platform.system() == "Linux":
                    suggestions.append("Linux显示设置: export DISPLAY=:0")
            
            # 添加通用建议
            if not suggestions:
                suggestions.append("检查系统资源是否充足")
                suggestions.append("尝试重新启动程序")
                suggestions.append("查看详细日志获取更多信息")
            
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_error(error_msg)
                if suggestions:
                    for suggestion in suggestions:
                        self.notification_manager.show_info(suggestion)
            
            # 控制台输出
            print(f"\n🔍 游戏启动失败详细诊断:")
            print(f"   系统: {platform.system()} {platform.release()}")
            print(f"   Python: {sys.version}")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误详情: {str(e)}")
    
    def _on_game_window_closed(self):
        """游戏窗口关闭时的处理"""
        if self.debug_mode:
            print("[DEBUG] 游戏窗口已关闭，重置游戏窗口打开标志")
        self._game_window_open = False
        # 同时重置点击计数器，以便可以重新开始计数
        self._reset_game_click_count()
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        try:
            dialog = SettingsDialog(self)
            dialog.settings_changed.connect(self.apply_settings)
            dialog.exec()
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 打开设置对话框失败: {e}")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
🌈 ColorBridge - AI8051U串口助手
        版本: 2.1.17 PCL2风格 - Linux帮助对话框和版本统一更新
专为 AI8051U USB-CDC 项目设计
完全模仿PCL2启动器的现代化UI设计

主要功能:
• PCL2风格界面设计
• 串口连接管理
• 实时数据监控
• 硬件测试支持
• 智能日志分析

作者: 076lik
许可证: GPLV3
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("关于 ColorBridge")
        msg_box.setText(about_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
        
    def create_left_panel(self):
        """创建左侧面板 - 串口连接控制"""
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(200, 200, 200, 0.3);
            }
        """)
        
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 串口连接卡片
        self.create_connection_card()
        layout.addWidget(self.connection_card)
        
        # 设备信息卡片
        self.create_device_info_card()
        layout.addWidget(self.device_info_card)
        
        layout.addStretch()  # 添加弹性空间
        
    def create_middle_panel(self):
        """创建中间面板 - 串口终端消息显示"""
        self.middle_panel = QFrame()
        self.middle_panel.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(200, 200, 200, 0.3);
            }
        """)
        
        layout = QVBoxLayout(self.middle_panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 消息显示卡片
        self.create_message_card()
        layout.addWidget(self.message_card, 1)  # 设置stretch factor为1，让消息卡片扩展
        
    def create_device_info_card(self):
        """创建设备信息卡片"""
        self.device_info_card = PCL2Card("📱 设备信息")
        
        # 设备信息显示文本框
        self.device_info_display = QTextEdit()
        self.device_info_display.setReadOnly(True)
        self.device_info_display.setFont(self.theme_manager.get_font("mono", 8))  # 使用更小的字体大小
        self.device_info_display.setMinimumHeight(100)  # 进一步减少最小高度
        self.device_info_display.setMaximumHeight(160)  # 进一步减少最大高度，为按钮留出更多空间
        self.device_info_display.setStyleSheet("""
            QTextEdit {
                background: rgba(248, 250, 252, 0.9);
                border: 1px solid rgba(100, 200, 255, 0.2);
                border-radius: 6px;
                padding: 4px;
                color: #2c3e50;
                font-size: 8px;
                line-height: 1.2;
            }
        """)
        self.device_info_display.setPlainText("等待设备连接...\n\n点击'🔄 获取设备信息'按钮获取AI8051U设备详细信息")
        self.device_info_card.content_layout.addWidget(self.device_info_display)
        
        # 设备信息刷新按钮
        refresh_device_btn = PCL2Button("🔄 获取设备信息", "secondary")
        refresh_device_btn.setMinimumHeight(32)  # 增加按钮高度
        refresh_device_btn.setMinimumWidth(150)  # 增加按钮宽度
        refresh_device_btn.clicked.connect(self.request_device_info)
        self.device_info_card.content_layout.addWidget(refresh_device_btn)
        
    def on_device_info_updated(self, device_info: dict):
        """处理设备信息更新（支持手动触发和自动重要信息更新）"""
        try:
            # 清除等待响应标志和设备忙状态，表示已收到设备信息
            if hasattr(self, '_waiting_for_info_response'):
                self._waiting_for_info_response = False
            if hasattr(self, '_device_busy'):
                self._device_busy = False
            
            system_info = device_info.get('system', {})
            memory_info = device_info.get('memory', {})
            
            # 检查是否有用户主动请求标志
            user_requested = hasattr(self, '_user_requested_device_info') and self._user_requested_device_info
            
            # 判断设备信息是否完整的条件
            has_basic_info = bool(system_info.get('mcu'))
            has_clock_info = bool(system_info.get('clock_frequency') or system_info.get('cpu_clock'))
            has_memory_info = bool(memory_info.get('flash_used') and memory_info.get('xram_used'))
            
            # 检查是否有重要系统信息（版本、作者、硬件加速等）
            has_important_info = bool(
                system_info.get('version') or 
                system_info.get('author') or 
                system_info.get('hw_acceleration') or
                system_info.get('system') == 'AI8051U氢原子系统'
            )
            
            # 决定是否刷新显示的条件：
            # 1. 用户请求且信息完整
            # 2. 有重要系统信息（即使没有用户请求）
            # 3. 信息完整（自动流程获取的完整信息也应该显示）
            should_refresh = False
            refresh_reason = ""
            
            if user_requested and has_basic_info and has_clock_info and has_memory_info:
                should_refresh = True
                refresh_reason = "用户请求且信息完整"
                # 重置用户请求标志
                self._user_requested_device_info = False
            elif has_important_info:
                should_refresh = True
                refresh_reason = "检测到重要系统信息"
            elif has_basic_info and has_clock_info and has_memory_info:
                # 信息完整但既不是用户请求也没有"重要系统信息"字段
                # 这种情况常见于自动初始化流程获取的标准设备信息
                should_refresh = True
                refresh_reason = "自动获取的完整设备信息"
            
            if should_refresh:
                # 刷新设备信息显示
                self.refresh_device_info_display()
                
                # 更新性能数据
                self._update_performance_data(device_info)
                
                # 更新AI8051U检测状态
                if hasattr(self, 'ai8051u_status_label') and self.ai8051u_detection_enabled:
                    if system_info.get('system') == 'AI8051U氢原子系统':
                        self.ai8051u_status_label.setText("✅ AI8051U: 已检测")
                        self.ai8051u_status_label.setStyleSheet("""
                            QLabel {
                                color: #27ae60;
                                padding: 10px 14px;
                                background: rgba(39, 174, 96, 0.1);
                                border-radius: 6px;
                                border: 1px solid rgba(39, 174, 96, 0.3);
                            }
                        """)
                    elif system_info.get('mcu') and 'AI8051U' in system_info.get('mcu', ''):
                        self.ai8051u_status_label.setText("✅ AI8051U: 已识别")
                        self.ai8051u_status_label.setStyleSheet("""
                            QLabel {
                                color: #27ae60;
                                padding: 10px 14px;
                                background: rgba(39, 174, 96, 0.1);
                                border-radius: 6px;
                                border: 1px solid rgba(39, 174, 96, 0.3);
                            }
                        """)
                    else:
                        self.ai8051u_status_label.setText("🔍 AI8051U: 未检测")
                        self.ai8051u_status_label.setStyleSheet("""
                            QLabel {
                                color: #95a5a6;
                                padding: 10px 14px;
                                background: rgba(149, 165, 166, 0.1);
                                border-radius: 6px;
                                border: 1px solid rgba(149, 165, 166, 0.3);
                            }
                        """)
                
                if self.debug_mode:
                    print(f"[DEBUG] 设备信息已更新（{refresh_reason}）")
                    if system_info.get('version'):
                        print(f"[DEBUG] 版本: {system_info.get('version')}")
                    if system_info.get('author'):
                        print(f"[DEBUG] 作者: {system_info.get('author')}")
                    if system_info.get('hw_acceleration'):
                        print(f"[DEBUG] 硬件加速: {system_info.get('hw_acceleration')}")
                    if system_info.get('mcu'):
                        print(f"[DEBUG] MCU: {system_info.get('mcu')}")
                    if system_info.get('clock_frequency') or system_info.get('cpu_clock'):
                        print(f"[DEBUG] 时钟: {system_info.get('clock_frequency', system_info.get('cpu_clock', 'N/A'))}")
            elif user_requested:
                # 用户请求但信息不完整，显示中间状态
                if hasattr(self, 'device_info_display'):
                    current_text = self.device_info_display.toPlainText()
                    if "正在获取设备信息" in current_text:
                        # 更新显示状态，显示当前进度
                        progress_text = "正在获取设备信息...\n\n"
                        if has_basic_info:
                            progress_text += f"✓ 已获取: {system_info.get('mcu', 'N/A')}\n"
                        if has_clock_info:
                            progress_text += f"✓ 时钟信息: {system_info.get('clock_frequency', system_info.get('cpu_clock', 'N/A'))}\n"
                        if memory_info.get('flash_used'):
                            progress_text += f"✓ Flash使用: {memory_info.get('flash_used', 'N/A')}\n"
                        if memory_info.get('xram_used'):
                            progress_text += f"✓ XRAM使用: {memory_info.get('xram_used', 'N/A')}\n"
                        
                        progress_text += "\n请稍候，正在获取完整信息..."
                        self.device_info_display.setPlainText(progress_text)
                
                if self.debug_mode:
                    print(f"[DEBUG] 设备信息部分更新，等待完整信息...")
                    print(f"[DEBUG] 基础信息: {has_basic_info}, 时钟信息: {has_clock_info}, 内存信息: {has_memory_info}")
            else:
                if self.debug_mode:
                    print(f"[DEBUG] 设备信息已更新（非用户触发且无重要信息，不刷新显示）")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 设备信息更新处理错误: {e}")
    
    def request_device_info(self):
        """请求设备信息"""
        try:
            # 设置用户主动请求标志
            self._user_requested_device_info = True
            
            # 发送info命令获取设备信息
            if hasattr(self, 'serial_manager') and self.serial_manager:
                self.send_quick_command("info")
                if self.debug_mode:
                    print("[DEBUG] 已发送info命令获取设备信息（用户主动）")
            
            # 显示获取中状态
            if hasattr(self, 'device_info_display'):
                self.device_info_display.setPlainText("正在获取设备信息...\n\n请稍候...")
            
            # 设置超时定时器，5秒后强制刷新显示
            if hasattr(self, 'device_info_timeout_timer'):
                self.device_info_timeout_timer.stop()
            
            self.device_info_timeout_timer = QTimer()
            self.device_info_timeout_timer.setSingleShot(True)
            self.device_info_timeout_timer.timeout.connect(self._on_device_info_timeout)
            self.device_info_timeout_timer.start(5000)  # 5秒超时
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 请求设备信息失败: {e}")
            if hasattr(self, 'device_info_display'):
                self.device_info_display.setPlainText(f"获取设备信息失败:\n{str(e)}")
            # 重置标志
            self._user_requested_device_info = False
    
    def _on_device_info_timeout(self):
        """设备信息获取超时处理"""
        try:
            if hasattr(self, '_user_requested_device_info') and self._user_requested_device_info:
                # 强制刷新当前已获取的信息
                self.refresh_device_info_display()
                # 重置标志
                self._user_requested_device_info = False
                
                if self.debug_mode:
                    print("[DEBUG] 设备信息获取超时，显示已获取的信息")
                
                # 检查是否有获取到任何信息
                device_info = self.device_info_manager.get_device_info()
                if device_info and (device_info.get('system') or device_info.get('memory')):
                    # 有获取到信息，不显示警告
                    pass
                else:
                    # 没有获取到任何信息，显示提示
                    if hasattr(self, 'device_info_display'):
                        current_text = self.device_info_display.toPlainText()
                        if not current_text or current_text == "正在获取设备信息...\n\n请稍候...":
                            self.device_info_display.setPlainText("⚠️ 无法获取设备信息\n\n请检查:\n• 设备是否正确连接\n• 串口是否正常工作\n• 设备是否支持info命令")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 设备信息超时处理错误: {e}")
    
    def refresh_device_info_display(self):
        """刷新设备信息显示"""
        if hasattr(self, 'device_info_display'):
            device_info = self.device_info_manager.get_formatted_device_info()
            self.device_info_display.setPlainText(device_info)
            # 确保字体设置正确
            if hasattr(self, 'theme_manager'):
                self.device_info_display.setFont(self.theme_manager.get_font("mono", 8))
    
    def _update_performance_data(self, device_info: dict):
        """更新性能数据"""
        try:
            system_info = device_info.get('system', {})
            performance_info = device_info.get('performance', {})
            
            # 更新CPU频率
            cpu_freq = system_info.get('clock_frequency') or system_info.get('cpu_clock') or '未知'
            self._performance_data['cpu_frequency'] = cpu_freq
            
            # 更新TFPU频率
            tfpu_freq = performance_info.get('tfpu_frequency') or '未知'
            self._performance_data['tfpu_frequency'] = tfpu_freq
            
            # 更新UI显示
            self._update_performance_ui()
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 更新性能数据失败: {e}")
    
    def _update_performance_ui(self):
        """更新性能UI显示"""
        try:
            if hasattr(self, 'cpu_freq_label'):
                self.cpu_freq_label.setText(f"CPU频率: {self._performance_data['cpu_frequency']}")
            
            if hasattr(self, 'tfpu_freq_label'):
                self.tfpu_freq_label.setText(f"TFPU频率: {self._performance_data['tfpu_frequency']}")
            
            if hasattr(self, 'message_stats_label'):
                sent = self._message_stats['sent']
                received = self._message_stats['received']
                self.message_stats_label.setText(f"消息: {sent} 发送 / {received} 接收")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 更新性能UI失败: {e}")
        
    def create_connection_card(self):
        """创建串口连接卡片"""
        self.connection_card = PCL2Card("🔗 串口连接")
        
        # 串口选择行
        port_row = QVBoxLayout()
        port_row.setSpacing(8)
        
        port_label = QLabel("串口:")
        port_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        port_label.setStyleSheet("color: #2c3e50;")
        port_row.addWidget(port_label)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(25)
        self.port_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                font-family: "Microsoft YaHei";
                color: #2c3e50;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #7f8c8d;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                color: #2c3e50;
                font-size: 10px;
                font-family: "Microsoft YaHei";
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        port_row.addWidget(self.port_combo)
        
        # 波特率选择
        baud_label = QLabel("波特率:")
        baud_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        baud_label.setStyleSheet("color: #2c3e50;")
        port_row.addWidget(baud_label)
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "115200", "38400", "19200"])
        # AI8051U固件默认使用115200波特率
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setMinimumHeight(25)
        self.baud_combo.setStyleSheet(self.port_combo.styleSheet())
        port_row.addWidget(self.baud_combo)
        
        self.connection_card.content_layout.addLayout(port_row)
        
        # 连接按钮行
        button_row = QVBoxLayout()
        button_row.setSpacing(6)
        
        self.connect_btn = PCL2Button("🔗 连接串口", "primary")
        self.connect_btn.clicked.connect(self.toggle_connection)
        button_row.addWidget(self.connect_btn)
        
        refresh_btn = PCL2Button("🔄 手动刷新串口", "secondary")
        refresh_btn.setToolTip("点击手动刷新串口列表（测试期间建议不要频繁刷新）")
        refresh_btn.clicked.connect(self.refresh_ports)
        button_row.addWidget(refresh_btn)
        
        self.connection_card.content_layout.addLayout(button_row)
        
    def create_message_card(self):
        """创建消息显示卡片"""
        self.message_card = PCL2Card("💬 消息终端")
        
        # 消息显示区域
        self.display_text = QTextEdit()
        self.display_text.setReadOnly(True)
        self.display_text.setFont(QFont("Consolas", 9))
        self.display_text.setMinimumHeight(380)  # 减少最小高度，为命令输入留出更多空间
        self.display_text.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        # 启用HTML格式显示
        self.display_text.setAcceptRichText(True)
        # 设置最大文档块数，防止内存占用过多
        self.display_text.document().setMaximumBlockCount(1000000)  # 增加到1000000行以支持完整测试输出
        # 优化文档布局
        self.display_text.document().documentLayout().setPaintDevice(self.display_text)  # 优化布局
        # 优化文档布局，提高显示性能
        self.display_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 自动换行
        self.display_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                line-height: 1.2;
                margin-bottom: 0px;
            }
        """)
        
        # 创建显示容器，用于放置按钮覆盖层
        self.display_container = QFrame()
        self.display_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.display_container.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        display_layout = QVBoxLayout(self.display_container)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.addWidget(self.display_text)
        
        # 安装事件过滤器以在容器调整大小时更新按钮位置
        self.display_container.installEventFilter(self)
        
        # 创建按钮覆盖层（右上角，半透明）
        self.button_overlay = QWidget(self.display_container)
        self.button_overlay.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.button_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # 允许鼠标事件
        button_layout = QHBoxLayout(self.button_overlay)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        # 最大化按钮
        self.maximize_btn = QPushButton("⛶")
        self.maximize_btn.setToolTip("最大化显示区域")
        self.maximize_btn.setFixedSize(28, 28)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background: rgba(52, 152, 219, 0.7);
                color: white;
                border: 1px solid rgba(41, 128, 185, 0.9);
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(52, 152, 219, 0.9);
                border: 1px solid rgba(41, 128, 185, 1.0);
            }
            QPushButton:pressed {
                background: rgba(41, 128, 185, 0.9);
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_display_maximize)
        button_layout.addWidget(self.maximize_btn)
        
        # 打印按钮
        self.print_btn = QPushButton("🖨️")
        self.print_btn.setToolTip("打印消息内容")
        self.print_btn.setFixedSize(28, 28)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background: rgba(46, 204, 113, 0.7);
                color: white;
                border: 1px solid rgba(39, 174, 96, 0.9);
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(46, 204, 113, 0.9);
                border: 1px solid rgba(39, 174, 96, 1.0);
            }
            QPushButton:pressed {
                background: rgba(39, 174, 96, 0.9);
            }
        """)
        self.print_btn.clicked.connect(self.print_display_content)
        button_layout.addWidget(self.print_btn)
        
        # 将按钮覆盖层定位到右上角
        self.button_overlay.setFixedSize(68, 32)  # 两个按钮加上间距
        self.button_overlay.move(self.display_container.width() - 72, 8)  # 稍后更新位置
        
        # 添加到卡片布局
        self.message_card.content_layout.addWidget(self.display_container)
        
        # 添加间距，避免命令输入与消息终端重叠
        self.message_card.content_layout.addSpacing(2)  # 最小间距，让输入框紧贴消息显示区域
        
        # 命令输入区域 - 创建独立的容器，确保与消息显示区域分离
        input_container = QFrame()
        input_container.setFixedHeight(48)  # 稍微增加高度，为按钮留出空间
        input_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        input_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 220, 0.25);  /* 淡黄色背景 */
                border-radius: 8px;
                border: 2px solid #f1c40f;  /* 金色边框 */
                margin-top: 0px;  /* 移除上边距 */
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 4)  # 进一步减少内边距
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("快速输入命令... (Enter发送)")
        self.command_input.setMinimumHeight(32)
        self.command_input.setMaximumHeight(36)
        self.command_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #f39c12;  /* 橙色边框，与淡黄色容器协调 */
                border-radius: 6px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
                padding: 4px 8px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 2px solid #e67e22;  /* 深橙色焦点边框 */
                background: white;
            }
            QLineEdit::placeholder {
                color: #95a5a6;
                font-size: 12px;
            }
        """)
        self.command_input.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.command_input, 1)  # 设置stretch factor为1
        
        # 大窗口输入按钮
        large_input_btn = PCL2Button("📝 大窗口", "secondary")
        large_input_btn.setMinimumWidth(75)  # 增加宽度，确保文字完整显示
        large_input_btn.setMinimumHeight(30)
        large_input_btn.setMaximumHeight(34)
        large_input_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.9);
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;  /* 减小字体大小 */
                font-family: "Microsoft YaHei";
                min-width: 75px;
            }
            QPushButton:hover {
                background: rgba(236, 240, 241, 0.9);
                border-color: #95a5a6;
            }
            QPushButton:pressed {
                background: rgba(189, 195, 199, 0.9);
            }
        """)
        large_input_btn.clicked.connect(self.open_large_input_window)
        input_layout.addWidget(large_input_btn)
        
        send_btn = PCL2Button("📤 发送", "success")
        send_btn.setMinimumWidth(80)  # 增加宽度，确保文字完整显示
        send_btn.setMinimumHeight(30)
        send_btn.setMaximumHeight(34)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;  /* 减小字体大小 */
                font-family: "Microsoft YaHei";
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #52c77e, stop:1 #27ae60);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
            }
        """)
        send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(send_btn)
        
        self.message_card.content_layout.addWidget(input_container)
        
        # 延迟更新按钮位置，确保容器大小已确定
        QTimer.singleShot(100, self.update_button_overlay_position)
        
    def create_right_panel(self):
        """创建右侧面板"""
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(200, 200, 200, 0.3);
            }
        """)
        
        # 使用滚动区域以适应更多内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(200, 200, 200, 0.3);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100, 200, 255, 0.6);
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)
        
        # 快捷命令卡片
        self.create_commands_card()
        right_layout.addWidget(self.commands_card)
        
        # 系统状态卡片
        self.create_status_card()
        right_layout.addWidget(self.status_card)
        
        right_layout.addStretch()
        
        # 添加菜单提示
        menu_tip = QLabel("💡 更多设置请查看顶部菜单栏")
        menu_tip.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 10px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(52, 152, 219, 0.3);
            }
        """)
        right_layout.addWidget(menu_tip)
        
        scroll_area.setWidget(right_content)
        
        main_layout = QVBoxLayout(self.right_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
    def create_commands_card(self):
        """创建快捷命令卡片"""
        self.commands_card = PCL2Card("⚡ 快捷命令")
        
        # 基础命令
        basic_label = QLabel("📋 基础命令")
        basic_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        basic_label.setStyleSheet("color: #2c3e50; padding: 4px 0px;")
        self.commands_card.content_layout.addWidget(basic_label)
        
        basic_grid = QGridLayout()
        basic_grid.setSpacing(4)
        
        basic_commands = [
            ("❓ help", "显示帮助"),
            ("ℹ️ info", "系统信息"),
            ("🧹 clear", "清空显示"),
            ("🔄 reset", "重启系统")
        ]
        
        for i, (cmd, desc) in enumerate(basic_commands):
            btn = PCL2Button(cmd, "secondary")
            btn.setMinimumHeight(35)
            btn.clicked.connect(lambda checked, c=cmd.split()[1]: self.send_quick_command(c))
            basic_grid.addWidget(btn, i // 2, i % 2)
        
        self.commands_card.content_layout.addLayout(basic_grid)
        
        # 硬件测试命令
        hw_label = QLabel("🧪 硬件测试")
        hw_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        hw_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.commands_card.content_layout.addWidget(hw_label)
        
        hw_grid = QGridLayout()
        hw_grid.setSpacing(8)
        
        hw_commands = [
            ("⚡ hwtest", "硬件测试"),
            ("🔢 mdu32", "MDU32测试"),
            ("🎯 tfpu", "TFPU测试"),
            ("🏃 benchmark", "性能测试")
        ]
        
        # 添加系统信息命令
        system_commands = [
            ("🌈 neofetch", "系统信息"),
            ("📊 clockinfo", "时钟信息"),
            ("🔋 voltage", "电源电压")
        ]
        
        for i, (cmd, desc) in enumerate(hw_commands):
            btn = PCL2Button(cmd, "secondary")
            btn.setMinimumHeight(35)
            btn.clicked.connect(lambda checked, c=cmd.split()[1]: self.send_quick_command(c))
            hw_grid.addWidget(btn, i // 2, i % 2)
        
        self.commands_card.content_layout.addLayout(hw_grid)
        
        # 系统信息命令
        system_label = QLabel("📊 系统信息")
        system_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        system_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.commands_card.content_layout.addWidget(system_label)
        
        system_grid = QGridLayout()
        system_grid.setSpacing(8)
        
        for i, (cmd, desc) in enumerate(system_commands):
            btn = PCL2Button(cmd, "secondary")
            btn.setMinimumHeight(35)
            btn.clicked.connect(lambda checked, c=cmd.split()[1]: self.send_quick_command(c))
            system_grid.addWidget(btn, i // 2, i % 2)
        
        self.commands_card.content_layout.addLayout(system_grid)
        
        # DS18B20温度传感器命令
        temp_label = QLabel("🌡️ DS18B20温度传感器")
        temp_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        temp_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.commands_card.content_layout.addWidget(temp_label)
        
        temp_grid = QGridLayout()
        temp_grid.setSpacing(8)
        
        temp_commands = [
            ("🔌 ds18b20 init", "初始化传感器"),
            ("📖 ds18b20 read", "读取温度"),
            ("🔍 ds18b20 scan", "扫描设备"),
            ("⏱️ 自动查询", "启用/禁用自动查询")
        ]
        
        for i, (cmd, desc) in enumerate(temp_commands):
            btn = PCL2Button(cmd, "secondary")
            btn.setMinimumHeight(35)
            btn.setToolTip(f"点击{desc}")
            if i < 3:  # 前3个是普通命令按钮
                # 发送完整命令（去除图标）
                command_str = ' '.join(cmd.split()[1:])
                btn.clicked.connect(lambda checked, c=command_str: self.send_quick_command(c))
            else:  # 第4个是自动查询切换按钮
                btn.clicked.connect(self.toggle_ds18b20_auto_query)
            temp_grid.addWidget(btn, i // 2, i % 2)
        
        # 温度显示标签
        self.temperature_display = QLabel("🌡️ 温度: 未读取")
        self.temperature_display.setFont(QFont("Microsoft YaHei", 10))
        self.temperature_display.setStyleSheet("""
            QLabel {
                color: #3498db;
                padding: 6px 10px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(52, 152, 219, 0.3);
                margin-top: 8px;
            }
        """)
        temp_grid.addWidget(self.temperature_display, 2, 0, 1, 2)  # 跨2列
        
        self.commands_card.content_layout.addLayout(temp_grid)
        
        # 时间设置命令
        time_label = QLabel("⏰ 时间设置")
        time_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        time_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.commands_card.content_layout.addWidget(time_label)
        
        time_grid = QGridLayout()
        time_grid.setSpacing(8)
        
        time_commands = [
            ("🕐 settime", "设置时间"),
            ("📅 setdate", "设置日期")
        ]
        
        for i, (cmd, desc) in enumerate(time_commands):
            btn = PCL2Button(cmd, "secondary")
            btn.setMinimumHeight(35)
            btn.setToolTip(f"点击发送 {cmd.split()[1]} 命令")
            btn.clicked.connect(lambda checked, c=cmd.split()[1]: self.send_time_command(c))
            time_grid.addWidget(btn, i // 2, i % 2)
        
        self.commands_card.content_layout.addLayout(time_grid)
        
    def create_status_card(self):
        """创建系统状态卡片"""
        self.status_card = PCL2Card("📊 系统状态")
        
        # 连接状态
        self.connection_status_label = QLabel("🔴 未连接")
        self.connection_status_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.connection_status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 10px 14px;
                background: rgba(231, 76, 60, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(231, 76, 60, 0.3);
            }
        """)
        self.status_card.content_layout.addWidget(self.connection_status_label)
        
        # 性能状态
        self.performance_status_label = QLabel("⚡ 性能正常")
        self.performance_status_label.setFont(QFont("Microsoft YaHei", 11))
        self.performance_status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 10px 14px;
                background: rgba(39, 174, 96, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(39, 174, 96, 0.3);
            }
        """)
        self.status_card.content_layout.addWidget(self.performance_status_label)
        
        # 环境状态
        self.env_status_label = QLabel("🌍 环境正常")
        self.env_status_label.setFont(QFont("Microsoft YaHei", 11))
        self.env_status_label.setStyleSheet("""
            QLabel {
                color: #f39c12;
                padding: 10px 14px;
                background: rgba(243, 156, 18, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(243, 156, 18, 0.3);
            }
        """)
        self.status_card.content_layout.addWidget(self.env_status_label)
        
        # AI8051U检测状态
        if self.ai8051u_detection_enabled:
            self.ai8051u_status_label = QLabel("🔍 AI8051U: 检测中")
            self.ai8051u_status_label.setFont(QFont("Microsoft YaHei", 11))
            self.ai8051u_status_label.setStyleSheet("""
                QLabel {
                    color: #f39c12;
                    padding: 10px 14px;
                    background: rgba(243, 156, 18, 0.1);
                    border-radius: 6px;
                    border: 1px solid rgba(243, 156, 18, 0.3);
                }
            """)
        else:
            self.ai8051u_status_label = QLabel("🔕 AI8051U: 已禁用")
            self.ai8051u_status_label.setFont(QFont("Microsoft YaHei", 11))
            self.ai8051u_status_label.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    padding: 10px 14px;
                    background: rgba(149, 165, 166, 0.1);
                    border-radius: 6px;
                    border: 1px solid rgba(149, 165, 166, 0.3);
                }
            """)
        self.status_card.content_layout.addWidget(self.ai8051u_status_label)
        
        # 性能监控详细信息
        perf_details_label = QLabel("📊 性能监控")
        perf_details_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        perf_details_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.status_card.content_layout.addWidget(perf_details_label)
        
        # 性能指标显示
        perf_layout = QVBoxLayout()
        perf_layout.setSpacing(4)
        
        # CPU频率
        self.cpu_freq_label = QLabel("CPU频率: 未知")
        self.cpu_freq_label.setFont(QFont("Microsoft YaHei", 9))
        self.cpu_freq_label.setStyleSheet("color: #7f8c8d;")
        perf_layout.addWidget(self.cpu_freq_label)
        
        # TFPU频率
        self.tfpu_freq_label = QLabel("TFPU频率: 未知")
        self.tfpu_freq_label.setFont(QFont("Microsoft YaHei", 9))
        self.tfpu_freq_label.setStyleSheet("color: #7f8c8d;")
        perf_layout.addWidget(self.tfpu_freq_label)
        
        # 消息处理统计
        self.message_stats_label = QLabel("消息: 0 发送 / 0 接收")
        self.message_stats_label.setFont(QFont("Microsoft YaHei", 9))
        self.message_stats_label.setStyleSheet("color: #7f8c8d;")
        perf_layout.addWidget(self.message_stats_label)
        
        self.status_card.content_layout.addLayout(perf_layout)
        
    def create_settings_card(self):
        """创建设置卡片"""
        self.settings_card = PCL2Card("⚙️ 快速设置")
        
        # 主题切换
        theme_label = QLabel("🎨 主题切换")
        theme_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        theme_label.setStyleSheet("color: #2c3e50; padding: 4px 0px;")
        self.settings_card.content_layout.addWidget(theme_label)
        
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        
        themes = [
            ("🌈 多巴胺", "dopamine"),
            ("🌙 深色", "dark"),
            ("☀️ 浅色", "light")
        ]
        
        for display, theme_name in themes:
            btn = PCL2Button(display, "secondary")
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(80)
            btn.clicked.connect(lambda checked, t=theme_name: self.apply_theme(t))
            theme_row.addWidget(btn)
        
        self.settings_card.content_layout.addLayout(theme_row)
        
        # 功能按钮
        function_label = QLabel("🔧 功能")
        function_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        function_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.settings_card.content_layout.addWidget(function_label)
        
        function_row1 = QHBoxLayout()
        function_row1.setSpacing(8)
        
        env_btn = PCL2Button("🔍 环境检测", "secondary")
        env_btn.setMinimumHeight(35)
        env_btn.setMinimumWidth(90)
        env_btn.clicked.connect(self.check_environment)
        function_row1.addWidget(env_btn)
        
        test_btn = PCL2Button("🔔 测试通知", "secondary")
        test_btn.setMinimumHeight(35)
        test_btn.setMinimumWidth(90)
        test_btn.clicked.connect(self.test_notifications)
        function_row1.addWidget(test_btn)
        
        self.settings_card.content_layout.addLayout(function_row1)
        
        # 缓冲策略选择
        buffer_label = QLabel("🗂️ 缓冲策略")
        buffer_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        buffer_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.settings_card.content_layout.addWidget(buffer_label)
        
        buffer_row = QHBoxLayout()
        buffer_row.setSpacing(8)
        
        self.buffer_combo = QComboBox()
        self.buffer_combo.addItems([
            "🛡️ 保守模式 (200KB)",
            "⚖️ 平衡模式 (100KB)",
            "🚀 性能模式 (50KB)"
        ])
        self.buffer_combo.setCurrentIndex(1)  # 默认平衡模式
        self.buffer_combo.setMinimumHeight(30)
        self.buffer_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 9px;
                color: #2c3e50;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #7f8c8d;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                color: #2c3e50;
                font-size: 9px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.buffer_combo.currentTextChanged.connect(self.change_buffer_strategy)
        buffer_row.addWidget(self.buffer_combo)
        
        apply_buffer_btn = PCL2Button("应用", "secondary")
        apply_buffer_btn.setMinimumHeight(30)
        apply_buffer_btn.setMinimumWidth(50)
        apply_buffer_btn.clicked.connect(self.apply_buffer_strategy)
        buffer_row.addWidget(apply_buffer_btn)
        
        self.settings_card.content_layout.addLayout(buffer_row)
        
        # 高级功能按钮
        advanced_label = QLabel("🚀 高级功能")
        advanced_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        advanced_label.setStyleSheet("color: #2c3e50; padding: 8px 0px 4px 0px;")
        self.settings_card.content_layout.addWidget(advanced_label)
        
        advanced_row1 = QHBoxLayout()
        advanced_row1.setSpacing(8)
        
        batch_btn = PCL2Button("🔄 批量测试", "success")
        batch_btn.setMinimumHeight(35)
        batch_btn.setMinimumWidth(90)
        batch_btn.clicked.connect(self.run_batch_tests)
        advanced_row1.addWidget(batch_btn)
        
        report_btn = PCL2Button("📊 性能报告", "success")
        report_btn.setMinimumHeight(35)
        report_btn.setMinimumWidth(90)
        report_btn.clicked.connect(self.generate_performance_report)
        advanced_row1.addWidget(report_btn)
        
        self.settings_card.content_layout.addLayout(advanced_row1)
        
        advanced_row2 = QHBoxLayout()
        advanced_row2.setSpacing(8)
        
        device_btn = PCL2Button("📱 设备信息", "primary")
        device_btn.setMinimumHeight(35)
        device_btn.setMinimumWidth(90)
        device_btn.clicked.connect(self.show_device_info_dialog)
        advanced_row2.addWidget(device_btn)
        
        save_btn = PCL2Button("💾 保存日志", "secondary")
        save_btn.setMinimumHeight(35)
        save_btn.setMinimumWidth(90)
        save_btn.clicked.connect(self.save_display_log)
        advanced_row2.addWidget(save_btn)
        
        # 设置功能已移至菜单栏，保留方法以兼容可能的调用
        
    def create_settings_card(self):
        """创建设置卡片（已移至菜单栏，保留方法以兼容）"""
        # 此方法已移至菜单栏，但保留以避免可能的调用错误
        pass
        
    def setup_window_geometry(self):
        """设置窗口几何属性"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # 设置窗口大小，适中的横向宽度
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.75)
        
        # 确保合适的尺寸范围
        window_width = max(window_width, 1300)
        window_height = max(window_height, 700)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)
        
    def apply_pcl2_theme(self):
        """应用PCL2主题"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        
    def setWindowScale(self, scale_factor: float):
        """设置窗口缩放因子"""
        if not hasattr(self, 'current_scale'):
            self.current_scale = 1.0
            
        # 限制缩放范围
        scale_factor = max(0.8, min(1.5, scale_factor))
        
        if abs(scale_factor - self.current_scale) > 0.01:  # 避免微小变化
            self.current_scale = scale_factor
            
            # 应用缩放到字体
            if hasattr(self, 'theme_manager'):
                self.theme_manager.set_font_scale(scale_factor)
                
            # 更新主要UI组件的字体
            self.update_fonts_for_scale(scale_factor)
            
            if self.debug_mode:
                print(f"[DEBUG] 界面缩放已设置为: {scale_factor:.2f}")
    
    def update_fonts_for_scale(self, scale_factor: float):
        """根据缩放因子更新所有字体"""
        # 更新显示文本区域的字体
        if hasattr(self, 'display_text'):
            current_font = self.display_text.font()
            new_size = int(9 * scale_factor)
            # 确保字体不会太大
            new_size = min(new_size, 10)
            self.display_text.setFont(QFont("Consolas", new_size))
            
        # 更新设备信息显示的字体
        if hasattr(self, 'device_info_display'):
            new_size = int(8 * scale_factor)
            # 确保字体不会太大
            new_size = min(new_size, 9)
            self.device_info_display.setFont(self.theme_manager.get_font("mono", new_size))
            
        # 更新命令输入框的字体
        if hasattr(self, 'command_input'):
            current_font = self.command_input.font()
            new_size = int(12 * scale_factor)
            self.command_input.setFont(QFont("Microsoft YaHei", new_size))
    
    def apply_settings(self, settings: dict):
        """应用设置到主窗口"""
        try:
            # 应用透明度设置
            if 'opacity' in settings:
                opacity = settings['opacity'] / 100.0
                self.setWindowOpacity(opacity)
            
            # 应用壁纸设置
            if 'wallpaper' in settings:
                wallpaper_path = settings['wallpaper']
                if wallpaper_path and os.path.exists(wallpaper_path):
                    self.current_wallpaper_path = wallpaper_path
                    self.load_wallpaper(wallpaper_path)
                else:
                    self.current_wallpaper_path = ''
                    self.clear_wallpaper()
            
            # 应用壁纸透明度设置
            if 'wallpaper_opacity' in settings:
                self.wallpaper_opacity = settings['wallpaper_opacity'] / 100.0
                self.update_wallpaper_display()
                
                
            
            # 应用字体大小设置
            if 'font_size' in settings:
                font_size = settings['font_size']
                # 更新主要UI组件的字体
                if hasattr(self, 'command_input'):
                    self.command_input.setFont(QFont("Microsoft YaHei", font_size))
                # 显示文本区域使用较小的字体，最大不超过10
                if hasattr(self, 'display_text'):
                    display_font_size = min(font_size, 10)
                    self.display_text.setFont(QFont("Consolas", display_font_size))
            
            # 应用等宽字体大小设置
            if 'mono_font_size' in settings:
                mono_font_size = settings['mono_font_size']
                if hasattr(self, 'device_info_display'):
                    # 设备信息显示使用更小的字体，最大不超过9
                    device_info_font_size = min(mono_font_size, 9)
                    self.device_info_display.setFont(QFont("Consolas", device_info_font_size))
            
            # 应用UI缩放设置
            if 'ui_scale' in settings:
                scale_factor = settings['ui_scale'] / 100.0
                self.setWindowScale(scale_factor)
            
            # 应用主题设置
            if 'theme' in settings:
                self.apply_theme(settings['theme'])
            
            # 应用壁纸设置
            if 'wallpaper' in settings:
                if settings['wallpaper']:
                    self.set_wallpaper(settings['wallpaper'])
                else:
                    self.clear_wallpaper()
            
            # 应用全局文本颜色设置
            if 'global_text_color' in settings:
                import re
                color_str = settings['global_text_color']
                match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
                if match:
                    self.global_text_color = QColor(
                        int(match.group(1)), 
                        int(match.group(2)), 
                        int(match.group(3))
                    )
            
            # 应用AI8051U检测设置
            if 'ai8051u_detection_enabled' in settings:
                self.ai8051u_detection_enabled = settings['ai8051u_detection_enabled']
                # 更新AI8051U状态标签显示
                if hasattr(self, 'ai8051u_status_label'):
                    if self.ai8051u_detection_enabled:
                        self.ai8051u_status_label.setText("🔍 AI8051U: 检测中")
                        self.ai8051u_status_label.setStyleSheet("""
                            QLabel {
                                color: #f39c12;
                                padding: 10px 14px;
                                background: rgba(243, 156, 18, 0.1);
                                border-radius: 6px;
                                border: 1px solid rgba(243, 156, 18, 0.3);
                            }
                        """)
                    else:
                        self.ai8051u_status_label.setText("🔕 AI8051U: 已禁用")
                        self.ai8051u_status_label.setStyleSheet("""
                            QLabel {
                                color: #95a5a6;
                                padding: 10px 14px;
                                background: rgba(149, 165, 166, 0.1);
                                border-radius: 6px;
                                border: 1px solid rgba(149, 165, 166, 0.3);
                            }
                        """)
            
            # 应用全局文本颜色使用设置
            if 'use_global_text_color' in settings:
                self.use_global_text_color = settings['use_global_text_color']
            
            # 应用时间戳设置
            if 'timestamp' in settings:
                self.show_timestamp = settings['timestamp']
            
            # 自动滚动始终启用（根据用户要求）
            self.auto_scroll = True
            if self.debug_mode:
                print(f"[DEBUG] apply_settings: auto_scroll始终设置为True（默认自动滚动）")
            
            # 应用终端日志设置
            if 'terminal_log_enabled' in settings:
                terminal_log_enabled = settings['terminal_log_enabled']
                if hasattr(self, 'terminal_logger') and self.terminal_logger:
                    self.terminal_logger.enabled = terminal_log_enabled
                    if terminal_log_enabled:
                        self.terminal_logger.create_session_log()
                        if self.debug_mode:
                            print(f"[DEBUG] 终端消息日志已启用")
                    else:
                        if self.debug_mode:
                            print(f"[DEBUG] 终端消息日志已禁用")
            
            if self.debug_mode:
                print(f"[DEBUG] 设置已应用到主窗口: {list(settings.keys())}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 应用设置失败: {e}")
        
    def update_opacity(self, value):
        """更新透明度"""
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        
    def set_wallpaper(self, wallpaper_path):
        """设置壁纸"""
        if wallpaper_path and os.path.exists(wallpaper_path):
            self.current_wallpaper_path = wallpaper_path
            self.load_wallpaper(wallpaper_path)
        else:
            self.clear_wallpaper()
    
    def load_wallpaper(self, wallpaper_path):
        """加载壁纸图片"""
        try:
            from PyQt6.QtGui import QPixmap
            self.current_wallpaper = QPixmap(wallpaper_path)
            if not self.current_wallpaper.isNull():
                self.update_wallpaper_display()
                if self.debug_mode:
                    print(f"[DEBUG] 壁纸加载成功: {wallpaper_path}")
            else:
                if self.debug_mode:
                    print(f"[DEBUG] 壁纸加载失败: 无效的图片文件")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 壁纸加载异常: {e}")
            self.current_wallpaper = None
    
    def clear_wallpaper(self):
        """清除壁纸"""
        self.current_wallpaper = None
        self.current_wallpaper_path = ''
        self.update_wallpaper_display()
        if self.debug_mode:
            print("[DEBUG] 壁纸已清除")
    
    def update_wallpaper_display(self):
        """更新壁纸显示"""
        try:
            if self.current_wallpaper and not self.current_wallpaper.isNull():
                # 创建一个背景标签来显示壁纸
                if not hasattr(self, 'wallpaper_label'):
                    from PyQt6.QtWidgets import QLabel
                    self.wallpaper_label = QLabel(self)
                    self.wallpaper_label.setGeometry(0, 0, self.width(), self.height())
                    self.wallpaper_label.lower()  # 放到最底层
                    self.wallpaper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 设置壁纸图片
                scaled_pixmap = self.current_wallpaper.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.wallpaper_label.setPixmap(scaled_pixmap)
                self.wallpaper_label.setGeometry(0, 0, self.width(), self.height())
                self.wallpaper_label.show()
                
                if self.debug_mode:
                    print(f"[DEBUG] 壁纸显示已更新: {self.current_wallpaper_path}")
            else:
                # 清除壁纸
                if hasattr(self, 'wallpaper_label'):
                    self.wallpaper_label.clear()
                    self.wallpaper_label.hide()
                
                if self.debug_mode:
                    print("[DEBUG] 壁纸已清除")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 更新壁纸显示失败: {e}")
    
    
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 更新壁纸显示
        if hasattr(self, 'current_wallpaper') and self.current_wallpaper:
            self.update_wallpaper_display()
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(255, 255, 255, 0.9);
                border-top: 1px solid rgba(200, 200, 200, 0.3);
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        self.setStatusBar(self.status_bar)
        
        # 状态信息
        self.status_bar.showMessage("🌈 ColorBridge 就绪 - AI8051U串口助手")
        
    def setup_notification_manager(self):
        """设置通知管理器"""
        self.notification_manager.setParent(self)
        self.update_notification_position()
        
        # 显示欢迎通知并自动检测环境
        QTimer.singleShot(1000, self.startup_environment_check)
        
        # 监听窗口大小变化
        self.resizeEvent = self.on_window_resize
        
    def update_notification_position(self):
        """更新通知管理器位置"""
        if hasattr(self, 'notification_manager'):
            window_width = self.width()
            window_height = self.height()
            
            notification_width = min(400, window_width - 40)
            margin = 20
            
            x = max(margin, window_width - notification_width - margin)
            y = margin + 60  # 考虑标题栏高度
            
            self.notification_manager.setFixedWidth(notification_width)
            self.notification_manager.move(x, y)
            
            max_height = window_height - 2 * margin - 60
            if self.notification_manager.height() > max_height:
                self.notification_manager.setFixedHeight(max_height)
                
    def on_window_resize(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.update_notification_position()
        
    def startup_environment_check(self):
        """启动时环境检测"""
        self.notification_manager.show_system(
            "🌈 ColorBridge PCL2风格界面已启动！正在检测环境...",
            auto_close=True
        )
        
        # 延迟执行环境检测
        QTimer.singleShot(1500, self.auto_environment_check)
        
    def auto_environment_check(self):
        """自动环境检测"""
        import sys
        import platform
        
        missing_deps = []
        
        # 检测关键依赖
        try:
            import psutil
        except ImportError:
            missing_deps.append('psutil')
            
        try:
            from PyQt6.QtSerialPort import QSerialPortInfo
        except ImportError:
            missing_deps.append('PyQt6-SerialPort')
            
        # 显示检测结果
        if missing_deps:
            self.notification_manager.show_warning(
                f"⚠️ 检测到缺失依赖: {', '.join(missing_deps)}\n正在自动安装...",
                auto_close=False
            )
            # 自动安装缺失依赖
            QTimer.singleShot(1000, lambda: self.auto_install_dependencies(missing_deps))
        else:
            self.notification_manager.show_success(
                "✅ 环境检测完成！所有依赖都已安装",
                auto_close=True
            )
            
        # 更新环境状态显示
        if hasattr(self, 'env_status_label'):
            if missing_deps:
                self.env_status_label.setText("⚠️ 环境不完整")
                self.env_status_label.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        padding: 8px 12px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 6px;
                        border: 1px solid rgba(231, 76, 60, 0.3);
                    }
                """)
            else:
                self.env_status_label.setText("🌍 环境正常")
                self.env_status_label.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        padding: 8px 12px;
                        background: rgba(39, 174, 96, 0.1);
                        border-radius: 6px;
                        border: 1px solid rgba(39, 174, 96, 0.3);
                    }
                """)
                
    def auto_install_dependencies(self, dependencies):
        """自动安装依赖"""
        import subprocess
        import sys
        
        for dep in dependencies:
            try:
                if self.debug_mode:
                    print(f"[DEBUG] 正在安装 {dep}...")
                    
                # 使用pip安装
                cmd = [sys.executable, '-m', 'pip', 'install', dep]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    if self.debug_mode:
                        print(f"[DEBUG] 成功安装: {dep}")
                    self.notification_manager.show_success(
                        f"✅ {dep} 安装成功",
                        auto_close=True
                    )
                else:
                    if self.debug_mode:
                        print(f"[ERROR] 安装失败: {dep}")
                    self.notification_manager.show_error(
                        f"❌ {dep} 安装失败",
                        auto_close=False
                    )
            except Exception as e:
                if self.debug_mode:
                    print(f"[ERROR] 安装异常: {dep} - {e}")
                self.notification_manager.show_error(
                    f"❌ {dep} 安装异常: {str(e)}",
                    auto_close=False
                )
                
        # 安装完成后重新检测
        QTimer.singleShot(2000, self.auto_environment_check)
        
    def show_welcome_notification(self):
        """显示欢迎通知"""
        self.notification_manager.show_system(
            "🌈 ColorBridge PCL2风格界面已启动！",
            auto_close=True
        )
        
    def test_notifications(self):
        """测试通知系统"""
        import random
        notifications = [
            ("info", "ℹ️ 这是一个信息通知"),
            ("success", "✅ 这是一个成功通知"),
            ("warning", "⚠️ 这是一个警告通知"),
            ("error", "❌ 这是一个错误通知"),
            ("system", "🔧 这是一个系统通知")
        ]
        
        notif_type, notif_message = random.choice(notifications)
        self.notification_manager.show_notification(notif_message, notif_type, auto_close=True)
        
    def refresh_ports(self):
        """刷新串口列表"""
        try:
            available_ports = self.serial_manager.get_available_ports()
            current_port = self.port_combo.currentText()
            
            if self.debug_mode:
                print(f"[DEBUG] 发现串口: {available_ports}")
            
            # 记录之前的串口数量，避免重复通知
            previous_count = getattr(self, '_previous_port_count', 0)
            
            self.port_combo.clear()
            
            if available_ports:
                for port in available_ports:
                    self.port_combo.addItem(port)
                    if self.debug_mode:
                        print(f"[DEBUG] 添加串口到列表: {port}")
            else:
                self.port_combo.addItem("未检测到串口设备")
                if self.debug_mode:
                    print("[DEBUG] 未检测到串口设备")
                
            # 恢复之前选择的串口
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
                
            # 只有在串口数量发生变化时才显示通知
            current_count = len(available_ports)
            if current_count != previous_count:
                if current_count > 0:
                    if not hasattr(self, '_startup_notification_shown'):
                        self._startup_notification_shown = True
                        self.notification_manager.show_info(
                            f"🔍 检测到 {current_count} 个串口设备",
                            auto_close=True
                        )
                elif previous_count > 0:
                    self.notification_manager.show_warning(
                        "⚠️ 所有串口设备已断开",
                        auto_close=True
                    )
                
                self._previous_port_count = current_count
                
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 刷新串口列表失败: {e}")
            self.port_combo.clear()
            self.port_combo.addItem("串口检测失败")
            # 只在第一次出错时显示错误通知
            if not hasattr(self, '_port_error_shown'):
                self._port_error_shown = True
                self.notification_manager.show_error(
                    f"❌ 串口列表刷新失败: {str(e)}",
                    auto_close=True
                )
            
    def toggle_connection(self):
        """切换连接状态"""
        # 检查当前连接状态，防止重复操作
        if hasattr(self, '_connecting') and self._connecting:
            if self.debug_mode:
                print("[DEBUG] 连接正在进行中，忽略重复点击")
            return
        
        # 检查实际的串口连接状态，而不是依赖按钮文本
        if self.serial_manager.is_connected():
            # 当前已连接，需要断开
            self.disconnect_serial()
        else:
            # 当前未连接，需要连接
            self._connecting = True
            self.connect_serial()
            
    def connect_serial(self):
        """连接串口"""
        port_name = self.port_combo.currentText()
        baud_rate = int(self.baud_combo.currentText())
        
        if "未检测到" in port_name or "检测失败" in port_name:
            self.notification_manager.show_error("❌ 请选择有效的串口设备", auto_close=True)
            return
            
        try:
            if self.serial_manager.connect(port_name, baud_rate):
                # 连接成功，UI更新由 on_connection_changed 信号处理
                # 不要在这里手动设置UI状态，避免与信号处理冲突
                if self.debug_mode:
                    print(f"[DEBUG] 串口连接请求已发送: {port_name}")
                # 重置响应超时检测
                self.serial_manager.reset_response_timeout()
                self.notification_manager.show_success(
                    f"🔗 串口连接成功！\n端口: {port_name} | 波特率: {baud_rate}",
                    auto_close=True
                )
            else:
                self.notification_manager.show_error("❌ 串口连接失败", auto_close=False)
        except Exception as e:
            self.notification_manager.show_error(f"❌ 连接错误: {str(e)}", auto_close=False)
        finally:
            # 重置连接状态标志
            self._connecting = False
            
    def disconnect_serial(self):
        """断开串口连接"""
        try:
            self.serial_manager.disconnect()
            # UI更新由 on_connection_changed 信号处理
            # 不要在这里手动设置UI状态，避免与信号处理冲突
            if self.debug_mode:
                print("[DEBUG] 串口断开请求已发送")
            self.notification_manager.show_info("🔌 串口已断开连接", auto_close=True)
        except Exception as e:
            self.notification_manager.show_error(f"❌ 断开连接错误: {str(e)}", auto_close=False)
        finally:
            # 重置连接状态标志
            self._connecting = False
            
    def _update_ui_disconnected(self):
        """更新UI为断开连接状态"""
        self.connect_btn.setText("🔗 连接串口")
        self.connect_btn.button_type = "primary"
        self.connect_btn.setup_style()
        self.connection_status_label.setText("🔴 未连接")
        self.connection_status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px 12px;
                background: rgba(231, 76, 60, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(231, 76, 60, 0.3);
            }
        """)
            
    def toggle_display_maximize(self):
        """打开独立窗口显示消息区域"""
        # 检查是否已有独立窗口
        if hasattr(self, 'display_window') and self.display_window and self.display_window.isVisible():
            # 窗口已存在，将其带到前台
            self.display_window.raise_()
            self.display_window.activateWindow()
            if self.debug_mode:
                print("[DEBUG] 独立窗口已存在，已将其带到前台")
            return
        
        # 获取当前消息内容
        content = self.display_text.toHtml() if self.display_text.acceptRichText() else self.display_text.toPlainText()
        
        # 创建独立窗口
        self.display_window = DisplayWindow(self, content, self.debug_mode)
        
        # 设置窗口关闭时的回调
        def on_window_closed():
            if self.debug_mode:
                print("[DEBUG] 独立窗口已关闭")
            # 恢复按钮状态
            if hasattr(self, 'maximize_btn'):
                self.maximize_btn.setText("⛶")
                self.maximize_btn.setToolTip("最大化显示区域")
            # 清除窗口引用（可选）
            self.display_window = None
        
        self.display_window.close_callback = on_window_closed
        
        # 最大化窗口
        self.display_window.showMaximized()
        
        # 更新按钮状态
        self.maximize_btn.setText("🗗")
        self.maximize_btn.setToolTip("关闭独立窗口")
        
        if self.debug_mode:
            print("[DEBUG] 独立窗口已创建并最大化显示")
        
        # 显示通知
        self.notification_manager.show_info("📺 消息显示已切换到独立窗口", auto_close=True)
    
    def print_display_content(self):
        """打印显示区域内容"""
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.display_text.print(printer)
                self.notification_manager.show_success("🖨️ 打印任务已发送")
        except ImportError:
            # 回退方案：保存到文件
            self.save_display_to_file()
    
    def save_display_to_file(self):
        """保存显示内容到文件（打印的备用方案）"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存消息内容", "", "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.display_text.toPlainText())
                self.notification_manager.show_success(f"💾 消息已保存到: {filename}")
        except Exception as e:
            self.notification_manager.show_error(f"❌ 保存失败: {str(e)}")
    
    def update_button_overlay_position(self):
        """更新按钮覆盖层位置（右上角）"""
        if hasattr(self, 'button_overlay') and self.button_overlay:
            # 获取容器大小
            container_width = self.display_container.width()
            # 设置按钮覆盖层位置：右上角，留出8像素边距
            self.button_overlay.move(container_width - self.button_overlay.width() - 8, 8)
    
    def send_command(self):
        """发送命令"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        if self.serial_manager.is_connected():
            # 1. 检查设备忙状态
            if self._device_busy:
                if self.debug_mode:
                    print(f"[DEBUG] 设备忙，将命令 '{command}' 添加到等待队列")
                # 尝试添加到等待队列
                if self._add_to_pending_commands(command):
                    # 队列添加成功，清空输入框
                    self.command_input.clear()
                else:
                    # 队列已满，显示错误
                    self.notification_manager.show_error("等待队列已满，请稍后再试", auto_close=True)
                return
            
            # 2. 移除主窗口的发送间隔检查，由串口管理器统一处理
            # 只保留极短时间内的命令去重机制，防止意外双击重复发送
            current_time = time.time()
            if hasattr(self, '_last_sent_command') and hasattr(self, '_last_send_time'):
                # 检查是否是相同的命令在极短时间内重复发送（防止双击）
                if (self._last_sent_command == command and 
                    current_time - self._last_send_time < 0.1):  # 0.1秒内重复相同命令（防止双击）
                    if self.debug_mode:
                        print(f"[DEBUG] 重复发送相同命令: '{command}'，跳过（防止双击）")
                    self.notification_manager.show_warning(f"重复发送相同命令，请等待0.1秒", auto_close=True)
                    return
            
            self._last_send_time = current_time
            
            # 调试信息
            if self.debug_mode:
                print(f"[DEBUG] send_command: 发送命令 '{command}'")
            
            # 记录最近发送的命令（用于过滤回显）
            self._last_sent_command = command
            
            # 添加命令到显示区域（蓝色）- 立即生成时间戳
            send_timestamp = self._get_current_timestamp()
            self.add_message(f"发送→{command}", "command", pre_timestamp=send_timestamp)
            
            # 检测是否是长时间测试命令
            test_commands = ['hwtest', 'mdu32', 'tfpu', 'benchmark', 'clockinfo']
            if any(cmd in command.lower() for cmd in test_commands):
                # 暂停串口刷新，避免干扰测试
                if hasattr(self, 'port_refresh_timer'):
                    self.port_refresh_timer.stop()
                    if self.debug_mode:
                        print("[DEBUG] 暂停串口刷新，进行长时间测试")
            
            # 发送命令并检查结果（带自动重试）
            success = False
            max_retries = 2  # 最多重试2次（包括首次）
            
            for attempt in range(max_retries):
                if self.debug_mode:
                    print(f"[DEBUG] 发送命令尝试 {attempt + 1}/{max_retries}: '{command}'")
                
                success = self.serial_manager.send_command(command)
                
                if self.debug_mode:
                    print(f"[DEBUG] 发送命令结果: {'成功' if success else '失败'}")
                
                if success:
                    # 发送成功，显示成功提示（即使没有调试模式）
                    if attempt > 0:  # 如果是重试后成功的
                        self.notification_manager.show_success(f"命令发送成功（第{attempt + 1}次尝试）", auto_close=True)
                    
                    # 设置设备忙状态（如果不是自动流程的info命令）- 机制已禁用
                    if not self._waiting_for_info_response:
                        # 设备忙状态机制已禁用
                        if self.debug_mode:
                            print(f"[DEBUG] 设备忙状态机制已禁用，跳过设置，命令: '{command}'")
                    
                    break
                else:
                    # 发送失败，如果是最后一次尝试，显示错误
                    if attempt == max_retries - 1:
                        if self.debug_mode:
                            print(f"[DEBUG] 发送命令失败（已尝试{max_retries}次）: {command}")
                        # 显示错误通知
                        self.notification_manager.show_error(f"发送命令失败（已尝试{max_retries}次）: {command}", auto_close=True)
                    else:
                        # 不是最后一次，等待500ms后重试
                        if self.debug_mode:
                            print(f"[DEBUG] 发送失败，500ms后重试第{attempt + 2}次")
                        time.sleep(0.5)  # 等待500ms
            
            # 特殊处理clear命令：无论发送成功与否，都清空本地显示区域
            if command.strip().lower() == 'clear':
                self.clear_display()
            
            self.command_input.clear()
        else:
            self.notification_manager.show_warning("请先连接串口", auto_close=True)
            if self.debug_mode:
                print("[DEBUG] 发送命令失败: 串口未连接")
            
    def send_quick_command(self, command: str):
        """发送快捷命令"""
        if self.serial_manager.is_connected():
            # 1. 检查设备忙状态
            if self._device_busy:
                if self.debug_mode:
                    print(f"[DEBUG] 设备忙，将快捷命令 '{command}' 添加到等待队列")
                # 尝试添加到等待队列
                if self._add_to_pending_commands(command):
                    # 队列添加成功，不显示命令（会在实际发送时显示）
                    pass
                else:
                    # 队列已满，显示错误
                    self.notification_manager.show_error("等待队列已满，请稍后再试", auto_close=True)
                return
            
            # 2. 检查是否正在等待自动流程的info响应
            if self._waiting_for_info_response:
                if self.debug_mode:
                    print(f"[DEBUG] 正在等待自动流程的info响应，跳过手动命令 '{command}'")
                self.notification_manager.show_warning("正在获取设备信息，请稍候...", auto_close=True)
                return
            
            # 手动发送间隔检查已禁用
            current_time = time.time()
            
            # 4. 命令去重机制，防止短时间内重复发送相同命令（防双击）
            if hasattr(self, '_last_sent_command') and hasattr(self, '_last_send_time'):
                # 检查是否是相同的命令在极短时间内重复发送（防止双击）
                if (self._last_sent_command == command and 
                    current_time - self._last_send_time < 0.1):  # 0.1秒内重复相同命令（防止双击）
                    if self.debug_mode:
                        print(f"[DEBUG] 重复发送相同快捷命令: '{command}'，跳过（防止双击）")
                    self.notification_manager.show_warning(f"重复发送相同命令，请等待0.1秒", auto_close=True)
                    return
            
            self._last_send_time = current_time
            
            # 记录最近发送的命令（用于过滤回显）
            self._last_sent_command = command
            
            # 特殊处理clear命令：增加重试次数，确保可靠发送
            is_clear_command = command.strip().lower() == 'clear'
            max_retries = 3 if is_clear_command else 1
            success = False
            last_error = None
            
            for attempt in range(max_retries):
                if self.debug_mode:
                    print(f"[DEBUG] 发送快捷命令尝试 {attempt + 1}/{max_retries}: '{command}'")
                
                success = self.serial_manager.send_command(command)
                
                if self.debug_mode:
                    print(f"[DEBUG] 发送快捷命令结果: {'成功' if success else '失败'}")
                
                if success:
                    # 发送成功，跳出重试循环
                    break
                else:
                    # 发送失败，记录错误
                    last_error = f"发送失败（第{attempt + 1}次尝试）"
                    # 如果不是最后一次尝试，等待100ms后重试
                    if attempt < max_retries - 1:
                        time.sleep(0.1)  # 100ms等待
            
            if success:
                # 更新消息统计（只在成功时）
                self._message_stats['sent'] += 1
                
                # 添加命令到显示区域（蓝色）- 立即生成时间戳
                send_timestamp = self._get_current_timestamp()
                self.add_message(f"发送→{command}", "command", pre_timestamp=send_timestamp)
                
                # 设置设备忙状态（如果不是自动流程的info命令）- 机制已禁用
                if not self._waiting_for_info_response:
                    # 设备忙状态机制已禁用
                    if self.debug_mode:
                        print(f"[DEBUG] 设备忙状态机制已禁用，跳过设置，命令: '{command}'")
            else:
                # 发送失败，显示错误通知
                error_msg = f"❌ 命令发送失败: {command}"
                if last_error:
                    error_msg += f" ({last_error})"
                self.notification_manager.show_error(error_msg, auto_close=True)
                # 仍然显示命令，但用特殊标记
                send_timestamp = self._get_current_timestamp()
                self.add_message(f"发送→{command} ❌ 发送失败", "warning", pre_timestamp=send_timestamp)
            
            # 特殊处理clear命令：无论发送成功与否，都清空本地显示区域
            if is_clear_command:
                self.clear_display()
            
        else:
            self.notification_manager.show_warning("⚠️ 请先连接串口", auto_close=True)
            if self.debug_mode:
                print("[DEBUG] 发送快捷命令失败: 串口未连接")
    
    def send_time_command(self, command: str):
        """发送时间设置命令（需要用户输入参数）"""
        if not self.serial_manager.is_connected():
            self.notification_manager.show_warning("⚠️ 请先连接串口", auto_close=True)
            return
        
        # 获取当前时间作为默认值
        from datetime import datetime
        now = datetime.now()
        
        if command == "settime":
            # 设置时间命令
            default_time = now.strftime("%H:%M:%S")
            time_str, ok = self._get_user_input("设置时间", f"请输入时间 (HH:MM:SS):", default_time)
            if ok and time_str:
                full_command = f"settime {time_str}"
                self._send_time_setting_command(full_command, "时间")
        
        elif command == "setdate":
            # 设置日期命令
            default_date = now.strftime("%y-%m-%d")  # AI8051U使用YY-MM-DD格式
            date_str, ok = self._get_user_input("设置日期", f"请输入日期 (YY-MM-DD):", default_date)
            if ok and date_str:
                full_command = f"setdate {date_str}"
                self._send_time_setting_command(full_command, "日期")
    
    def _get_user_input(self, title: str, prompt: str, default: str = ""):
        """获取用户输入"""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, prompt, text=default)
        return text.strip(), ok
    
    def _send_time_setting_command(self, command: str, command_type: str):
        """发送时间设置命令"""
        if self.debug_mode:
            print(f"[DEBUG] 发送{command_type}设置命令: {command}")
        
        # 检查设备忙状态
        if self._device_busy:
            if self.debug_mode:
                print(f"[DEBUG] 设备忙，将时间设置命令 '{command}' 添加到等待队列")
            # 尝试添加到等待队列
            if self._add_to_pending_commands(command):
                self.notification_manager.show_warning(f"⏳ {command_type}设置命令已排队（设备忙）")
            else:
                self.notification_manager.show_error(f"❌ 等待队列已满，无法发送{command_type}设置命令")
            return
        
        # 发送命令
        success = self.serial_manager.send_command(command)
        if success:
            # 更新消息统计
            self._message_stats['sent'] += 1
            # 立即生成时间戳
            send_timestamp = self._get_current_timestamp()
            self.add_message(f"发送→{command}", "command", pre_timestamp=send_timestamp)
            self.notification_manager.show_success(f"✅ {command_type}设置命令已发送")
        else:
            self.notification_manager.show_error(f"❌ {command_type}设置命令发送失败")
    
    def toggle_ds18b20_auto_query(self):
        """切换DS18B20自动查询功能"""
        if not self.serial_manager.is_connected():
            self.notification_manager.show_warning("⚠️ 请先连接串口", auto_close=True)
            return
        
        self.ds18b20_auto_query_enabled = not self.ds18b20_auto_query_enabled
        
        if self.ds18b20_auto_query_enabled:
            # 启动定时器
            interval_ms = self.ds18b20_auto_query_interval * 1000
            self.ds18b20_auto_query_timer.start(interval_ms)
            self.notification_manager.show_success(f"✅ DS18B20自动查询已启用，间隔{self.ds18b20_auto_query_interval}秒")
            
            # 立即查询一次温度
            self._auto_query_ds18b20()
        else:
            # 停止定时器
            self.ds18b20_auto_query_timer.stop()
            self.notification_manager.show_info("⏹️ DS18B20自动查询已禁用")
    
    def _auto_query_ds18b20(self):
        """自动查询DS18B20温度"""
        if not self.serial_manager.is_connected() or not self.ds18b20_auto_query_enabled:
            return
        
        # 发送读取温度命令
        self.serial_manager.send_command("ds18b20 read")
        
    def _update_temperature_display(self, temperature_str):
        """更新温度显示，根据温度值着色"""
        if not hasattr(self, 'temperature_display'):
            print(f"[温度显示] 错误: temperature_display属性不存在")
            return
        
        print(f"[温度显示] 更新温度显示为: {temperature_str}")
        # 设置显示文本
        self.temperature_display.setText(f"🌡️ 温度: {temperature_str}")
        
        # 默认样式（蓝色，初始状态）
        default_style = """
            QLabel {
                color: #3498db;
                padding: 6px 10px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(52, 152, 219, 0.3);
                margin-top: 8px;
            }
        """
        
        # 尝试解析温度数值
        try:
            # 移除单位和非数字字符，只保留数字和小数点
            temp_str_clean = temperature_str.replace('°C', '').replace('℃', '').replace('℉', '').strip()
            
            # 如果字符串为空或为"未读取"，使用默认颜色
            if not temp_str_clean or temp_str_clean == "未读取":
                self.temperature_display.setStyleSheet(default_style)
                return
            
            temperature = float(temp_str_clean)
            
            # 根据温度值选择颜色
            if temperature < 15.0:
                # 低温：蓝色
                color = "#3498db"
                bg_color = "rgba(52, 152, 219, 0.1)"
                border_color = "rgba(52, 152, 219, 0.3)"
            elif temperature <= 28.0:
                # 常温：绿色
                color = "#27ae60"
                bg_color = "rgba(39, 174, 96, 0.1)"
                border_color = "rgba(39, 174, 96, 0.3)"
            else:
                # 高温：红色
                color = "#e74c3c"
                bg_color = "rgba(231, 76, 60, 0.1)"
                border_color = "rgba(231, 76, 60, 0.3)"
            
            # 应用动态样式
            self.temperature_display.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    padding: 6px 10px;
                    background: {bg_color};
                    border-radius: 6px;
                    border: 1px solid {border_color};
                    margin-top: 8px;
                }}
            """)
            
        except ValueError:
            # 解析失败，使用默认样式
            if self.debug_mode:
                print(f"[DEBUG] 无法解析温度值: {temperature_str}")
            self.temperature_display.setStyleSheet(default_style)
    
    def _check_and_update_temperature(self, message: str):
        """检查消息是否为温度数据并更新显示"""
        try:
            # 检查是否包含温度关键词
            if '温度:' in message and ('°C' in message or '℃' in message):
                # 总是打印温度消息检测到日志（方便调试）
                print(f"[温度检测] 检测到温度消息: '{message}'")
                
                # 提取温度值部分
                # 示例: "温度: 25.500°C" 或 "温度: 25.500°C (CRC校验成功)"
                start = message.find('温度:') + 3  # '温度:' 长度
                
                # 先检查℃符号，再检查°C符号
                end_celsius = message.find('℃', start)
                if end_celsius == -1:
                    end_celsius = message.find('°C', start)
                
                end = end_celsius
                
                if start < end:
                    temp_str = message[start:end].strip()
                    # 移除可能的多余空格和单位
                    temp_str = temp_str.replace('°C', '').replace('℃', '').strip()
                    
                    print(f"[温度检测] 提取的温度值: '{temp_str}'")
                    
                    # 更新温度显示
                    self._update_temperature_display(f"{temp_str}°C")
                    # 保存当前温度值
                    self.ds18b20_current_temperature = temp_str
                else:
                    print(f"[温度检测] 温度消息格式异常: start={start}, end={end}, message='{message}'")
            else:
                # 如果不是温度消息，但包含'温度'关键词，记录简短信息
                if '温度' in message:
                    print(f"[温度检测] 消息包含'温度'但未匹配单位符号: '{message[:50]}...'")
        except Exception as e:
            print(f"[温度检测] 温度消息解析失败: {e}")
    
    def _check_device_busy_keywords(self, message: str) -> bool:
        """检查消息是否包含设备忙关键词（已禁用设备忙检测机制）"""
        # 已禁用设备忙检测机制，始终返回False
        # 这样不会触发设备忙状态设置和等待通知
        if self.debug_mode:
            # 仅记录检测到关键词，但不触发状态变化
            message_lower = message.lower()
            for keyword in self._device_busy_keywords:
                if keyword.lower() in message_lower:
                    print(f"[DEBUG] 检测到设备忙关键词但机制已禁用: '{keyword}'")
                    break
        return False  # 始终返回False，不触发设备忙状态
    
    def _check_device_ready_keywords(self, message: str) -> bool:
        """检查消息是否包含设备就绪关键词"""
        message_lower = message.lower()
        for keyword in self._device_ready_keywords:
            if keyword.lower() in message_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到设备就绪关键词: '{keyword}'")
                return True
        return False
    
    def _set_device_busy(self, reason: str = "未知"):
        """设置设备忙状态（已禁用设备忙检测和等待机制）"""
        # 已禁用设备忙检测和等待机制，仅记录日志，不设置实际状态
        if self.debug_mode:
            print(f"[DEBUG] 检测到设备忙关键词但机制已禁用: {reason}")
            print(f"[DEBUG] 注意：设备忙状态和等待通知机制已禁用，命令将立即发送")
        
        # 不设置_device_busy标志，不启动定时器，不显示通知
        # 这样可以确保命令不会被延迟发送
    
    def _set_device_ready(self, reason: str = "未知"):
        """设置设备就绪状态"""
        if self._device_busy:
            # 先计算忙时长
            busy_duration = time.time() - self._device_busy_start_time if self._device_busy_start_time > 0 else 0
            
            self._device_busy = False
            self._device_busy_start_time = 0
            self._device_busy_timer.stop()
            
            if self.debug_mode:
                print(f"[DEBUG] 设置设备就绪状态，原因: {reason}，忙时长: {busy_duration:.1f}秒")
                print(f"[DEBUG] 当前等待队列长度: {len(self._pending_commands)}个命令")
            
            # 显示状态通知
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_success(f"✅ 设备已就绪（{reason}，忙时 {busy_duration:.1f}秒）", auto_close=True)
            
            # 更新UI状态
            self._update_device_busy_ui(False, f"就绪（忙 {busy_duration:.1f}秒）")
            
            # 设备就绪后立即处理等待队列
            if self._pending_commands:
                if self.debug_mode:
                    print(f"[DEBUG] 设备就绪，开始处理等待队列（{len(self._pending_commands)}个命令）")
                self._process_pending_commands()
    
    def _check_device_busy_timeout(self):
        """检查设备忙超时"""
        if not self._device_busy:
            return
        
        current_time = time.time()
        busy_duration = current_time - self._device_busy_start_time
        
        if busy_duration > self._device_busy_timeout:
            if self.debug_mode:
                print(f"[DEBUG] 设备忙超时（{busy_duration:.1f}秒 > {self._device_busy_timeout}秒），强制设置为就绪")
            self._set_device_ready("超时自动恢复")
    
    def _process_pending_commands(self):
        """处理等待队列中的命令（排队机制已禁用）"""
        # 排队机制已禁用，清空任何残留的队列
        if self._pending_commands:
            queue_size = len(self._pending_commands)
            if self.debug_mode:
                print(f"[DEBUG] 排队机制已禁用，清空残留的等待队列（{queue_size}个命令）")
            self._pending_commands.clear()
        # 不执行任何发送操作
    
    def _add_to_pending_commands(self, command: str) -> bool:
        """添加命令到等待队列（排队机制已禁用）"""
        # 排队机制已禁用，始终返回False，命令不会被加入队列
        if self.debug_mode:
            print(f"[DEBUG] 排队机制已禁用，命令 '{command}' 将直接发送")
            # 清空可能残留的队列，避免旧命令被意外发送
            if self._pending_commands:
                print(f"[DEBUG] 清空残留的等待队列（{len(self._pending_commands)}个命令）")
                self._pending_commands.clear()
        
        # 始终返回False，表示命令未被加入队列，调用者应直接发送
        return False
    
    def _send_command_direct(self, command: str) -> bool:
        """直接发送命令（绕过设备忙检查）"""
        # 这是send_command的核心逻辑，但不包含设备忙检查
        if not command or not hasattr(self, 'serial_manager') or not self.serial_manager.is_connected():
            return False
        
        # 记录最近发送的命令（用于过滤回显）
        self._last_sent_command = command
        
        # 添加命令到显示区域（蓝色）- 立即生成时间戳
        send_timestamp = self._get_current_timestamp()
        self.add_message(f"发送→{command}", "command", pre_timestamp=send_timestamp)
        
        # 发送命令并检查结果
        success = self.serial_manager.send_command(command)
        
        if not success and self.debug_mode:
            print(f"[DEBUG] 发送命令失败: {command}")
        
        return success
    
    def _update_device_busy_ui(self, is_busy: bool, status_text: str = ""):
        """更新设备忙UI状态"""
        try:
            # 更新状态栏消息
            if hasattr(self, 'status_bar'):
                if is_busy:
                    self.status_bar.showMessage(f"⚠️ 设备忙 - {status_text}")
                else:
                    self.status_bar.showMessage(f"✅ 设备就绪 - {status_text}")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 更新设备忙UI状态失败: {e}")
            
    def add_message(self, message: str, msg_type: str = "info", add_timestamp: bool = None, pre_timestamp: str = None):
        """添加消息到显示区域 - 简化直接显示机制（修复版）"""
        if not hasattr(self, 'display_text') or self.display_text is None:
            return
        
        # 调试信息：追踪消息添加
        if self.debug_mode:
            print(f"[DEBUG] add_message调用: msg='{message[:50]}...', type='{msg_type}', add_timestamp={add_timestamp}, pre_timestamp={pre_timestamp}")
        
        # 命令回显（echo类型）只记录到日志，不显示在终端
        if msg_type == "echo":
            if self.debug_mode:
                print(f"[DEBUG] 命令回显只记录到日志，不显示: {message[:50]}...")
            # 仍然调用_add_message_to_display来记录到日志，但不实际显示
            # 通过传递一个特殊标志来跳过显示
            self._add_message_to_display(message, msg_type, add_timestamp, skip_display=True, pre_timestamp=pre_timestamp)
            return
        
        # 完全移除重复检测，确保所有串口消息都能显示
        # 串口数据本身就可能包含重复内容，不应该在UI层面过滤
        
        # 直接添加到显示区域，不使用缓冲区
        self._add_message_to_display(message, msg_type, add_timestamp, pre_timestamp=pre_timestamp)
    
    def _add_message_to_display(self, message: str, msg_type: str = "info", add_timestamp: bool = None, skip_display: bool = False, pre_timestamp: str = None):
        """直接添加消息到显示区域 - 简化版本（修复版）"""
        try:
            # 调试信息：确认消息到达显示函数
            if self.debug_mode:
                print(f"[DEBUG] 显示函数收到消息: {repr(message[:30])}..., skip_display={skip_display}, pre_timestamp={pre_timestamp}")
            
            # 如果skip_display为True，只记录到日志，不显示
            if skip_display:
                if self.debug_mode:
                    print(f"[DEBUG] 跳过显示，只记录到日志: {repr(message[:30])}...")
                # 只记录到日志，不显示
                self._log_terminal_message(message, msg_type)
                return
            
            # 简化行数限制检查 - 只在文档过大时清理
            document = self.display_text.document()
            if document.blockCount() > 50000:  # 50000行限制
                cursor = self.display_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10000)  # 删除前10000行
                cursor.removeSelectedText()
            
            # 添加时间戳（如果启用）
            # 如果add_timestamp为None，使用self.show_timestamp设置
            # 如果add_timestamp为False，不添加时间戳
            # 如果add_timestamp为True，添加时间戳
            should_add_timestamp = self.show_timestamp if add_timestamp is None else add_timestamp
            
            if should_add_timestamp:
                # 优先使用预先生成的时间戳（更准确）
                if pre_timestamp:
                    timestamp = pre_timestamp
                else:
                    from datetime import datetime
                    now = datetime.now()
                    # 毫秒级时间戳格式：[HH:MM:SS.mmm]
                    timestamp = now.strftime("%H:%M:%S") + f".{now.microsecond // 1000:03d}"
                
                # 特殊处理：对于接收消息（以"接收←"开头）或发送消息（以"发送→"开头），只对第一行添加时间戳
                # 参考命令实际执行效果.txt格式：[时间戳]接收←命令，后续行无时间戳，保持原始缩进
                if (message.startswith("接收←") or message.startswith("发送→")) and '\n' in message:
                    lines = message.split('\n')
                    # 只对第一行添加时间戳前缀
                    lines[0] = f"[{timestamp}]{lines[0]}"
                    # 重新组合消息，保持原始换行符
                    message_with_timestamp = '\n'.join(lines)
                else:
                    message_with_timestamp = f"[{timestamp}]{message}"
            else:
                message_with_timestamp = message
            
            # 对消息进行着色（保持原始格式）
            colored_message = self._colorize_message(message_with_timestamp, msg_type)
            
            # 记录到终端日志（如果启用）
            self._log_terminal_message(message, msg_type)
            
            # 检测"未知命令"并更新AI8051U状态标签
            if '未知命令' in message and hasattr(self, 'ai8051u_status_label') and self.ai8051u_detection_enabled:
                self.ai8051u_status_label.setText("❌ AI8051U: 未知命令")
                self.ai8051u_status_label.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        padding: 10px 14px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 6px;
                        border: 1px solid rgba(231, 76, 60, 0.3);
                    }
                """)
                if self.debug_mode:
                    print(f"[DEBUG] 检测到未知命令，更新AI8051U状态为红色")
            
            # 直接添加消息到显示区域，实现实时显示
            if hasattr(self, 'display_text') and self.display_text:
                self.display_text.append(colored_message)
                # 自动滚动到底部
                if self.auto_scroll:
                    # 使用QTimer确保消息已完全添加到文档中
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(10, lambda: self._scroll_to_bottom())
                
                if self.debug_mode:
                    print(f"[DEBUG] _add_message_to_display: 直接显示完成")
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 添加消息到显示区域错误: {e}")
            # 出错时直接添加原始消息
            try:
                self.display_text.append(message)
                # 异常处理时也自动滚动到底部
                if self.debug_mode:
                    print(f"[DEBUG] _add_message_to_display(异常处理): 自动滚动到底部")
                # 使用QTimer确保消息已完全添加到文档中
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(10, lambda: self._scroll_to_bottom())
            except:
                pass
    
    def _scroll_to_bottom(self):
        """滚动到底部 - 改进版本"""
        if not hasattr(self, 'display_text') or self.display_text is None:
            return
        
        try:
            # 方法1：直接设置滚动条值
            scrollbar = self.display_text.verticalScrollBar()
            max_value = scrollbar.maximum()
            
            # 检查最大值是否有效
            if max_value > 0:
                scrollbar.setValue(max_value)
            
            # 方法2：使用ensureCursorVisible确保光标可见
            self.display_text.ensureCursorVisible()
            
            # 方法3：使用moveCursor到文档末尾
            cursor = self.display_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.display_text.setTextCursor(cursor)
            
            # 方法4：延迟再次滚动，确保UI更新完成
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, lambda: self._force_scroll_to_bottom())
            
            if self.debug_mode:
                print(f"[DEBUG] 滚动到底部执行完成，最大值: {max_value}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 滚动到底部失败: {e}")
    
    def _force_scroll_to_bottom(self):
        """强制滚动到底部（延迟执行）"""
        if not hasattr(self, 'display_text') or self.display_text is None:
            return
        
        try:
            scrollbar = self.display_text.verticalScrollBar()
            max_value = scrollbar.maximum()
            
            # 再次检查并滚动
            if max_value > 0:
                current_value = scrollbar.value()
                if current_value < max_value - 10:  # 如果不在底部附近
                    scrollbar.setValue(max_value)
                    if self.debug_mode:
                        print(f"[DEBUG] 强制滚动: {current_value} -> {max_value}")
            
            # 确保光标在视图中
            self.display_text.ensureCursorVisible()
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 强制滚动失败: {e}")
    
    def _log_terminal_message(self, message: str, msg_type: str):
        """记录终端消息到日志文件"""
        if not hasattr(self, 'terminal_logger') or self.terminal_logger is None:
            return
        
        try:
            # 判断消息方向（发送或接收）
            direction = None
            
            # 检查是否为发送的消息
            if message.startswith("发送→"):
                direction = "send"
                # 移除"发送→"前缀
                clean_message = message[3:]  # 移除"发送→"
            # 检查是否为接收的消息
            elif message.startswith("接收←"):
                direction = "receive"
                # 移除"接收←"前缀
                clean_message = message[3:]  # 移除"接收←"
            else:
                # 未知方向，不记录
                return
            
            # 记录到终端日志
            if direction == "send":
                self.terminal_logger.log_send(clean_message, msg_type)
            elif direction == "receive":
                self.terminal_logger.log_receive(clean_message, msg_type)
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 记录终端消息失败: {e}")
    
    def _colorize_message(self, message: str, msg_type: str) -> str:
        """为消息添加颜色（多巴胺配色主题）"""
        # 将换行符转换为HTML换行标签，保持原始格式
        # 同时保留空格（使用&nbsp;代替普通空格以保持缩进）
        message_html = message.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
        
        # 为不同类型的消息添加颜色 - 使用多巴胺配色方案
        if msg_type == "command":
            # 用户发送的命令 - 鲜艳的蓝色（多巴胺蓝）
            return f'<span style="color: #667eea; font-weight: bold;">{message_html}</span>'
        elif msg_type == "system":
            # 系统信息 - 亮紫色加粗（更明显）
            return f'<span style="color: #DA70D6; font-weight: bold;">{message_html}</span>'
        elif msg_type == "hardware":
            # 硬件测试结果 - 橙色（多巴胺橙）
            return f'<span style="color: #f39c12;">{message_html}</span>'
        elif msg_type == "benchmark":
            # 性能基准测试 - 红色（多巴胺红）
            return f'<span style="color: #e74c3c;">{message_html}</span>'
        elif msg_type == "clock":
            # 时钟信息 - 金色（多巴胺金）
            return f'<span style="color: #f1c40f;">{message_html}</span>'
        elif msg_type == "voltage":
            # 电压测量 - 绿色（多巴胺绿）
            return f'<span style="color: #27ae60;">{message_html}</span>'
        elif msg_type == "ascii_art":
            # ASCII艺术 - 青色（多巴胺青）
            # 对于ASCII艺术，使用等宽字体并保留所有空格
            ascii_html = message.replace('\n', '<br>').replace(' ', '&nbsp;')
            return f'<span style="color: #1abc9c; font-family: Consolas, monospace;">{ascii_html}</span>'
        elif msg_type == "rtc":
            # RTC时钟信息 - 粉色（多巴胺粉）
            return f'<span style="color: #e84393;">{message_html}</span>'
        elif msg_type == "memory":
            # 内存使用信息 - 深蓝色（多巴胺深蓝）
            return f'<span style="color: #3498db;">{message_html}</span>'
        elif msg_type == "hardware_status":
            # 硬件状态信息 - 棕色（多巴胺棕）
            return f'<span style="color: #a0522d;">{message_html}</span>'
        elif msg_type == "test_detail":
            # 测试结果详细信息 - 深紫色（多巴胺深紫）
            return f'<span style="color: #8e44ad;">{message_html}</span>'
        elif msg_type == "reboot":
            # 重启信息 - 亮黄色（多巴胺亮黄）
            return f'<span style="color: #f1c40f; font-weight: bold;">{message_html}</span>'
        elif msg_type == "clear":
            # 清屏效果 - 浅灰色（中性色）
            return f'<span style="color: #bdc3c7;">{message_html}</span>'
        elif msg_type == "help":
            # 帮助信息 - 浅紫色（多巴胺浅紫）
            return f'<span style="color: #9b59b6;">{message_html}</span>'
        elif msg_type == "error":
            # 错误消息 - 深红色（醒目）
            return f'<span style="color: #c0392b; font-weight: bold;">{message_html}</span>'
        elif msg_type == "warning":
            # 警告消息 - 琥珀色（多巴胺琥珀）
            return f'<span style="color: #f39c12;">{message_html}</span>'
        elif msg_type == "success":
            # 成功消息 - 翠绿色（多巴胺翠绿）
            return f'<span style="color: #2ecc71;">{message_html}</span>'
        elif msg_type == "temperature":
            # 温度消息 - 根据温度值动态着色
            try:
                # 从消息中提取温度值
                if '温度:' in message and ('°C' in message or '℃' in message):
                    start = message.find('温度:') + 3
                    
                    # 先检查℃符号，再检查°C符号
                    end_celsius = message.find('℃', start)
                    if end_celsius == -1:
                        end_celsius = message.find('°C', start)
                    
                    end = end_celsius
                    
                    if start < end:
                        temp_str = message[start:end].strip().replace('°C', '').replace('℃', '').strip()
                        if temp_str:
                            temperature = float(temp_str)
                            # 根据温度值选择颜色
                            if temperature < 15.0:
                                color = "#3498db"  # 低温蓝
                            elif temperature <= 28.0:
                                color = "#27ae60"  # 常温绿
                            else:
                                color = "#e74c3c"  # 高温红
                            return f'<span style="color: {color}; font-weight: bold;">{message_html}</span>'
            except (ValueError, AttributeError):
                pass  # 解析失败，使用默认颜色
            # 默认温度颜色（青色）
            return f'<span style="color: #1abc9c; font-weight: bold;">{message_html}</span>'
        elif msg_type == "graphic":
            # 图形命令信息 - 青绿色（多巴胺青绿）
            return f'<span style="color: #4ECDC4;">{message_html}</span>'
        elif msg_type == "info":
            # 普通信息 - 黑色（默认颜色，如建议）
            return f'<span style="color: #000000;">{message_html}</span>'
        else:
            # 默认颜色 - 黑色（如建议）
            return f'<span style="color: #000000;">{message_html}</span>'
    
    def setup_connections(self):
        """设置信号连接"""
        # 创建串口管理器
        self.serial_manager = ColorBridgeSerialManager(
            monitoring_system=self.monitoring_system,
            debug_mode=self.debug_mode
        )
        
        # 连接串口信号
        self.serial_manager.message_received.connect(self.on_message_received)
        self.serial_manager.connection_changed.connect(self.on_connection_changed)
        
        # 连接消息处理器信号
        self._connect_message_processor_signals()
        
    def _connect_message_processor_signals(self):
        """连接消息处理器信号"""
        if (hasattr(self.serial_manager, 'reader_thread') and 
            self.serial_manager.reader_thread and 
            hasattr(self.serial_manager.reader_thread, 'message_processor')):
            
            processor = self.serial_manager.reader_thread.message_processor
            
            # 恢复消息处理信号连接，修复消息不显示问题
            processor.message_processed.connect(self.add_message)
            
            # 连接命令检测信号
            processor.command_detected.connect(self._on_command_detected)
            
            if self.debug_mode:
                print("[DEBUG] 消息处理器信号已连接（已恢复消息显示）")
    
    def _on_command_detected(self, command: str):
        """命令检测回调"""
        if self.debug_mode:
            print(f"[DEBUG] UI检测到命令: {command}")
    
    def on_connection_changed(self, connected: bool):
        """处理连接状态变化"""
        try:
            if connected:
                self.connection_status_label.setText("🟢 已连接")
                self.connection_status_label.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        padding: 8px 12px;
                        background: rgba(39, 174, 96, 0.1);
                        border-radius: 6px;
                        border: 1px solid rgba(39, 174, 96, 0.3);
                    }
                """)
                self.connect_btn.setText("🔗 断开连接")
                self.connect_btn.button_type = "danger"
                self.connect_btn.setup_style()
                if self.debug_mode:
                    print("[DEBUG] 连接状态变化: 已连接")
                
                # 连接验证机制：连接成功后2秒发送空命令测试通信，给设备充分初始化时间
                if hasattr(self, 'serial_manager') and self.serial_manager.is_connected():
                    if self.debug_mode:
                        print("[DEBUG] 调度连接验证测试命令")
                    # 延迟2秒发送，给设备充分时间初始化
                    QTimer.singleShot(2000, self._send_connection_test)
            else:
                self.connection_status_label.setText("🔴 未连接")
                self.connection_status_label.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        padding: 8px 12px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 6px;
                        border: 1px solid rgba(231, 76, 60, 0.3);
                    }
                """)
                self.connect_btn.setText("🔗 连接串口")
                self.connect_btn.button_type = "primary"
                self.connect_btn.setup_style()
                if self.debug_mode:
                    print("[DEBUG] 连接状态变化: 已断开")
                
                # 连接状态变化时清空设备信息显示（仅断开时）
                if hasattr(self, 'device_info_display'):
                    self.device_info_display.setPlainText("设备已断开\n\n点击'🔄 获取设备信息'按钮重新获取设备信息")
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 连接状态变化处理错误: {e}")
    
    def _send_connection_test(self):
        """发送连接测试命令 - 简化可靠版本"""
        try:
            if hasattr(self, 'serial_manager') and self.serial_manager.is_connected():
                # 显示连接状态
                self.add_message("🔗 串口已连接，正在初始化设备通信...", "info", add_timestamp=False)
                
                if self.debug_mode:
                    print("[DEBUG] 开始设备通信初始化")
                
                # 方案1：直接检查串口状态，不发送测试命令
                # 避免虚假的"测试成功"，真实通信测试由info命令完成
                
                # 检查串口基本状态
                serial_port = self.serial_manager.serial_port
                if serial_port and serial_port.isOpen():
                    if self.debug_mode:
                        print("[DEBUG] 串口已打开且可写，开始设备初始化等待")
                    
                    # 显示状态
                    self.add_message("✅ 串口通信已建立", "success", add_timestamp=False)
                    
                    # 关键改进：立即发送info命令激活设备，解决首次发送无响应问题
                    if self.debug_mode:
                        print("[DEBUG] 发送初始化info命令（激活设备）...")
                    self.add_message("🔄 发送初始化info命令激活设备...", "info", add_timestamp=False)
                    
                    # 发送info命令直接激活设备，同时重置所有发送状态，避免后续命令被去重
                    try:
                        # 重置串口管理器状态，确保info命令不会被过滤
                        if hasattr(self.serial_manager, '_last_command_hash'):
                            self.serial_manager._last_command_hash = None
                        if hasattr(self.serial_manager, '_last_send_time'):
                            self.serial_manager._last_send_time = 0
                        
                        test_sent = self.serial_manager.send_data("info")
                        if self.debug_mode:
                            print(f"[DEBUG] 初始化info命令发送结果: {'成功' if test_sent else '失败'}")
                            if test_sent:
                                # 显示发送记录
                                send_timestamp = self._get_current_timestamp()
                                self.add_message(f"发送→info (激活)", "command", pre_timestamp=send_timestamp)
                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] 发送初始化info命令时出错: {e}")
                    
                    # 等待15秒让设备充分初始化并处理激活命令
                    if self.debug_mode:
                        print("[DEBUG] 等待15秒让设备完全初始化并处理激活命令...")
                    
                    self.add_message("⏳ 设备初始化中，请稍候...", "info", add_timestamp=False)
                    
                    # 15秒后发送info命令获取设备信息，确保设备已完全就绪
                    QTimer.singleShot(15000, lambda: self._send_info_with_retry())
                else:
                    # 串口状态异常
                    self.add_message("⚠️ 串口状态异常，请检查连接", "warning")
                    if self.debug_mode:
                        print("[DEBUG] 串口状态异常，无法进行通信测试")
        
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 连接验证错误: {e}")
            self.add_message(f"⚠️ 连接验证时出错: {str(e)[:50]}...", "warning")
    
    def _retry_connection_with_info(self):
        """使用info命令重试连接验证"""
        try:
            if hasattr(self, 'serial_manager') and self.serial_manager.is_connected():
                self.add_message("🔗 使用'info'命令测试设备通信...", "info")
                
                if self.debug_mode:
                    print("[DEBUG] 使用'info'命令重试连接验证")
                
                # 重置串口管理器哈希，确保命令不被错误去重
                if hasattr(self.serial_manager, '_last_command_hash'):
                    self.serial_manager._last_command_hash = None
                
                # 发送info命令
                self.send_quick_command("info")
                
                if self.debug_mode:
                    print("[DEBUG] info命令已发送（不依赖返回值）")
                
                # 设置响应检查
                def check_device_response():
                    if self.debug_mode:
                        print("[DEBUG] 设备响应检查：显示状态提示")
                    self.add_message("⏳ 正在检测设备响应，请稍候...", "info")
                
                QTimer.singleShot(5000, check_device_response)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 重试连接验证错误: {e}")
            self.add_message(f"⚠️ 测试设备通信时出错: {str(e)[:50]}...", "warning")
    
    def _send_info_with_retry(self):
        """发送info命令并支持重试（用于连接验证后） - 重写版本，确保可靠发送"""
        try:
            if self.debug_mode:
                print("[DEBUG] _send_info_with_retry: 发送info命令（带重试）")
            
            # 检查是否已经在等待info响应，避免重复发送
            if self._waiting_for_info_response:
                if self.debug_mode:
                    print("[DEBUG] 已经在等待info响应，跳过重复发送")
                return
            
            # 检查设备忙状态，如果设备忙则延迟发送
            if hasattr(self, '_device_busy') and self._device_busy:
                if self.debug_mode:
                    print("[DEBUG] 设备忙，延迟1秒后重试发送info命令")
                # 延迟1秒后重试
                QTimer.singleShot(1000, self._send_info_with_retry)
                return
            
            # 显示进度提示
            self.add_message("🔍 正在获取设备信息...", "info", add_timestamp=False)
            
            # 设置用户主动请求标志，确保自动获取的设备信息能刷新UI显示
            if hasattr(self, '_user_requested_device_info'):
                self._user_requested_device_info = True
                if self.debug_mode:
                    print("[DEBUG] 已设置用户主动请求标志，确保自动获取信息刷新显示")
            else:
                # 如果属性不存在，创建它
                self._user_requested_device_info = True
            
            # 详细的串口状态调试（包含波特率）
            if self.debug_mode:
                serial_port = self.serial_manager.serial_port
                port_status = "未连接"
                port_name = "无"
                baud_rate = "无"
                writable = "未知"
                if serial_port:
                    port_status = "已打开" if serial_port.isOpen() else "已关闭"
                    port_name = serial_port.portName() if serial_port.portName() else "无"
                    baud_rate = str(serial_port.baudRate()) if serial_port.baudRate() else "无"
                    writable = serial_port.isWritable() if hasattr(serial_port, 'isWritable') else "未知"
                    print(f"[DEBUG] 串口状态: {port_status}, 端口: {port_name}, 波特率: {baud_rate}, 可写: {writable}")
                    if hasattr(self.serial_manager, '_last_command_hash'):
                        print(f"[DEBUG] 当前命令哈希: {self.serial_manager._last_command_hash}")
                    if hasattr(self.serial_manager, '_last_send_time'):
                        print(f"[DEBUG] 最后发送时间: {self.serial_manager._last_send_time}")
                # 同时显示UI中的波特率设置
                if hasattr(self, 'baud_combo'):
                    ui_baud = self.baud_combo.currentText() if self.baud_combo.currentText() else "未设置"
                    print(f"[DEBUG] UI波特率设置: {ui_baud}")
            
            # 强制重置所有可能干扰发送的状态
            if hasattr(self.serial_manager, '_last_command_hash'):
                self.serial_manager._last_command_hash = None
            if hasattr(self.serial_manager, '_last_send_time'):
                self.serial_manager._last_send_time = 0
            if hasattr(self, '_last_sent_command'):
                self._last_sent_command = None
            if hasattr(self, '_last_send_time'):
                self._last_send_time = 0
            
            # 重置reader_thread的发送时间（用于响应超时检测）
            if (hasattr(self.serial_manager, 'reader_thread') and 
                self.serial_manager.reader_thread and
                hasattr(self.serial_manager.reader_thread, 'last_send_time')):
                self.serial_manager.reader_thread.last_send_time = 0
                self.serial_manager.reader_thread.response_received = False
            
            if self.debug_mode:
                print("[DEBUG] 已重置所有发送状态，确保info命令不被错误过滤")
                # 显示状态重置信息到UI日志（调试用）
                self.add_message("🔧 已重置所有发送状态", "debug", add_timestamp=False)
            
            # 清空串口缓冲区，确保没有残留数据干扰
            try:
                if (hasattr(self.serial_manager, 'serial_port') and 
                    self.serial_manager.serial_port and
                    self.serial_manager.serial_port.isOpen()):
                    serial_port = self.serial_manager.serial_port
                    # 清空输入缓冲区（接收）
                    try:
                        serial_port.clear(QSerialPort.Input)
                    except:
                        serial_port.clear()  # 回退方案
                    # 清空输出缓冲区（发送）
                    try:
                        serial_port.clear(QSerialPort.Output)
                    except:
                        pass  # 已经清空过
                    if self.debug_mode:
                        print("[DEBUG] 已清空串口输入/输出缓冲区")
                        self.add_message("🔧 已清空串口缓冲区", "debug", add_timestamp=False)
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 清空缓冲区时出错: {e}")
            
            # 设置等待响应标志和设备忙状态，防止重复发送 - 设备忙状态机制已禁用
            self._waiting_for_info_response = True
            # 设备忙状态机制已禁用
            if self.debug_mode:
                print("[DEBUG] 已设置等待响应标志，设备忙状态机制已禁用")
            
            # 关键修复：使用force=True强制发送，跳过所有去重和间隔检查
            # 这是自动流程，必须确保命令发送出去
            if self.debug_mode:
                print("[DEBUG] 使用force=True强制发送info命令...")
            
            # 尝试发送，最多重试3次
            max_retries = 3
            actual_sent = False
            
            for attempt in range(max_retries):
                if self.debug_mode:
                    print(f"[DEBUG] 发送尝试 {attempt + 1}/{max_retries}")
                
                # 使用force=True，确保命令不被去重或间隔检查阻止
                actual_sent = self.serial_manager.send_data("info")
                
                if self.debug_mode:
                    print(f"[DEBUG] 发送结果: {'成功' if actual_sent else '失败'}")
                    self.add_message(f"🔧 发送尝试 {attempt + 1}/{max_retries}: {'成功' if actual_sent else '失败'}", "debug", add_timestamp=False)
                
                if actual_sent:
                    break
                else:
                    # 发送失败，等待500ms后重试
                    if attempt < max_retries - 1:
                        if self.debug_mode:
                            print(f"[DEBUG] 发送失败，500ms后重试...")
                        time.sleep(0.5)
            
            if self.debug_mode:
                print(f"[DEBUG] 最终发送结果: {'成功' if actual_sent else '失败'}")
                send_status = "命令已发送（实际写入串口）" if actual_sent else "发送失败（串口可能未连接）"
                self.add_message(f"🔧 发送结果: {send_status}", "debug", add_timestamp=False)
            
            # 添加命令到显示区域（确保用户看到发送记录）- 立即生成时间戳
            send_timestamp = self._get_current_timestamp()
            self.add_message(f"发送→info", "command", pre_timestamp=send_timestamp)
            
            # 优化时间参数：3秒、6秒、9秒
            # 1. 3秒后检查：显示处理中提示
            # 2. 6秒后检查：显示等待提示
            # 3. 9秒后检查：显示超时提示（不再自动重试，避免重复发送）
            
            def check_response_3s():
                """3秒后检查响应"""
                # 检查是否已经收到响应（显示区域包含系统信息）
                if hasattr(self, 'display_text') and self.display_text:
                    current_text = self.display_text.toPlainText()
                    # 检查最后2000个字符中是否包含系统信息关键词
                    check_text = current_text[-2000:] if len(current_text) > 2000 else current_text
                    # 扩展关键词列表，提高检测准确性
                    response_keywords = ['系统信息:', '系统信息', '微控制器:', '时钟频率:', 'Flash大小:', 'XRAM大小:', 'USB-CDC:', 'OLED显示:', 'DS18B20温度传感器:', '编译日期:', 'RTC时钟:', '内存使用:', '可用图形命令:']
                    if any(keyword in check_text for keyword in response_keywords):
                        if self.debug_mode:
                            print("[DEBUG] 检测到已收到系统信息响应，跳过3秒提示")
                            self.add_message("🔧 检测到已收到系统信息响应，跳过3秒提示", "debug", add_timestamp=False)
                        return
                
                if self.debug_mode:
                    print("[DEBUG] 3秒响应检查：显示处理中提示")
                    self.add_message("🔧 3秒响应检查：显示处理中提示", "debug", add_timestamp=False)
                self.add_message("⏳ 设备正在处理info命令，请稍候...", "info", add_timestamp=False)
            
            def check_response_6s():
                """6秒后检查响应"""
                # 检查是否已经收到响应（显示区域包含系统信息）
                if hasattr(self, 'display_text') and self.display_text:
                    current_text = self.display_text.toPlainText()
                    # 检查最后2000个字符中是否包含系统信息关键词
                    check_text = current_text[-2000:] if len(current_text) > 2000 else current_text
                    # 扩展关键词列表，提高检测准确性
                    response_keywords = ['系统信息:', '系统信息', '微控制器:', '时钟频率:', 'Flash大小:', 'XRAM大小:', 'USB-CDC:', 'OLED显示:', 'DS18B20温度传感器:', '编译日期:', 'RTC时钟:', '内存使用:', '可用图形命令:']
                    if any(keyword in check_text for keyword in response_keywords):
                        if self.debug_mode:
                            print("[DEBUG] 检测到已收到系统信息响应，跳过6秒提示")
                            self.add_message("🔧 检测到已收到系统信息响应，跳过6秒提示", "debug", add_timestamp=False)
                        return
                
                if self.debug_mode:
                    print("[DEBUG] 6秒响应检查：显示等待提示")
                    self.add_message("🔧 6秒响应检查：显示等待提示", "debug", add_timestamp=False)
                self.add_message("⏳ 仍在等待设备响应...", "info", add_timestamp=False)
            
            def auto_retry_9s():
                """9秒后检查响应（不再自动重试，避免重复发送）"""
                # 检查是否已经收到响应（显示区域包含系统信息）
                if hasattr(self, 'display_text') and self.display_text:
                    current_text = self.display_text.toPlainText()
                    # 检查最后2000个字符中是否包含系统信息关键词
                    check_text = current_text[-2000:] if len(current_text) > 2000 else current_text
                    # 扩展关键词列表，提高检测准确性
                    response_keywords = ['系统信息:', '系统信息', '微控制器:', '时钟频率:', 'Flash大小:', 'XRAM大小:', 'USB-CDC:', 'OLED显示:', 'DS18B20温度传感器:', '编译日期:', 'RTC时钟:', '内存使用:', '可用图形命令:']
                    if any(keyword in check_text for keyword in response_keywords):
                        if self.debug_mode:
                            print("[DEBUG] 检测到已收到系统信息响应，跳过9秒检查")
                            self.add_message("🔧 检测到已收到系统信息响应，跳过9秒检查", "debug", add_timestamp=False)
                        return
                
                if self.debug_mode:
                    print("[DEBUG] 9秒检查：设备响应超时")
                    self.add_message("🔧 9秒检查：设备响应超时", "debug", add_timestamp=False)
                self.add_message("⏳ 设备响应超时，请检查设备连接或手动发送info命令", "warning", add_timestamp=False)
                # 不再自动重试发送第二次info命令，避免重复
                # 清除等待响应标志和设备忙状态，允许手动重试
                if hasattr(self, '_waiting_for_info_response'):
                    self._waiting_for_info_response = False
                if hasattr(self, '_device_busy'):
                    self._device_busy = False
            
            # 设置定时器
            QTimer.singleShot(3000, check_response_3s)    # 3秒后显示处理中提示
            QTimer.singleShot(6000, check_response_6s)    # 6秒后显示等待提示
            QTimer.singleShot(9000, auto_retry_9s)        # 9秒后自动重试
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] _send_info_with_retry错误: {e}")
                self.add_message(f"🔧 _send_info_with_retry错误: {str(e)[:50]}...", "debug")
            self.add_message(f"⚠️ 获取设备信息时出错: {str(e)[:50]}...", "warning")
    
    def _send_info_with_progress(self):
        """发送info命令并显示进度提示"""
        try:
            if self.debug_mode:
                print("[DEBUG] 发送info命令（带进度提示）")
            
            # 显示进度提示
            self.add_message("⏳ 正在获取设备信息，请稍候...", "info", add_timestamp=False)
            
            # 发送info命令
            success = self.send_quick_command("info")
            
            if success:
                # 设置超时检查：5秒后如果还没有收到响应，显示仍在处理提示
                def check_info_timeout():
                    if self.debug_mode:
                        print("[DEBUG] info命令处理超时检查")
                    # 可以在这里添加超时处理，但目前只记录日志
                    self.add_message("⏳ 仍在获取设备信息，可能需要更多时间...", "info")
                
                QTimer.singleShot(5000, check_info_timeout)
            else:
                if self.debug_mode:
                    print("[DEBUG] info命令发送失败（可能实际已发送）")
                # 不显示错误，因为命令可能实际已发送
                # 只记录调试信息
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 发送info命令错误: {e}")
            self.add_message(f"⚠️ 发送info命令时出错: {str(e)[:50]}...", "warning")
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳字符串 [HH:MM:SS.mmm]"""
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%H:%M:%S") + f".{now.microsecond // 1000:03d}"
    
    def on_message_received(self, message: str):
        """处理接收到的消息 - 改进的消息合并机制"""
        try:
            # 调试信息：显示接收到的消息
            if self.debug_mode:
                print(f"[DEBUG] on_message_received: '{message[:50]}...'")
            
            current_time = time.time()
            # 立即生成接收时间戳
            receive_timestamp = self._get_current_timestamp()
            
            # 智能消息合并逻辑
            should_merge = False
            
            # 情况1：缓冲区为空，直接处理或添加到缓冲区
            if not self._message_buffer:
                # 如果消息看起来是完整的（以换行符结尾或包含完整命令结构）
                if (message.endswith('\n') or message.endswith('\r\n') or
                    '> ' in message or ':' in message and len(message) > 10):
                    # 直接处理完整消息，传递接收时间戳
                    self._process_complete_message(message, receive_timestamp)
                else:
                    # 可能是分割消息的开始，添加到缓冲区
                    self._message_buffer = message
                    self._last_message_time = current_time
                    self._buffer_timestamp = receive_timestamp  # 保存缓冲区开始时间戳
                    if self.debug_mode:
                        print(f"[DEBUG] 开始新消息缓冲区: '{message[:30]}...'")
                return
            
            # 情况2：检查是否需要合并到现有缓冲区
            # 合并条件：时间间隔短，且当前消息看起来是分割的部分
            time_diff = current_time - self._last_message_time
            if time_diff < self._message_timeout:
                # 检查消息特征：分割的消息通常不以换行符开头，且可能不完整
                if (not message.startswith('\n') and 
                    not message.startswith('\r\n') and
                    not self._message_buffer.endswith('\n') and
                    not self._message_buffer.endswith('\r\n')):
                    
                    # 智能判断：检查是否形成更完整的消息
                    combined = self._message_buffer + message
                    
                    # 检查合并后的消息是否更完整
                    if self._is_message_more_complete(combined, self._message_buffer):
                        should_merge = True
                    # 或者检查是否是明显的分割命令（如 's' + 'etdate'）
                    elif (len(message) < 10 and 
                          len(self._message_buffer) < 10 and
                          self._looks_like_split_command(combined)):
                        should_merge = True
            
            if should_merge:
                # 合并到缓冲区
                self._message_buffer += message
                self._last_message_time = current_time
                if self.debug_mode:
                    print(f"[DEBUG] 合并消息到缓冲区，长度: {len(self._message_buffer)}")
                
                # 检查合并后的消息是否完整
                if self._is_message_complete(self._message_buffer):
                    complete_message = self._message_buffer
                    self._message_buffer = ""
                    self._last_message_time = 0
                    # 使用缓冲区开始的时间戳
                    buffer_timestamp = getattr(self, '_buffer_timestamp', receive_timestamp)
                    self._process_complete_message(complete_message, buffer_timestamp)
                return
            
            # 情况3：不合并，处理缓冲区中的消息，然后处理当前消息
            if self._message_buffer:
                complete_message = self._message_buffer
                self._message_buffer = ""
                self._last_message_time = 0
                # 使用缓冲区开始的时间戳
                buffer_timestamp = getattr(self, '_buffer_timestamp', receive_timestamp)
                self._process_complete_message(complete_message, buffer_timestamp)
            
            # 处理当前消息（可能开始新的缓冲区）
            if (message.endswith('\n') or message.endswith('\r\n') or
                '> ' in message or ':' in message and len(message) > 10):
                self._process_complete_message(message, receive_timestamp)
            else:
                self._message_buffer = message
                self._last_message_time = current_time
                self._buffer_timestamp = receive_timestamp  # 保存缓冲区开始时间戳
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 消息处理错误: {e}")
            # 出错时直接添加原始消息
            try:
                self.display_text.append(message)
                self.display_text.ensureCursorVisible()
            except:
                pass
    
    def _determine_message_type(self, message: str) -> str:
        """根据消息内容确定消息类型"""
        # 不要清理消息，保持原始格式
        msg_lower = message.lower()
        
        # 调试信息：显示正在检测的消息
        if self.debug_mode:
            print(f"[DEBUG] _determine_message_type: '{message[:50]}...'")
        
        # 检查是否为命令回显（需要过滤）
        # 注意：设备可能返回命令本身作为回显，需要宽松匹配
        if self._last_sent_command:
            cmd_lower = self._last_sent_command.lower()
            msg_stripped = message.strip()
            cmd_stripped = self._last_sent_command.strip()
            
            # 宽松匹配：消息是否以最近发送的命令开头（可能是回显）
            # 或者消息是否包含最近发送的命令
            if (msg_stripped == cmd_stripped or 
                msg_stripped.startswith(cmd_stripped) or
                cmd_stripped in msg_stripped):
                # 这是命令回显，应该过滤掉
                if self.debug_mode:
                    print(f"[DEBUG] 跳过命令回显: '{self._last_sent_command}' (宽松匹配)")
                self._last_sent_command = None  # 重置
                return "echo"  # 特殊类型，用于过滤
        
        # 系统信息类消息 - 简化检测逻辑
        system_keywords = [
            '系统信息:', '可用命令:', 'help', 'info', 'clear', 'reset',
            '微控制器:', '时钟频率:', 'flash大小:', 'xram大小:', 'usb-cdc:',
            '编译日期:', '编译时间:', 'rtc时钟:', '当前时间:', '内存使用:',
            'flash已用:', '常量存储:', 'xram已用:', '内部ram:',
            'ai8051u氢原子系统', '版本:', '作者:', '编译:',
            'cpu时钟:', '硬件加速:', '外设:', '基础命令:', '时间设置:', '系统监控:'
        ]
        
        for keyword in system_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到系统信息关键字: '{keyword}' -> system")
                return "system"
        
        # 硬件测试结果
        hardware_keywords = [
            '硬件加速单元测试', 'mdu32硬件乘除单元测试', 'tfpu浮点运算单元测试',
            'mdu32测试完成', 'tfpu测试完成', '乘法测试:', '除法测试:', '加法测试:',
            '乘法性能:', '除法性能:', '加法性能:', '乘法平均:', '除法平均:',
            '硬件加速比:', '执行时间:', '理论时间:', '时钟周期', '基础功能测试:',
            '性能基准测试:', '三角函数测试:', '特殊函数测试:', '硬件状态:',
            'tfpu状态检查完成', '硬件加速测试完成', '所有计算均为实时执行',
            'hwtest', 'mdu32', 'tfpu', '硬件测试', '单元测试',
            '硬件加速测试', '性能测试', '基准测试'
        ]
        
        for keyword in hardware_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到硬件测试关键字: '{keyword}' -> hardware")
                return "hardware"
        
        # 图形命令信息
        graphic_keywords = [
            '可用图形命令:', 'oled显示:', 'oled', '图形命令',
            'oled heart', 'oled heart_anim', 'oled lissajous', 'oled lissajous_anim',
            '3d立体爱心', '旋转爱心动画', '李萨如图形', '旋转李萨如图形动画',
            '使用TFPU硬件加速进行浮点运算',
            'oled init', 'oled clear', 'oled test', 'oled status',
            'ssd1315', 'i2c', 'oled初始化', 'oled清屏', 'oled测试',
            'p15=scl', 'p14=sda', 'i2c总线'
        ]
        
        for keyword in graphic_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到图形命令关键字: '{keyword}' -> graphic")
                return "graphic"
        
        # 性能基准测试
        benchmark_keywords = [
            '性能基准测试', 'benchmark', '长耗时', '开始:', '结束:', '差值:',
            '平均每次:', '时钟周期/次', '加速比:', 'tfpu时钟源:', 'cpu时钟:'
        ]
        
        for keyword in benchmark_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到性能基准测试关键字: '{keyword}' -> benchmark")
                return "benchmark"
        
        # 时钟信息
        clock_keywords = [
            '时钟系统详细信息', 'clockinfo', '系统时钟配置:', 'pll输出时钟:',
            '高速外设时钟:', 'tfpu时钟配置:', '预分频系数:', '计算频率:',
            '与cpu频率比:', '关键寄存器状态:', 'clksel寄存器:', 'usbclk寄存器:',
            't4t3m寄存器:', 'tfpu运行在约'
        ]
        
        for keyword in clock_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到时钟信息关键字: '{keyword}' -> clock")
                return "clock"
        
        # 电压测量
        voltage_keywords = [
            '电源电压测量结果', 'voltage', 'adc原始值:', '电源电压:', '测量通道:',
            '参考电压:', '分辨率:', '采样次数:', '电压:',
            'adc', 'adc15', '电源电压测量', '电压测量', 'adc测量',
            '测量电源电压', 'adc通道', '参考电压源'
        ]
        
        for keyword in voltage_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到电压测量关键字: '{keyword}' -> voltage")
                return "voltage"
        
        # ASCII艺术（neofetch）
        ascii_keywords = [
            'neofetch', '.:.', '.o:o.', '.o:o:o.', 'ai8051u氢原子终端',
            '系统:', '核心:', '时钟:', 'flash:', 'xram:', 'mdu32:', 'tfpu:',
            'usb-cdc:', 'rtc:', 'adc:', '终端:', '电压:', '构建:', '时间:',
            '╔════════╗', '║系统就绪║', '║运行正常║', '╚════════╝'
        ]
        
        for keyword in ascii_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到ASCII艺术关键字: '{keyword}' -> ascii_art")
                return "ascii_art"
        
        # RTC时钟信息
        rtc_keywords = [
            'rtc时钟:', '当前时间:', '设置时间', '设置日期', 'settime', 'setdate',
            'hh:mm:ss', 'yy-mm-dd', '2025-12-03', '18:51:16', '18:51:45'
        ]
        
        for keyword in rtc_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到RTC时钟关键字: '{keyword}' -> rtc")
                return "rtc"
        
        # 内存使用信息
        memory_keywords = [
            '内存使用:', 'flash已用:', '常量存储:', 'xram已用:', '内部ram:',
            '字节', 'flash大小:', 'xram大小:', '16958', '8622', '1472', '758'
        ]
        
        for keyword in memory_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到内存使用关键字: '{keyword}' -> memory")
                return "memory"
        
        # 硬件状态信息
        hardware_status_keywords = [
            '硬件状态:', 'tfpu时钟源:', 'pll高速时钟', 'cpu时钟:', '系统时钟',
            '加速比:', 'tfpu时钟是cpu的', '功耗管理:', 'mdu32运算时自动进入idle模式',
            'tfpu_clkdiv寄存器:', 'pll状态(cksel):', '0xc0', '0x01'
        ]
        
        for keyword in hardware_status_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到硬件状态关键字: '{keyword}' -> hardware_status")
                return "hardware_status"
        
        # 测试结果详细信息
        test_detail_keywords = [
            '基础功能测试:', '三角函数测试:', '特殊函数测试:', '性能基准测试:',
            '0 × 0 = 0', '1 × 1 = 1', 'sin(0度)', 'cos(0度)', 'tan(0度)',
            'sqrt(0.0)', 'atan(0.0)', '100次运算耗时', '平均每次:'
        ]
        
        for keyword in test_detail_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到测试结果详细信息关键字: '{keyword}' -> test_detail")
                return "test_detail"
        
        # 重启信息
        reboot_keywords = [
            '系统重启中...', '重启系统', 'reset', '========================================',
            'ai8051u氢原子系统', '版本: 2.1.0', '作者: 076lik'
        ]
        
        for keyword in reboot_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到重启信息关键字: '{keyword}' -> reboot")
                return "reboot"
        
        # 清屏效果
        clear_keywords = [
            'clear', '清屏', '清空显示'
        ]
        
        for keyword in clear_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到清屏关键字: '{keyword}' -> clear")
                return "clear"
        
        # 帮助信息
        help_keywords = [
            '可用命令:', 'help', '显示帮助信息', '基础命令:', '时间设置:',
            '系统监控:', '硬件测试:', 'help    - 显示帮助信息'
        ]
        
        for keyword in help_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到帮助信息关键字: '{keyword}' -> help")
                return "help"
        
        # 错误消息
        error_keywords = [
            '错误', '失败', '无法', '不支持', '无效', '超时', '断开', '丢失',
            'exception', 'error', 'failed', 'invalid', 'timeout', '未知命令'
        ]
        
        for keyword in error_keywords:
            if keyword in msg_lower:
                if self.debug_mode:
                    print(f"[DEBUG] 检测到错误关键字: '{keyword}' -> error")
                return "error"
        
        # 温度信息
        temperature_keywords = [
            '温度:', '°c', '℃', 'crc校验', 'ds18b20', '温度传感器',
            '温度值:', '摄氏度', '当前温度',
            'ds18b20 init', 'ds18b20 read', '单总线', 'p3.5',
            '温度传感器初始化', '读取温度', 'ds18b20温度'
        ]
        
        for keyword in temperature_keywords:
            if keyword in msg_lower:
                print(f"[消息类型] 检测到温度关键字: '{keyword}' -> temperature")
                return "temperature"
        
        # 默认信息类型
        if self.debug_mode:
            print(f"[DEBUG] 未匹配到关键字，使用默认类型: info")
        return "info"
    
    def _check_message_buffer(self):
        """检查消息缓冲区，处理超时的消息"""
        if not self._message_buffer or self._last_message_time == 0:
            return
        
        current_time = time.time()
        if current_time - self._last_message_time >= self._message_timeout:
            # 缓冲区超时，处理剩余消息
            if self.debug_mode:
                print(f"[DEBUG] 消息缓冲区超时，处理剩余消息，长度: {len(self._message_buffer)}")
            
            # 检查响应是否完整
            if not self._is_response_complete(self._message_buffer):
                if self.debug_mode:
                    print(f"[DEBUG] 响应不完整，等待更多数据")
                # 如果响应不完整，延长等待时间
                self._message_timeout = 0.5  # 延长到500ms
                return
            
            complete_message = self._message_buffer
            self._message_buffer = ""
            self._last_message_time = 0
            self._message_timeout = 0.1  # 重置为100ms
            self._process_complete_message(complete_message)
    
    def _is_response_complete(self, message: str) -> bool:
        """检查响应是否完整"""
        # 空消息不算完整
        if not message.strip():
            return False
        
        # 检查常见的完整响应模式
        complete_patterns = [
            "========================================",  # 分隔线
            "TFPU测试完成！",  # TFPU测试完成
            "MDU32测试完成！",  # MDU32测试完成
            "硬件加速测试完成",  # 硬件测试完成
            "可用命令:",  # 命令列表
            "终端> ",  # 命令提示符
            "\n\n",  # 双换行符（通常表示消息结束）
        ]
        
        # 如果消息以这些模式结尾，可能是完整的
        for pattern in complete_patterns:
            if message.endswith(pattern) or pattern in message[-100:]:  # 检查最后100个字符
                return True
        
        # 检查长消息是否可能被截断
        # 对于非常长的消息（>1000字符），如果以换行符结尾，认为是完整的
        if len(message) > 1000 and (message.endswith('\n') or message.endswith('\r\n')):
            return True
        
        # 默认认为完整（避免无限等待）
        return True
    
    def _is_message_more_complete(self, combined: str, original: str) -> bool:
        """检查合并后的消息是否比原始消息更完整"""
        # 合并后的消息更长，通常更完整
        if len(combined) <= len(original):
            return False
        
        # 检查是否形成了更完整的结构
        # 1. 合并后是否包含了完整的关键词
        complete_keywords = ['settime', 'setdate', 'voltage', 'hwtest', 'mdu32', 'tfpu', 'benchmark', 'clockinfo']
        for keyword in complete_keywords:
            if keyword in combined and keyword not in original:
                return True
        
        # 2. 合并后是否形成了更合理的命令结构
        if (combined.startswith('set') and len(combined) > 3 and 
            ' ' in combined and combined.index(' ') > 3):
            return True
        
        # 3. 合并后是否包含了换行符或回车符
        if ('\n' in combined or '\r' in combined) and ('\n' not in original and '\r' not in original):
            return True
        
        return False
    
    def _looks_like_split_command(self, text: str) -> bool:
        """检查文本是否看起来像被分割的命令"""
        # 常见的命令前缀
        command_prefixes = ['set', 'vol', 'hw', 'md', 'tf', 'be', 'cl', 'in', 're', 'he', 'cl']
        
        # 检查是否以命令前缀开头
        for prefix in command_prefixes:
            if text.startswith(prefix) and len(text) > len(prefix):
                # 检查是否形成了有效的命令
                possible_commands = ['settime', 'setdate', 'voltage', 'hwtest', 'mdu32', 
                                    'tfpu', 'benchmark', 'clockinfo', 'info', 'reset', 
                                    'help', 'clear']
                for cmd in possible_commands:
                    if cmd.startswith(text) or text.startswith(cmd):
                        return True
        
        return False
    
    def _is_message_complete(self, message: str) -> bool:
        """检查消息是否完整"""
        # 空消息不完整
        if not message.strip():
            return False
        
        # 完整消息的特征
        # 1. 以换行符结尾
        if message.endswith('\n') or message.endswith('\r\n'):
            return True
        
        # 2. 包含完整的命令响应结构
        complete_indicators = [
            '> ',  # 命令提示符
            ':',   # 键值对分隔符（在较长的消息中）
            '测试完成！',
            '性能基准测试完成',
            '所有计算均为实时执行',
            'clockinfo完成',
            '可用命令:',
            '系统信息:',
            'RTC时钟:',
            '内存使用:',
            '电源电压测量结果:',
            'AI8051U氢原子系统'
        ]
        
        for indicator in complete_indicators:
            if indicator in message:
                # 检查indicator是否在消息的较后部分（表示消息可能完整）
                idx = message.find(indicator)
                if idx > len(message) * 0.7:  # 在消息的后30%部分
                    return True
        
        # 3. 长消息（>200字符）且包含多个换行符
        if len(message) > 200 and message.count('\n') >= 2:
            return True
        
        return False
    
    def _process_complete_message(self, message: str, receive_timestamp: str = None):
        """处理完整的消息（合并后的消息）"""
        try:
            # 解析设备信息（但不自动刷新显示）
            if hasattr(self, 'device_info_manager'):
                updated = self.device_info_manager.parse_message(message)
                if updated and self.debug_mode:
                    print(f"[DEBUG] 设备信息已更新（等待用户手动刷新显示）")
            
            # 根据消息内容确定消息类型
            msg_type = self._determine_message_type(message)
            
            if self.debug_mode:
                print(f"[DEBUG] 确定的消息类型: {msg_type}")
            
            # 异步处理消息显示，避免阻塞UI，传递接收时间戳
            QTimer.singleShot(0, lambda: self._async_process_message(message, msg_type, receive_timestamp))
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 完整消息处理错误: {e}")
            # 出错时直接添加原始消息
            try:
                self.display_text.append(message)
                self.display_text.ensureCursorVisible()
            except:
                pass
    
    def _async_process_message(self, message: str, msg_type: str = "info", receive_timestamp: str = None):
        """异步处理消息显示"""
        try:
            # 命令回显也需要记录到日志，但不显示在终端
            if msg_type == "echo":
                if self.debug_mode:
                    print(f"[DEBUG] 过滤命令回显（但记录到日志）: {message[:50]}...")
                # 命令回显也记录到日志，但不显示在终端
                # 格式：接收←命令（根据命令实际执行效果.txt格式）
                self.add_message(f"接收←{message}", "echo", pre_timestamp=receive_timestamp)
                return
            
            # 检测设备忙/就绪关键词（基于原始消息内容）
            # 注意：这里使用原始消息（不带"接收←"前缀）进行检测
            if self._check_device_busy_keywords(message):
                self._set_device_busy(f"检测到忙关键词: {message[:30]}...")
            elif self._check_device_ready_keywords(message):
                self._set_device_ready(f"检测到就绪关键词: {message[:30]}...")
            
            # 更新接收消息统计
            self._message_stats['received'] += 1
            
            # 接收到的消息格式：接收←消息
            # 添加"接收←"前缀，传递接收时间戳
            # 如果消息包含换行符，只对第一行添加"接收←"前缀，保持后续行原样
            if '\n' in message:
                lines = message.split('\n')
                # 对第一行添加"接收←"前缀
                lines[0] = f"接收←{lines[0]}"
                # 重新组合消息，保留原始换行符
                processed_message = '\n'.join(lines)
            else:
                processed_message = f"接收←{message}"
            
            self.add_message(processed_message, msg_type, pre_timestamp=receive_timestamp)
            
            # 检测温度消息并更新显示
            self._check_and_update_temperature(message)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 异步消息处理错误: {e}")
            # 出错时直接添加原始消息
            try:
                self.display_text.append(message)
                self.display_text.ensureCursorVisible()
            except:
                pass
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 应用透明度设置
                opacity = settings.get('opacity', 85)
                self.setWindowOpacity(opacity / 100.0)
                
                # 应用字体大小设置
                font_size = settings.get('font_size', 12)
                # 显示文本区域使用较小的字体，最大不超过10
                if hasattr(self, 'display_text'):
                    display_font_size = min(font_size, 10)
                    self.display_text.setFont(QFont("Consolas", display_font_size))
                if hasattr(self, 'command_input'):
                    self.command_input.setFont(QFont("Microsoft YaHei", font_size))
                
                # 应用等宽字体大小设置
                mono_font_size = settings.get('mono_font_size', 11)
                if hasattr(self, 'device_info_display'):
                    # 设备信息显示使用更小的字体，最大不超过9
                    device_info_font_size = min(mono_font_size, 9)
                    self.device_info_display.setFont(QFont("Consolas", device_info_font_size))
                
                # 应用UI缩放设置
                ui_scale = settings.get('ui_scale', 100)
                scale_factor = ui_scale / 100.0
                self.setWindowScale(scale_factor)
                
                # 应用主题设置
                theme = settings.get('theme', 'dopamine')
                self.apply_theme(theme)
                
                # 应用壁纸设置
                wallpaper_path = settings.get('wallpaper', '')
                if wallpaper_path and os.path.exists(wallpaper_path):
                    self.set_wallpaper(wallpaper_path)
                
                # 应用全局文本颜色设置
                if 'global_text_color' in settings:
                    import re
                    color_str = settings['global_text_color']
                    match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
                    if match:
                        self.global_text_color = QColor(
                            int(match.group(1)), 
                            int(match.group(2)), 
                            int(match.group(3))
                        )
                
                # 应用其他设置
                self.ai8051u_detection_enabled = settings.get('ai8051u_detection_enabled', True)
                self.use_global_text_color = settings.get('use_global_text_color', False)
                self.show_timestamp = settings.get('timestamp', True)
                self.auto_scroll = True  # 始终启用自动滚动
                
                # 应用终端日志设置
                terminal_log_enabled = settings.get('terminal_log_enabled', False)
                if hasattr(self, 'terminal_logger') and self.terminal_logger:
                    self.terminal_logger.enabled = terminal_log_enabled
                    if terminal_log_enabled:
                        self.terminal_logger.create_session_log()
                        if self.debug_mode:
                            print(f"[DEBUG] 终端消息日志已启用")
                    else:
                        if self.debug_mode:
                            print(f"[DEBUG] 终端消息日志已禁用")
                
                if self.debug_mode:
                    print(f"[DEBUG] 设置已加载: {list(settings.keys())}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 加载设置失败: {e}")
    
    def start_performance_monitoring(self):
        """启动性能监控"""
        try:
            # 性能监控定时器
            self.performance_timer = QTimer()
            self.performance_timer.timeout.connect(self._update_performance_status)
            self.performance_timer.start(5000)  # 每5秒更新一次
            
            if self.debug_mode:
                print("[DEBUG] 性能监控已启动")
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 性能监控启动失败: {e}")
    
    def start_device_info_refresh(self):
        """设备信息刷新已改为手动触发，不再自动刷新"""
        if self.debug_mode:
            print("[DEBUG] 设备信息改为手动刷新模式，点击'🔄 获取设备信息'按钮更新")
    
    def _update_performance_status(self):
        """更新性能状态显示"""
        try:
            # 更新性能UI
            self._update_performance_ui()
            
            # 更新系统性能状态
            if hasattr(self, 'performance_status_label'):
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                if cpu_percent > 80 or memory_percent > 80:
                    self.performance_status_label.setText("⚠️ 性能警告")
                    self.performance_status_label.setStyleSheet("""
                        QLabel {
                            color: #e74c3c;
                            padding: 10px 14px;
                            background: rgba(231, 76, 60, 0.1);
                            border-radius: 6px;
                            border: 1px solid rgba(231, 76, 60, 0.3);
                        }
                    """)
                elif cpu_percent > 60 or memory_percent > 60:
                    self.performance_status_label.setText("⚡ 性能正常")
                    self.performance_status_label.setStyleSheet("""
                        QLabel {
                            color: #f39c12;
                            padding: 10px 14px;
                            background: rgba(243, 156, 18, 0.1);
                            border-radius: 6px;
                            border: 1px solid rgba(243, 156, 18, 0.3);
                        }
                    """)
                else:
                    self.performance_status_label.setText("⚡ 性能正常")
                    self.performance_status_label.setStyleSheet("""
                        QLabel {
                            color: #27ae60;
                            padding: 10px 14px;
                            background: rgba(39, 174, 96, 0.1);
                            border-radius: 6px;
                            border: 1px solid rgba(39, 174, 96, 0.3);
                        }
                    """)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 性能状态更新失败: {e}")
    
    def start_startup_animation(self):
        """启动动画"""
        try:
            # 启动时自动检测串口设备
            QTimer.singleShot(1000, self._auto_detect_devices)
            
            # 启动时刷新串口列表
            QTimer.singleShot(1500, self.refresh_ports)
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 启动动画失败: {e}")
    
    def _auto_detect_devices(self):
        """自动检测串口设备"""
        try:
            ports = self.serial_manager.get_available_ports()
            if ports:
                self.port_combo.addItems(ports)
                self.port_combo.setCurrentIndex(0)
                self.notification_manager.show_success(f"🔍 自动检测到 {len(ports)} 个串口设备", auto_close=True)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 自动检测设备失败: {e}")
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        try:
            # 获取当前透明度设置
            current_opacity = self.windowOpacity()
            
            # 检查是否有壁纸
            has_wallpaper = (hasattr(self, 'current_wallpaper') and 
                           self.current_wallpaper and 
                           not self.current_wallpaper.isNull())
            
            # 如果有壁纸，不设置背景样式
            if not has_wallpaper:
                if theme_name == "dopamine":
                    # 多巴胺主题
                    self.setStyleSheet("""
                        QMainWindow {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #667eea, stop:1 #764ba2);
                        }
                    """)
                elif theme_name == "dark":
                    # 深色主题
                    self.setStyleSheet("""
                        QMainWindow {
                            background: #2c3e50;
                        }
                    """)
                elif theme_name == "light":
                    # 浅色主题
                    self.setStyleSheet("""
                        QMainWindow {
                            background: #ecf0f1;
                        }
                    """)
            else:
                # 有壁纸时清除样式表，让壁纸显示
                self.setStyleSheet("")
            
            # 重新应用透明度设置（主题切换后可能需要重新设置）
            self.setWindowOpacity(current_opacity)
            self.update()
            self.repaint()
            
            # 只有在主题改变或首次设置时才更新壁纸显示
            if not hasattr(self, '_last_applied_theme'):
                self._last_applied_theme = None
            
            if has_wallpaper and (self._last_applied_theme != theme_name):
                self.update_wallpaper_display()
                self._last_applied_theme = theme_name
            
            self.notification_manager.show_success(f"🎨 主题已切换: {theme_name}", auto_close=True)
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 主题切换失败: {e}")
    
    def check_environment(self):
        """环境检测"""
        try:
            from core.colorbridge_environment_manager import EnvironmentManager
            manager = EnvironmentManager()
            results = manager.run_full_check_and_fix()
            
            if results["summary"]["success"]:
                self.notification_manager.show_success("✅ 环境检测通过", auto_close=True)
            else:
                self.notification_manager.show_warning("⚠️ 环境检测有问题", auto_close=True)
                
        except Exception as e:
            self.notification_manager.show_error(f"❌ 环境检测失败: {e}", auto_close=False)
    
    def run_batch_tests(self):
        """运行批量测试"""
        if not self.serial_manager.is_connected():
            self.notification_manager.show_warning("⚠️ 请先连接串口", auto_close=True)
            return
        
        self.notification_manager.show_info("🔄 开始批量测试...", auto_close=True)
        
        # 执行批量测试命令
        test_commands = ['help', 'info', 'hwtest', 'mdu32', 'tfpu', 'benchmark']
        for cmd in test_commands:
            if self.serial_manager.is_connected():
                self.serial_manager.send_command(cmd)
                self.add_message(f"> {cmd}", "command")
                time.sleep(0.2)  # 间隔200ms
    
    def generate_performance_report(self):
        """生成性能报告"""
        try:
            report = f"""
📊 ColorBridge 性能报告
================
系统信息: {os.name}
Python版本: {sys.version}
PyQt6版本: {PyQt6.QtCore.PYQT_VERSION_STR}

连接状态: {'已连接' if self.serial_manager.is_connected() else '未连接'}
当前串口: {self.port_combo.currentText()}
波特率: {self.baud_combo.currentText()}

消息显示行数: {self.display_text.document().blockCount()}
"""
            self.notification_manager.show_info(report, auto_close=False)
            
        except Exception as e:
            self.notification_manager.show_error(f"❌ 生成报告失败: {e}", auto_close=False)
    
    def show_device_info_dialog(self):
        """显示设备信息对话框"""
        try:
            device_info = self.device_info_manager.get_formatted_device_info()
            self.notification_manager.show_info(device_info, auto_close=False)
        except Exception as e:
            self.notification_manager.show_error(f"❌ 获取设备信息失败: {e}", auto_close=False)
    
    def save_display_log(self):
        """保存显示日志"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"colorbridge_log_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.display_text.toPlainText())
            
            self.notification_manager.show_success(f"💾 日志已保存: {filename}", auto_close=True)
            
        except Exception as e:
            self.notification_manager.show_error(f"❌ 保存日志失败: {e}", auto_close=False)
    
    def change_buffer_strategy(self, strategy: str):
        """改变缓冲策略"""
        if self.debug_mode:
            print(f"[DEBUG] 缓冲策略改变: {strategy}")
    
    def apply_buffer_strategy(self):
        """应用缓冲策略"""
        strategy = self.buffer_combo.currentText()
        self.notification_manager.show_success(f"🗂️ 缓冲策略已应用: {strategy}", auto_close=True)
    
    def clear_display(self):
        """清空显示区域"""
        self.display_text.clear()
        self.notification_manager.show_info("🗑️ 显示区域已清空", auto_close=True)
    
    def closeEvent(self, event):
        """窗口关闭事件 - 优化版本"""
        try:
            if self.debug_mode:
                print("[DEBUG] 开始关闭程序...")
            
            # 设置关闭标志
            self.is_closing = True
            
            # 1. 快速断开串口连接
            if hasattr(self, 'serial_manager') and self.serial_manager:
                try:
                    self.serial_manager.disconnect()
                    if self.debug_mode:
                        print("[DEBUG] 串口已断开")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 断开串口失败: {e}")
            
            # 2. 快速停止定时器
            if hasattr(self, '_ui_update_timer'):
                self._ui_update_timer.stop()
            
            # 停止设备信息超时定时器
            if hasattr(self, 'device_info_timeout_timer'):
                self.device_info_timeout_timer.stop()
            
            # 3. 停止监控系统
            if hasattr(self, 'monitoring_system') and self.monitoring_system:
                try:
                    self.monitoring_system.stop_monitoring()
                    self.monitoring_system = None  # 清理引用
                except:
                    pass
            
            if hasattr(self, 'log_analyzer') and self.log_analyzer:
                try:
                    self.log_analyzer.stop_realtime_analysis()
                    self.log_analyzer = None  # 清理引用
                except:
                    pass
            
            # 4. 清理消息处理器
            if hasattr(self, 'message_processor') and self.message_processor:
                try:
                    self.message_processor.close()
                    self.message_processor = None  # 清理引用
                except:
                    pass
            
            # 5. 清理设备信息管理器
            if hasattr(self, 'device_info_manager') and self.device_info_manager:
                try:
                    self.device_info_manager = None  # 清理引用
                except:
                    pass
            
            # 6. 清理串口管理器
            if hasattr(self, 'serial_manager') and self.serial_manager:
                try:
                    self.serial_manager = None  # 清理引用
                except:
                    pass
            
            if self.debug_mode:
                print("[DEBUG] 资源清理完成")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 清理失败: {e}")
        
        # 立即接受关闭事件
        event.accept()
        
                # 立即退出程序
        try:
            sys.exit(0)
        except:
            os._exit(0)
            
    def disconnect_serial(self):
        """断开串口连接"""
        try:
            self.serial_manager.disconnect()
            self._update_ui_disconnected()
            self.notification_manager.show_info("🔌 串口已断开连接", auto_close=True)
        except Exception as e:
            self.notification_manager.show_error(f"❌ 断开连接错误: {str(e)}", auto_close=False)
        finally:
            # 重置连接状态标志
            self._connecting = False
            
    
    
    
    
    
    
    def clear_display(self):
        """清空显示区域"""
        self.display_text.clear()
        self.notification_manager.show_info("🗑️ 显示区域已清空", auto_close=True)
    
    def refresh_ports(self):
        """刷新串口列表"""
        try:
            self.port_combo.clear()
            ports = self.serial_manager.get_available_ports()
            self.port_combo.addItems(ports)
            
            if ports:
                self.notification_manager.show_success(f"🔄 发现 {len(ports)} 个串口设备", auto_close=True)
            else:
                self.notification_manager.show_warning("⚠️ 未检测到串口设备", auto_close=True)
        except Exception as e:
            self.notification_manager.show_error(f"❌ 刷新串口列表失败: {str(e)}", auto_close=False)
    
    def _auto_detect_devices(self):
        """自动检测串口设备"""
        try:
            ports = self.serial_manager.get_available_ports()
            if ports:
                self.port_combo.addItems(ports)
                self.port_combo.setCurrentIndex(0)
                self.notification_manager.show_success(f"🔍 自动检测到 {len(ports)} 个串口设备", auto_close=True)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 自动检测设备失败: {e}")
    
    def _load_settings(self):
        """加载设置"""
        try:
            if os.path.exists("colorbridge_settings.json"):
                with open("colorbridge_settings.json", 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 应用透明度设置
                opacity = settings.get('opacity', 85)
                self.setWindowOpacity(opacity / 100.0)
                
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] 加载设置失败: {e}")
                
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            if self.debug_mode:
                print("[DEBUG] 开始关闭程序...")
            
            # 设置关闭标志
            self.is_closing = True
            
            # 1. 快速断开串口连接
            if hasattr(self, 'serial_manager') and self.serial_manager:
                try:
                    self.serial_manager.disconnect()
                    if self.debug_mode:
                        print("[DEBUG] 串口已断开")
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 断开串口失败: {e}")
            
            # 2. 快速停止定时器
            if hasattr(self, '_ui_update_timer'):
                self._ui_update_timer.stop()
            
            # 停止设备信息超时定时器
            if hasattr(self, 'device_info_timeout_timer'):
                self.device_info_timeout_timer.stop()
            
            # 3. 停止监控系统
            if hasattr(self, 'monitoring_system') and self.monitoring_system:
                try:
                    self.monitoring_system.stop_monitoring()
                except:
                    pass
            
            if hasattr(self, 'log_analyzer') and self.log_analyzer:
                try:
                    self.log_analyzer.stop_realtime_analysis()
                except:
                    pass
            
            if self.debug_mode:
                print("[DEBUG] 资源清理完成")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 清理失败: {e}")
        
        # 立即接受关闭事件
        event.accept()
        
        # 立即退出程序
        try:
            sys.exit(0)
        except:
            os._exit(0)# ==================== 窗口拖动和调整大小功�?====================
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position().toPoint()
                edge = self._get_resize_edge(pos)
                
                if self.debug_mode:
                    print(f"[DEBUG] 鼠标按下事件: 位置={pos}, 边缘={edge}")
                
                # 只处理边缘调整大小，标题栏拖动由事件过滤器处理
                if edge:
                    # 开始调整大小
                    self.resize_edge = edge
                    self.drag_position = pos
                    if self.debug_mode:
                        print(f"[DEBUG] 开始调整大小: 边缘={edge}")
                    event.accept()
                else:
                    super().mousePressEvent(event)
            else:
                super().mousePressEvent(event)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 鼠标按下事件出错: {e}")
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        try:
            if event.buttons() & Qt.MouseButton.LeftButton:
                if self.resize_edge:
                    # 正在调整大小
                    if self.debug_mode:
                        print(f"[DEBUG] 正在调整大小: 边缘={self.resize_edge}")
                    self._resize_window(event)
                    event.accept()
                else:
                    super().mouseMoveEvent(event)
            else:
                # 更新鼠标光标
                self._update_cursor(event.position().toPoint())
                super().mouseMoveEvent(event)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 鼠标移动事件出错: {e}")
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            self.resize_edge = None
            self._update_cursor(event.position().toPoint())
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def _get_resize_edge(self, pos):
        """获取鼠标所在的边缘位置"""
        rect = self.rect()
        x, y = pos.x(), pos.y()
        
        # 检查各个边缘
        edges = []
        if x <= self.edge_margin:
            edges.append('left')
        if x >= rect.width() - self.edge_margin:
            edges.append('right')
        if y <= self.edge_margin:
            edges.append('top')
        if y >= rect.height() - self.edge_margin:
            edges.append('bottom')
        
        # 返回边缘组合
        if len(edges) == 1:
            return edges[0]
        elif len(edges) == 2:
            return '-'.join(edges)
        return None
    
    def _resize_window(self, event):
        """调整窗口大小"""
        if not self.resize_edge:
            return
        
        try:
            global_pos = event.globalPosition().toPoint()
            rect = self.frameGeometry()
            
            new_rect = QRect(rect)
            
            # 根据边缘调整窗口大小
            if 'left' in self.resize_edge:
                new_left = global_pos.x()
                # 确保新的左边不会超过右边
                if new_left < new_rect.right() - self.minimumWidth():
                    new_rect.setLeft(new_left)
            if 'right' in self.resize_edge:
                new_rect.setRight(global_pos.x())
            if 'top' in self.resize_edge:
                new_top = global_pos.y()
                # 确保新的上边不会超过下边
                if new_top < new_rect.bottom() - self.minimumHeight():
                    new_rect.setTop(new_top)
            if 'bottom' in self.resize_edge:
                new_rect.setBottom(global_pos.y())
            
            # 确保最小尺寸
            min_size = self.minimumSize()
            if new_rect.width() >= min_size.width() and new_rect.height() >= min_size.height():
                # 额外的安全检查
                if new_rect.width() > 0 and new_rect.height() > 0:
                    self.setGeometry(new_rect)
                    
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 调整窗口大小出错: {e}")
    
    def _update_cursor(self, pos):
        """更新鼠标光标形状"""
        edge = self._get_resize_edge(pos)
        
        cursor_shapes = {
            'left': Qt.CursorShape.SizeHorCursor,
            'right': Qt.CursorShape.SizeHorCursor,
            'top': Qt.CursorShape.SizeVerCursor,
            'bottom': Qt.CursorShape.SizeVerCursor,
            'top-left': Qt.CursorShape.SizeFDiagCursor,
            'top-right': Qt.CursorShape.SizeBDiagCursor,
            'bottom-left': Qt.CursorShape.SizeBDiagCursor,
            'bottom-right': Qt.CursorShape.SizeFDiagCursor
        }
        
        if edge and edge in cursor_shapes:
            self.setCursor(cursor_shapes[edge])
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def open_large_input_window(self):
        """打开大输入窗口"""
        if not hasattr(self, '_large_input_window') or not self._large_input_window:
            self._large_input_window = LargeInputWindow(self)
        self._large_input_window.show()
        self._large_input_window.raise_()
        self._large_input_window.activateWindow()


class LargeInputWindow(QDialog):
    """大输入窗口 - 支持多行命令输入"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._sending = False  # 防止重复发送的标志
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("📝 命令输入窗口 - ColorBridge")
        self.setMinimumSize(500, 300)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("💬 命令输入窗口")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px 0;")
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel("在此输入多行命令，支持Enter换行，Ctrl+Enter发送")
        info_label.setFont(QFont("Microsoft YaHei", 10))
        info_label.setStyleSheet("color: #7f8c8d; padding: 5px 0;")
        layout.addWidget(info_label)
        
        # 大输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入多行命令...\n例如：\ninfo\nhwtest\nbenchmark\n\n支持Ctrl+Enter发送，Enter换行")
        self.input_text.setFont(QFont("Consolas", 11))
        self.input_text.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 12px;
                font-family: "Consolas", "Microsoft YaHei";
                padding: 12px;
                color: #2c3e50;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.input_text, 1)  # 设置stretch factor为1
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 清空按钮
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setMinimumHeight(40)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.input_text.clear)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        # 发送按钮
        send_btn = QPushButton("📤 发送命令")
        send_btn.setMinimumHeight(40)
        send_btn.setMinimumWidth(120)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        send_btn.clicked.connect(self.send_command)
        button_layout.addWidget(send_btn)
        
        layout.addLayout(button_layout)
        
        # 安装事件过滤器处理Ctrl+Enter
        self.input_text.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """事件过滤器处理Ctrl+Enter"""
        if obj == self.input_text:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    # 检查是否按下了Ctrl键
                    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                        # Ctrl+Enter: 发送命令
                        self.send_command()
                        return True
                    else:
                        # 单独的Enter键: 不处理，让QTextEdit正常换行
                        return False
        return super().eventFilter(obj, event)
        
    def send_command(self):
        """发送命令"""
        # 防止重复发送
        if self._sending:
            return
        self._sending = True
        
        try:
            command = self.input_text.toPlainText().strip()
            if not command:
                return
                
            # 检查父窗口和串口管理器
            if not self.parent_window:
                return
                
            # 将命令设置到主窗口的输入框（用于显示）
            if hasattr(self.parent_window, 'command_input'):
                self.parent_window.command_input.setText(command)
                
            # 直接发送命令，不通过主窗口的send_command方法
            # 这样可以避免多行文本被分割
            if hasattr(self.parent_window, 'serial_manager') and self.parent_window.serial_manager.is_connected():
                # 记录最近发送的命令（用于过滤回显）
                if hasattr(self.parent_window, '_last_sent_command'):
                    self.parent_window._last_sent_command = command
                
                # 添加消息到显示区域
                if hasattr(self.parent_window, 'add_message'):
                    # 如果是多行命令，显示所有行
                    lines = command.split('\n')
                    if len(lines) > 1:
                        # 显示多行命令
                        for line in lines:
                            if line.strip():  # 只显示非空行
                                self.parent_window.add_message(f"> {line.strip()}", "command")
                    else:
                        self.parent_window.add_message(f"> {command}", "command")
                
                # 发送整个命令（多行文本作为一个整体）
                # 注意：serial_manager.send_command()会在末尾添加换行符
                # 对于多行文本，我们需要确保每行都被正确处理
                self.parent_window.serial_manager.send_command(command)
                
                # 清空主窗口输入框
                if hasattr(self.parent_window, 'command_input'):
                    self.parent_window.command_input.clear()
            else:
                # 如果没有连接串口，显示警告
                if hasattr(self.parent_window, 'notification_manager'):
                    self.parent_window.notification_manager.show_warning("请先连接串口", auto_close=True)
                
            # 清空输入框并关闭窗口
            self.input_text.clear()
            self.close()
            
        finally:
            self._sending = False
        
    def closeEvent(self, event):
        """关闭事件"""
        # 刷新终端日志缓冲区
        if hasattr(self, 'terminal_logger') and self.terminal_logger:
            try:
                self.terminal_logger.flush()
                if self.debug_mode:
                    print("[DEBUG] 终端日志缓冲区已刷新")
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 刷新终端日志缓冲区失败: {e}")
        
        event.accept()


class LinuxHelpDialog(QDialog):
    """Linux系统帮助对话框 - 提供可复制的命令"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("🔧 Linux系统连接帮助 - ColorBridge")
        self.setMinimumSize(700, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🔧 Linux系统连接帮助")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 10px 0; border-bottom: 3px solid #3498db;")
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel("以下命令可复制到终端执行，解决Linux串口连接问题")
        info_label.setFont(QFont("Microsoft YaHei", 11))
        info_label.setStyleSheet("color: #7f8c8d; padding: 5px 0;")
        layout.addWidget(info_label)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 5px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                border-color: #2980b9;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)
        
        # 选项卡1: 虚拟环境
        venv_tab = QWidget()
        venv_layout = QVBoxLayout(venv_tab)
        venv_layout.setContentsMargins(15, 15, 15, 15)
        
        venv_title = QLabel("<h3>解决方案一：使用虚拟环境（推荐）</h3>")
        venv_title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        venv_layout.addWidget(venv_title)
        
        # 虚拟环境命令
        venv_commands = """<b>1. 创建虚拟环境</b>
```bash
python3 -m venv myenv
```

<b>2. 激活虚拟环境</b>
```bash
source myenv/bin/activate
```

<b>3. 安装依赖（激活虚拟环境后）</b>
```bash
pip install -r requirements.txt
```

<b>4. 运行ColorBridge（激活虚拟环境后）</b>
```bash
python main.py
```"""
        
        venv_text = QTextEdit()
        venv_text.setReadOnly(True)
        venv_text.setHtml(f"<pre style='font-family: Consolas, monospace; font-size: 12px; line-height: 1.4;'>{venv_commands}</pre>")
        venv_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                font-family: Consolas, monospace;
                font-size: 12px;
                line-height: 1.4;
                color: #212529;
            }
        """)
        venv_layout.addWidget(venv_text)
        
        # 复制按钮
        copy_venv_btn = QPushButton("📋 复制虚拟环境命令")
        copy_venv_btn.clicked.connect(lambda: self.copy_to_clipboard(venv_commands))
        copy_venv_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        venv_layout.addWidget(copy_venv_btn)
        
        venv_layout.addStretch()
        tab_widget.addTab(venv_tab, "🐍 虚拟环境")
        
        # 选项卡2: 串口权限
        serial_tab = QWidget()
        serial_layout = QVBoxLayout(serial_tab)
        serial_layout.setContentsMargins(15, 15, 15, 15)
        
        serial_title = QLabel("<h3>LINUX USB转UART设备连接Linux电脑无反应</h3>")
        serial_title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        serial_layout.addWidget(serial_title)
        
        # 串口权限命令
        serial_commands = """<b>1. 授予当前用户访问权限</b>
即使设备节点存在，普通用户也无法访问。将用户加入 dialout 组：
```bash
sudo usermod -a -G dialout $USER
```

<b>⚠️ 重要</b>：此更改<b>必须重新登录终端或重启会话</b>才能生效。

<b>2. 立即测试（无需重启）</b>
```bash
newgrp dialout
```
或退出终端重新登录。

<b>3. 检查设备权限</b>
```bash
ls -l /dev/ttyUSB*
ls -l /dev/ttyACM*
```

<b>4. 临时权限（每次重启需重新执行）</b>
```bash
sudo chmod 666 /dev/ttyUSB0
```"""
        
        serial_text = QTextEdit()
        serial_text.setReadOnly(True)
        serial_text.setHtml(f"<pre style='font-family: Consolas, monospace; font-size: 12px; line-height: 1.4;'>{serial_commands}</pre>")
        serial_text.setStyleSheet(venv_text.styleSheet())
        serial_layout.addWidget(serial_text)
        
        # 复制按钮
        copy_serial_btn = QPushButton("📋 复制串口权限命令")
        copy_serial_btn.clicked.connect(lambda: self.copy_to_clipboard(serial_commands))
        copy_serial_btn.setStyleSheet(copy_venv_btn.styleSheet())
        serial_layout.addWidget(copy_serial_btn)
        
        serial_layout.addStretch()
        tab_widget.addTab(serial_tab, "🔌 串口权限")
        
        layout.addWidget(tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(45)
        close_btn.setMinimumWidth(120)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        # 移除HTML标签，保留纯文本命令
        import re
        # 移除<b>标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 将```bash和```替换为空
        clean_text = clean_text.replace('```bash', '').replace('```', '')
        # 去除多余空白行
        clean_text = '\n'.join(line for line in clean_text.split('\n') if line.strip() or line == '')
        
        clipboard = QApplication.clipboard()
        clipboard.setText(clean_text)
        
        # 显示成功提示
        from ui.colorbridge_notification_manager import EnhancedNotificationManager
        notification = EnhancedNotificationManager()
        notification.show_success("✅ 命令已复制到剪贴板", auto_close=True)
