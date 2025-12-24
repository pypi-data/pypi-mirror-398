#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的多巴胺风格通知系统 - ColorBridge PCL2风格
支持跳动效果、闪烁错误指示和丰富的动画效果
"""

import sys
import math
import random
from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                            QFrame, QPushButton, QGraphicsOpacityEffect,
                            QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QBrush, QLinearGradient

class BounceAnimation:
    """跳动动画类"""
    
    def __init__(self, target_widget):
        self.target = target_widget
        self.animation = QPropertyAnimation(target_widget, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.original_pos = target_widget.pos()
        
    def start_bounce(self, duration: int = 800, height: int = 10):
        """开始跳动动画"""
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.original_pos)
        self.animation.setEndValue(self.original_pos)
        
        # 设置关键帧
        self.animation.setKeyValueAt(0.0, self.original_pos)
        self.animation.setKeyValueAt(0.3, QPoint(self.original_pos.x(), int(self.original_pos.y() - height)))
        self.animation.setKeyValueAt(0.5, QPoint(self.original_pos.x(), int(self.original_pos.y() - height * 0.5)))
        self.animation.setKeyValueAt(0.7, QPoint(self.original_pos.x(), int(self.original_pos.y() - height * 0.8)))
        self.animation.setKeyValueAt(1.0, self.original_pos)
        
        self.animation.start()

class FlashAnimation:
    """闪烁动画类"""
    
    def __init__(self, target_widget):
        self.target = target_widget
        self.opacity_animation = QPropertyAnimation(target_widget, b"windowOpacity")
        self.original_opacity = target_widget.windowOpacity()
        self.flash_count = 0
        self.max_flashes = 3
        
    def start_flash(self, duration: int = 200, count: int = 3):
        """开始闪烁动画"""
        self.max_flashes = count
        self.flash_count = 0
        
        self.opacity_animation.setDuration(duration)
        self.opacity_animation.setLoopCount(count * 2)  # 每次闪烁包含淡入和淡出
        
        # 设置闪烁效果
        self.opacity_animation.setStartValue(self.original_opacity)
        self.opacity_animation.setEndValue(0.3)
        self.opacity_animation.finished.connect(self.on_flash_finished)
        
        self.opacity_animation.start()
        
    def on_flash_finished(self):
        """闪烁完成回调"""
        self.flash_count += 1
        if self.flash_count >= self.max_flashes:
            self.target.setWindowOpacity(self.original_opacity)

class GlowEffect(QGraphicsDropShadowEffect):
    """发光效果"""
    
    def __init__(self, color: QColor, radius: float = 10.0):
        super().__init__()
        self.setColor(color)
        self.setBlurRadius(radius)
        self.setOffset(0, 0)

class EnhancedNotificationWidget(QFrame):
    """增强的通知消息条 - 支持跳动和闪烁效果"""
    
    # 信号定义
    close_requested = pyqtSignal()
    clicked = pyqtSignal()
    
    def __init__(self, message: str, notification_type: str = "info", 
                 auto_close: bool = True, parent=None):
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        self.auto_close = auto_close
        self.is_closing = False
        
        # 动画组件
        self.bounce_animation = None
        self.flash_animation = None
        self.glow_effect = None
        
        # 设置通知样式
        self.setup_notification_style()
        
        # 创建UI
        self.setup_ui()
        
        # 设置自动关闭定时器
        if auto_close:
            self.auto_close_timer = QTimer()
            self.auto_close_timer.timeout.connect(self.start_close_animation)
            self.auto_close_timer.start(5000)  # 5秒后自动关闭
        else:
            self.auto_close_timer = None
        
        # 启动进入动画
        self.start_enter_effects()
    
    def setup_notification_style(self):
        """设置通知样式 - 多巴胺风格"""
        # 根据通知类型设置颜色
        type_styles = {
            "info": {
                "bg_gradient": [QColor(100, 150, 255), QColor(150, 100, 255)],
                "border_color": QColor(80, 130, 235),
                "icon": "ℹ️",
                "text_color": QColor(255, 255, 255),
                "glow_color": QColor(100, 150, 255, 100)
            },
            "warning": {
                "bg_gradient": [QColor(255, 200, 100), QColor(255, 150, 50)],
                "border_color": QColor(235, 180, 80),
                "icon": "⚠️",
                "text_color": QColor(50, 50, 50),
                "glow_color": QColor(255, 200, 100, 100)
            },
            "error": {
                "bg_gradient": [QColor(255, 100, 100), QColor(255, 50, 50)],
                "border_color": QColor(235, 80, 80),
                "icon": "❌",
                "text_color": QColor(255, 255, 255),
                "glow_color": QColor(255, 100, 100, 100)
            },
            "success": {
                "bg_gradient": [QColor(100, 255, 100), QColor(50, 255, 50)],
                "border_color": QColor(80, 235, 80),
                "icon": "✅",
                "text_color": QColor(50, 50, 50),
                "glow_color": QColor(100, 255, 100, 100)
            },
            "system": {
                "bg_gradient": [QColor(150, 100, 255), QColor(200, 100, 255)],
                "border_color": QColor(130, 80, 235),
                "icon": "🔧",
                "text_color": QColor(255, 255, 255),
                "glow_color": QColor(150, 100, 255, 100)
            }
        }
        
        self.style_config = type_styles.get(self.notification_type, type_styles["info"])
        
        # 设置固定高度和样式
        self.setFixedHeight(70)  # 增加高度以容纳动画效果
        self.setObjectName("notificationFrame")
        
        # 添加发光效果
        self.glow_effect = GlowEffect(self.style_config["glow_color"], 15.0)
        self.setGraphicsEffect(self.glow_effect)
        
        # 设置样式表
        self.update_stylesheet()
        
    def update_stylesheet(self):
        """更新样式表"""
        bg_colors = self.style_config["bg_gradient"]
        border_color = self.style_config["border_color"]
        text_color = self.style_config["text_color"]
        
        self.setStyleSheet(f"""
            QFrame#notificationFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_colors[0].name()},
                    stop:1 {bg_colors[1].name()});
                border: 2px solid {border_color.name()};
                border-radius: 15px;
                margin: 2px;
            }}
            
            QFrame#notificationFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_colors[0].lighter(110).name()},
                    stop:1 {bg_colors[1].lighter(110).name()});
                border: 2px solid {border_color.lighter(110).name()};
            }}
            
            QLabel#notificationIcon {{
                color: {text_color.name()};
                font-size: 28px;
                font-weight: bold;
            }}
            
            QLabel#notificationText {{
                color: {text_color.name()};
                font-size: 15px;
                font-weight: bold;
                background: transparent;
            }}
            
            QPushButton#closeButton {{
                background: transparent;
                border: none;
                color: {text_color.name()};
                font-size: 20px;
                font-weight: bold;
                padding: 6px;
                border-radius: 8px;
            }}
            
            QPushButton#closeButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }}
        """)
    
    def setup_ui(self):
        """创建UI组件"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 12, 12)
        layout.setSpacing(15)
        
        # 图标
        icon_label = QLabel(self.style_config["icon"])
        icon_label.setObjectName("notificationIcon")
        icon_label.setFixedWidth(35)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 消息文本
        text_label = QLabel(self.message)
        text_label.setObjectName("notificationText")
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(text_label, 1)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.start_close_animation)
        layout.addWidget(close_btn)
        
        # 设置鼠标悬停效果
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def start_enter_effects(self):
        """启动进入效果"""
        # 跳动动画
        self.bounce_animation = BounceAnimation(self)
        self.bounce_animation.start_bounce(duration=600, height=8)
        
        # 如果是错误类型，添加闪烁效果
        if self.notification_type == "error":
            QTimer.singleShot(800, self.start_error_flash)
            
    def start_error_flash(self):
        """启动错误闪烁效果"""
        self.flash_animation = FlashAnimation(self)
        self.flash_animation.start_flash(duration=150, count=4)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        
        # 暂停自动关闭定时器
        if self.auto_close_timer and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
            
        # 增强发光效果
        if self.glow_effect:
            self.glow_effect.setBlurRadius(25.0)
            
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        
        # 恢复自动关闭定时器
        if self.auto_close_timer and not self.is_closing:
            self.auto_close_timer.start(3000)  # 3秒后关闭
            
        # 恢复发光效果
        if self.glow_effect:
            self.glow_effect.setBlurRadius(15.0)
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            # 添加点击反馈动画
            self.bounce_animation = BounceAnimation(self)
            self.bounce_animation.start_bounce(duration=300, height=5)
        super().mousePressEvent(event)
    
    def start_close_animation(self):
        """开始关闭动画"""
        if self.is_closing:
            return
            
        self.is_closing = True
        
        # 停止自动关闭定时器
        if self.auto_close_timer:
            self.auto_close_timer.stop()
        
        # 关闭发光效果
        if self.glow_effect:
            self.glow_effect.setBlurRadius(0.0)
        
        # 创建淡出动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.close_notification)
        self.fade_animation.start()
    
    def close_notification(self):
        """关闭通知"""
        self.close_requested.emit()
        self.close()


class EnhancedNotificationManager(QWidget):
    """增强的通知管理器（修复无限递归问题）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.notifications: List[EnhancedNotificationWidget] = []
        self.max_notifications = 5  # 最大同时显示的通知数量
        
        # 通知防重复机制
        self.recent_notifications = []  # 最近通知缓存
        self.max_recent_cache = 20  # 最大缓存数量
        self.notification_cooldown = 2.0  # 2秒冷却时间
        
        # 调试模式标志
        self.debug_mode = True
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 设置布局
        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.layout)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
    def setup_layout(self):
        """设置布局"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 设置自身样式
        self.setStyleSheet("background: transparent;")
        
    def setup_background_effect(self):
        """设置背景效果"""
        # 简化背景效果，避免布局冲突
        self.setStyleSheet("""
            EnhancedNotificationManager {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
    def show_notification(self, message: str, notification_type: str = "info", 
                         auto_close: bool = True) -> Optional[EnhancedNotificationWidget]:
        """显示通知（带防重复机制）"""
        import time
        
        # 检查是否为重复通知
        current_time = time.time()
        message_key = f"{notification_type}:{message}"
        
        # 清理过期的通知缓存
        self.recent_notifications = [
            (msg_key, timestamp) for msg_key, timestamp in self.recent_notifications
            if current_time - timestamp < self.notification_cooldown
        ]
        
        # 检查是否为重复通知
        for recent_key, timestamp in self.recent_notifications:
            if recent_key == message_key:
                # 重复通知，忽略
                return None
        
        # 添加到缓存
        self.recent_notifications.append((message_key, current_time))
        if len(self.recent_notifications) > self.max_recent_cache:
            self.recent_notifications.pop(0)
        
        # 如果已有太多通知，移除最旧的
        if len(self.notifications) >= self.max_notifications:
            oldest = self.notifications[0]
            oldest.start_close_animation()
        
        # 创建新通知
        notification = EnhancedNotificationWidget(message, notification_type, auto_close, self)
        notification.close_requested.connect(lambda: self.remove_notification(notification))
        
        # 添加到布局和列表
        self.layout.addWidget(notification)
        self.notifications.append(notification)
        
        # 显示通知
        notification.show()
        
        # 调整窗口大小
        self.adjust_size()
        
        return notification
    
    def remove_notification(self, notification: EnhancedNotificationWidget):
        """移除通知"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            self.layout.removeWidget(notification)
            notification.deleteLater()
            self.adjust_size()
    
    def adjust_size(self):
        """调整窗口大小"""
        total_height = 0
        for notification in self.notifications:
            total_height += notification.sizeHint().height() + self.layout.spacing()
        
        # 添加边距
        total_height += self.layout.contentsMargins().top() + self.layout.contentsMargins().bottom()
        
        # 如果有父窗口，计算合适的大小
        if self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
            
            # 限制宽度不超过450px或父窗口宽度减去边距
            max_width = min(450, parent_width - 40)
            
            # 限制高度不超过父窗口高度的80%
            max_height = int(parent_height * 0.8)
            
            # 确保总高度不超过最大高度
            total_height = min(total_height, max_height)
            
            self.setFixedSize(max_width, total_height)
        else:
            # 没有父窗口时的默认大小
            self.setFixedSize(450, total_height)
    
    def clear_all_notifications(self):
        """清除所有通知"""
        for notification in self.notifications.copy():
            notification.start_close_animation()
    
    def show_info(self, message: str, auto_close: bool = True):
        """显示信息通知"""
        if self.debug_mode:
            print(f"[DEBUG] 通知[INFO]: {message}")
        return self.show_notification(message, "info", auto_close)
    
    def show_warning(self, message: str, auto_close: bool = True):
        """显示警告通知"""
        if self.debug_mode:
            print(f"[DEBUG] 通知[WARNING]: {message}")
        return self.show_notification(message, "warning", auto_close)
    
    def show_error(self, message: str, auto_close: bool = False):
        """显示错误通知 - 默认不自动关闭"""
        if self.debug_mode:
            print(f"[DEBUG] 通知[ERROR]: {message}")
        return self.show_notification(message, "error", auto_close)
    
    def show_success(self, message: str, auto_close: bool = True):
        """显示成功通知"""
        if self.debug_mode:
            print(f"[DEBUG] 通知[SUCCESS]: {message}")
        return self.show_notification(message, "success", auto_close)
    
    def show_system(self, message: str, auto_close: bool = True):
        """显示系统通知"""
        if self.debug_mode:
            print(f"[DEBUG] 通知[SYSTEM]: {message}")
        return self.show_notification(message, "system", auto_close)
    
    def show_bouncing_notification(self, message: str, notification_type: str = "info"):
        """显示带跳动效果的通知"""
        notification = self.show_notification(message, notification_type, auto_close=False)
        
        # 添加额外的跳动效果
        QTimer.singleShot(1000, lambda: self.trigger_extra_bounce(notification))
        
        return notification
    
    def trigger_extra_bounce(self, notification: EnhancedNotificationWidget):
        """触发额外的跳动效果"""
        if notification and not notification.is_closing:
            bounce = BounceAnimation(notification)
            bounce.start_bounce(duration=400, height=6)
    
    def cascade_notifications(self, messages: List[str], notification_type: str = "info", delay: int = 800):
        """级联显示多个通知"""
        for i, message in enumerate(messages):
            QTimer.singleShot(i * delay, lambda m=message: self.show_notification(m, notification_type))