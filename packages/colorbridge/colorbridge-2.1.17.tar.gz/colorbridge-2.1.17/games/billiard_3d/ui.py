"""
台球游戏UI界面模块
实现2D模仿3D的台球游戏界面
"""

import math
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSlider, QFrame, QGraphicsView, 
                            QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
                            QGraphicsLineItem, QGraphicsRectItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (QPainter, QBrush, QColor, QPen, QLinearGradient, 
                        QRadialGradient, QFont, QPainterPath)

from .core import BilliardGame, Ball, BallType


class BilliardBallItem(QGraphicsEllipseItem):
    """台球图形项"""
    def __init__(self, ball: Ball, debug_mode: bool = False, parent=None):
        super().__init__(parent)
        self.ball = ball
        self.debug_mode = debug_mode
        self.original_radius = ball.radius
        self.setRect(-ball.radius, -ball.radius, 
                    ball.radius * 2, ball.radius * 2)
        self.setPos(ball.x, ball.y)
        self.setBrush(self._get_ball_brush())
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # 动画相关
        self.animation_timer = None
        self.animation_step = 0
        self.max_animation_steps = 10  # 动画总步数
        
        # 启用鼠标事件
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
    
    def _get_ball_brush(self) -> QBrush:
        """获取球的画刷"""
        if self.ball.ball_type == BallType.CUE:
            # 母球 - 白色带渐变
            gradient = QRadialGradient(0, 0, self.ball.radius)
            gradient.setColorAt(0, QColor(255, 255, 255, 255))
            gradient.setColorAt(0.7, QColor(240, 240, 240, 255))
            gradient.setColorAt(1, QColor(220, 220, 220, 255))
            return QBrush(gradient)
            
        elif self.ball.ball_type == BallType.BLACK:
            # 黑8球
            gradient = QRadialGradient(0, 0, self.ball.radius)
            gradient.setColorAt(0, QColor(50, 50, 50, 255))
            gradient.setColorAt(0.7, QColor(30, 30, 30, 255))
            gradient.setColorAt(1, QColor(10, 10, 10, 255))
            return QBrush(gradient)
            
        elif self.ball.ball_type == BallType.SOLID:
            # 实心球 - 根据数字选择颜色
            colors = [
                QColor(255, 50, 50),    # 1: 红色
                QColor(255, 165, 0),    # 2: 橙色
                QColor(255, 255, 0),    # 3: 黄色
                QColor(0, 128, 0),      # 4: 绿色
                QColor(0, 0, 255),      # 5: 蓝色
                QColor(75, 0, 130),     # 6: 靛蓝色
                QColor(238, 130, 238),  # 7: 紫色
            ]
            color_idx = (self.ball.number - 1) % len(colors)
            gradient = QRadialGradient(0, 0, self.ball.radius)
            gradient.setColorAt(0, colors[color_idx].lighter(150))
            gradient.setColorAt(0.7, colors[color_idx])
            gradient.setColorAt(1, colors[color_idx].darker(150))
            return QBrush(gradient)
            
        else:  # STRIPE
            # 条纹球 - 白色带彩色条纹
            stripe_colors = [
                QColor(255, 50, 50),    # 9: 红色条纹
                QColor(255, 165, 0),    # 10: 橙色条纹
                QColor(255, 255, 0),    # 11: 黄色条纹
                QColor(0, 128, 0),      # 12: 绿色条纹
                QColor(0, 0, 255),      # 13: 蓝色条纹
                QColor(75, 0, 130),     # 14: 靛蓝色条纹
                QColor(238, 130, 238),  # 15: 紫色条纹
            ]
            color_idx = (self.ball.number - 9) % len(stripe_colors)
            return QBrush(QColor(255, 255, 255, 255))
    
    def paint(self, painter: QPainter, option, widget=None):
        """绘制球"""
        super().paint(painter, option, widget)
        
        # 如果球进袋了且动画已完成，不绘制
        if self.ball.is_pocketed and self.animation_timer is None:
            return
        
        # 绘制球上的数字（除了母球）
        if self.ball.ball_type != BallType.CUE:
            painter.setPen(QPen(Qt.GlobalColor.white if self.ball.ball_type == BallType.BLACK else Qt.GlobalColor.black, 1))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            
            # 绘制数字
            text = str(self.ball.number)
            text_rect = painter.fontMetrics().boundingRect(text)
            painter.drawText(-text_rect.width() // 2, text_rect.height() // 4, text)
        
        # 如果是条纹球，绘制彩色条纹
        if self.ball.ball_type == BallType.STRIPE:
            stripe_colors = [
                QColor(255, 50, 50),    # 9: 红色条纹
                QColor(255, 165, 0),    # 10: 橙色条纹
                QColor(255, 255, 0),    # 11: 黄色条纹
                QColor(0, 128, 0),      # 12: 绿色条纹
                QColor(0, 0, 255),      # 13: 蓝色条纹
                QColor(75, 0, 130),     # 14: 靛蓝色条纹
                QColor(238, 130, 238),  # 15: 紫色条纹
            ]
            color_idx = (self.ball.number - 9) % len(stripe_colors)
            
            stripe_width = self.ball.radius * 0.6
            stripe_height = self.ball.radius * 1.2
            
            painter.setBrush(QBrush(stripe_colors[color_idx]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(-stripe_width/2, -stripe_height/2, 
                                      stripe_width, stripe_height))
    
    def update_position(self):
        """更新球的位置"""
        if not self.ball.is_pocketed:
            # 如果球之前进袋了但现在不是进袋状态（只对母球）
            if self.ball.ball_type == BallType.CUE and not self.isVisible():
                # 调试信息：母球从进袋状态恢复
                if self.debug_mode:
                    print(f"[DEBUG] 母球从进袋状态恢复，重新显示")
                self.setVisible(True)
                # 重置大小和透明度
                self.setRect(-self.original_radius, -self.original_radius,
                           self.original_radius * 2, self.original_radius * 2)
                # 重置画刷透明度
                brush = self.brush()
                color = brush.color()
                color.setAlphaF(1.0)
                brush.setColor(color)
                self.setBrush(brush)
            
            # 更新位置
            self.setPos(self.ball.x, self.ball.y)
            # 调试信息：显示母球位置
            if self.debug_mode and self.ball.ball_type == BallType.CUE:
                print(f"[DEBUG] 母球位置更新: ({self.ball.x:.1f}, {self.ball.y:.1f}), 可见: {self.isVisible()}")
        elif self.ball.is_pocketed and self.animation_timer is None:
            # 球刚进袋，开始动画
            if self.debug_mode and self.ball.ball_type == BallType.CUE:
                print(f"[DEBUG] 母球进袋，开始动画")
            self.start_pocket_animation()
    
    def start_pocket_animation(self):
        """开始进袋动画"""
        self.animation_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(50)  # 每50ms更新一次动画
    
    def _update_animation(self):
        """更新动画"""
        if self.animation_step >= self.max_animation_steps:
            # 动画完成，停止定时器
            self.animation_timer.stop()
            self.animation_timer = None
            # 完全隐藏球
            self.setVisible(False)
            return
        
        # 计算缩放比例（从1到0）
        scale = 1.0 - (self.animation_step / self.max_animation_steps)
        
        # 更新球的大小
        current_radius = self.original_radius * scale
        self.setRect(-current_radius, -current_radius, 
                    current_radius * 2, current_radius * 2)
        
        # 更新透明度
        brush = self.brush()
        color = brush.color()
        color.setAlphaF(scale)  # 设置透明度
        brush.setColor(color)
        self.setBrush(brush)
        
        self.animation_step += 1
        self.update()


class BilliardTableItem(QGraphicsRectItem):
    """台球桌图形项"""
    def __init__(self, table_width: float, table_height: float, parent=None):
        super().__init__(0, 0, table_width, table_height, parent)
        self.table_width = table_width
        self.table_height = table_height
        self.cushion_width = 20
        self.pocket_radius = 25
        
        # 设置样式
        self.setBrush(self._get_table_brush())
        self.setPen(QPen(QColor(139, 69, 19), 2))  # 棕色边框
        
        # 创建球袋
        self._create_pockets()
    
    def _get_table_brush(self) -> QBrush:
        """获取台球桌的画刷"""
        # 创建绿色渐变模拟3D效果
        gradient = QLinearGradient(0, 0, 0, self.table_height)
        gradient.setColorAt(0, QColor(0, 100, 0, 255))      # 顶部较暗
        gradient.setColorAt(0.5, QColor(0, 150, 0, 255))    # 中间较亮
        gradient.setColorAt(1, QColor(0, 100, 0, 255))      # 底部较暗
        return QBrush(gradient)
    
    def _create_pockets(self):
        """创建球袋"""
        pockets = [
            (self.cushion_width, self.cushion_width),  # 左上
            (self.table_width // 2, self.cushion_width),     # 上中
            (self.table_width - self.cushion_width, self.cushion_width),  # 右上
            (self.cushion_width, self.table_height - self.cushion_width),  # 左下
            (self.table_width // 2, self.table_height - self.cushion_width),    # 下中
            (self.table_width - self.cushion_width, self.table_height - self.cushion_width)  # 右下
        ]
        
        for x, y in pockets:
            pocket = QGraphicsEllipseItem(x - self.pocket_radius, 
                                         y - self.pocket_radius,
                                         self.pocket_radius * 2,
                                         self.pocket_radius * 2,
                                         self)
            pocket.setBrush(QBrush(QColor(0, 0, 0, 200)))
            pocket.setPen(QPen(Qt.GlobalColor.black, 1))
    
    def paint(self, painter: QPainter, option, widget=None):
        """绘制台球桌"""
        super().paint(painter, option, widget)
        
        # 绘制3D效果的边框
        painter.setPen(QPen(QColor(101, 67, 33), 3))  # 深棕色
        painter.drawRect(self.rect())
        
        # 绘制阴影效果
        painter.setPen(QPen(QColor(0, 0, 0, 50), 2))
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))
        
        # 绘制桌边标记
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        for i in range(1, 4):
            x = int(self.table_width * i / 4)
            painter.drawLine(x, int(self.cushion_width), x, int(self.table_height - self.cushion_width))
        
        for i in range(1, 3):
            y = int(self.table_height * i / 3)
            painter.drawLine(int(self.cushion_width), y, int(self.table_width - self.cushion_width), y)


class BilliardGameUI(QWidget):
    """台球游戏UI主界面"""
    
    # 信号
    game_state_changed = pyqtSignal(str)
    shot_taken = pyqtSignal()
    
    def __init__(self, parent=None, debug_mode=False):
        super().__init__(parent)
        self.debug_mode = debug_mode
        try:
            self.game = BilliardGame()
            self.aim_angle = 0.0
            self.power_level = 0.0
            self.is_charging = False
            self.is_decaying = False  # 力气值是否在衰减
            self._last_game_state = None  # 用于优化显示更新
            
            # 设置窗口大小策略，允许窗口调整大小
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            self.setup_ui()
            self.setup_game_timer()
            self.setup_power_decay_timer()
            self.update_game_display()
            
            if self.debug_mode:
                print("[DEBUG] 游戏UI初始化完成")
        except Exception as e:
            print(f"[ERROR] 游戏UI初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def setup_ui(self):
        """设置UI界面"""
        # 主布局 - 改为水平布局，左侧游戏，右侧系统信息
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)
        
        # 左侧游戏区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        game_frame = QFrame()
        game_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        game_frame.setStyleSheet("background: rgba(40, 40, 40, 200); border: 2px solid #555; border-radius: 8px;")
        
        game_layout = QVBoxLayout(game_frame)
        
        # 创建图形视图
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.game.table.width, self.game.table.height)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 根据屏幕分辨率动态计算视图尺寸
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # 计算适合屏幕的视图尺寸（屏幕宽度的40%）
            view_width = int(screen_width * 0.4)
            view_height = int(view_width * (self.game.table.height / self.game.table.width))
            
            # 确保视图高度不超过屏幕高度的60%
            max_view_height = int(screen_height * 0.6)
            if view_height > max_view_height:
                view_height = max_view_height
                view_width = int(view_height * (self.game.table.width / self.game.table.height))
            
            if self.debug_mode:
                print(f"[DEBUG] 屏幕分辨率: {screen_width}x{screen_height}, 视图尺寸: {view_width}x{view_height}")
        else:
            # 备用方案：使用原始比例的80%
            view_width = int(self.game.table.width * 0.8)
            view_height = int(self.game.table.height * 0.8)
        
        # 使用最小尺寸而不是固定尺寸，允许窗口调整大小
        self.view.setMinimumSize(view_width, view_height)
        # 设置大小策略，允许视图扩展
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 简化样式表，避免解析错误
        self.view.setStyleSheet("background: #3c3c3c; border: 2px solid #777; border-radius: 6px;")
        
        # 添加台球桌
        self.table_item = BilliardTableItem(self.game.table.width, self.game.table.height)
        self.scene.addItem(self.table_item)
        
        # 添加台球
        self.ball_items = {}
        for ball in self.game.balls:
            ball_item = BilliardBallItem(ball, self.debug_mode)
            self.scene.addItem(ball_item)
            self.ball_items[id(ball)] = ball_item
        
        # 添加瞄准线
        self.aim_line = QGraphicsLineItem()
        self.aim_line.setPen(QPen(QColor(255, 255, 0, 150), 2, Qt.PenStyle.DashLine))
        self.scene.addItem(self.aim_line)
        
        # 添加力量指示器
        self.power_indicator = QGraphicsRectItem()
        self.power_indicator.setBrush(QBrush(QColor(255, 100, 100, 180)))
        self.power_indicator.setPen(QPen(Qt.GlobalColor.transparent))
        self.scene.addItem(self.power_indicator)
        
        game_layout.addWidget(self.view)
        
        # 控制面板
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        control_frame.setStyleSheet("background: rgba(50, 50, 50, 200); border: 1px solid #666; border-radius: 6px; padding: 10px;")
        
        control_layout = QVBoxLayout(control_frame)  # 改为垂直布局
        
        # 游戏状态显示
        self.status_label = QLabel("游戏状态: 瞄准中")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # 玩家信息（单人游戏）
        self.player_label = QLabel("单人游戏模式")
        self.player_label.setStyleSheet("""
            QLabel {
                color: #87CEEB;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # 分数显示
        self.score_label = QLabel("分数: 玩家1: 0 | 玩家2: 0")
        self.score_label.setStyleSheet("""
            QLabel {
                color: #98FB98;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # 控制按钮
        self.shot_button = QPushButton("击球")
        self.shot_button.setStyleSheet("""
            QPushButton {
                background: #FF4500;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #FF6347;
            }
            QPushButton:pressed {
                background: #DC143C;
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.shot_button.clicked.connect(self.take_shot)
        
        self.reset_button = QPushButton("重置游戏")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background: #4682B4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #5F9EA0;
            }
            QPushButton:pressed {
                background: #4169E1;
            }
        """)
        self.reset_button.clicked.connect(self.reset_game)
        # 确保重置按钮没有默认快捷键
        self.reset_button.setShortcut("")
        
        # 力量控制
        power_layout = QHBoxLayout()
        power_label = QLabel("力量:")
        power_label.setStyleSheet("color: #FFA07A; font-weight: bold;")
        
        self.power_slider = QSlider(Qt.Orientation.Horizontal)
        self.power_slider.setRange(0, 100)
        self.power_slider.setValue(0)
        self.power_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #FF0000;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
                border: 2px solid #888;
            }
        """)
        self.power_slider.valueChanged.connect(self.update_power)
        
        self.power_value_label = QLabel("0%")
        self.power_value_label.setStyleSheet("color: #FFD700; font-weight: bold;")
        
        power_layout.addWidget(power_label)
        power_layout.addWidget(self.power_slider)
        power_layout.addWidget(self.power_value_label)
        
        # 提示标签
        self.hint_label = QLabel("💡 提示: 鼠标瞄准，空格键蓄力，W键击球 (300%力量)")
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #90EE90;
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                font-style: italic;
            }
        """)
        
        # 添加到控制布局
        # 第一行：状态信息（水平排列）
        status_row = QHBoxLayout()
        status_row.addWidget(self.status_label)
        status_row.addWidget(self.player_label)
        status_row.addWidget(self.score_label)
        status_row.addStretch()
        control_layout.addLayout(status_row)
        
        # 第二行：提示信息
        control_layout.addWidget(self.hint_label)
        
        # 第三行：力量控制（水平排列）
        power_row = QHBoxLayout()
        power_row.addWidget(power_label)
        power_row.addWidget(self.power_slider)
        power_row.addWidget(self.power_value_label)
        power_row.addStretch()
        control_layout.addLayout(power_row)
        
        # 第四行：按钮（水平排列）
        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.shot_button)
        button_row.addWidget(self.reset_button)
        control_layout.addLayout(button_row)
        
        # 添加到左侧布局
        left_layout.addWidget(game_frame)
        left_layout.addWidget(control_frame)
        
        # 创建右侧系统信息面板
        right_widget = self._create_system_info_panel()
        
        # 添加到主布局（左侧游戏区域，右侧系统信息）
        main_layout.addWidget(left_widget, 4)  # 左侧占4份
        main_layout.addWidget(right_widget, 1)  # 右侧占1份
        
        # 设置鼠标跟踪
        self.view.setMouseTracking(True)
        self.view.mouseMoveEvent = self.handle_mouse_move
        self.view.mousePressEvent = self.handle_mouse_press
        self.view.mouseReleaseEvent = self.handle_mouse_release
        
        # 设置键盘焦点
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def setup_game_timer(self):
        """设置游戏定时器"""
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_game)
        self.game_timer.start(16)  # 约60FPS
    
    def setup_power_decay_timer(self):
        """设置力气值衰减定时器"""
        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self.decay_power)
        self.decay_timer.setInterval(100)  # 每100ms衰减一次
    
    def update_game(self):
        """更新游戏状态"""
        # 总是更新游戏逻辑（即使在aiming状态也需要更新，特别是母球重置后）
        if self.game.game_state == "moving":
            self.game.update(0.016)  # 16ms = 1/60秒
        
        # 总是更新球的位置（即使在aiming状态，母球重置后需要更新显示）
        balls_moved = False
        for ball in self.game.balls:
            if id(ball) in self.ball_items:
                ball_item = self.ball_items[id(ball)]
                old_pos = ball_item.pos()
                ball_item.update_position()
                new_pos = ball_item.pos()
                if old_pos != new_pos:
                    balls_moved = True
        
        # 只有球移动了或者状态变化时才更新显示
        if balls_moved or self._last_game_state != self.game.game_state:
            self.update_game_display()
            self._last_game_state = self.game.game_state
    
    def update_game_display(self):
        """更新游戏显示"""
        # 更新状态标签
        state_texts = {
            "setup": "设置中",
            "aiming": "瞄准中",
            "shooting": "击球中",
            "moving": "球运动中",
            "game_over": "游戏结束"
        }
        state_text = state_texts.get(self.game.game_state, "未知状态")
        self.status_label.setText(f"游戏状态: {state_text}")
        
        # 更新玩家标签（单人游戏）
        if self.game.game_state == "game_over":
            player_text = f"游戏结束: {self.game.winner}"
        else:
            player_text = "单人游戏模式"
        self.player_label.setText(player_text)
        
        # 更新分数标签（单人游戏）
        self.score_label.setText(f"得分: {self.game.player_score}")
        
        # 更新按钮状态
        self.shot_button.setEnabled(self.game.game_state == "aiming" and not self.game.cue_ball.is_pocketed)
        
        # 更新瞄准线
        self.update_aim_line()
        
        # 更新力量指示器
        self.update_power_indicator()
    
    def update_aim_line(self):
        """更新瞄准线"""
        if self.game.game_state != "aiming" or self.game.cue_ball.is_pocketed:
            self.aim_line.setLine(0, 0, 0, 0)
            return
        
        # 计算瞄准线
        cue_x, cue_y = self.game.cue_ball.x, self.game.cue_ball.y
        length = 100 + self.power_level * 2
        
        end_x = cue_x + math.cos(self.aim_angle) * length
        end_y = cue_y + math.sin(self.aim_angle) * length
        
        self.aim_line.setLine(cue_x, cue_y, end_x, end_y)
    
    def update_power_indicator(self):
        """更新力量指示器"""
        if self.game.game_state != "aiming" or self.game.cue_ball.is_pocketed:
            self.power_indicator.setRect(0, 0, 0, 0)
            return
        
        # 计算力量指示器位置
        cue_x, cue_y = self.game.cue_ball.x, self.game.cue_ball.y
        power_length = self.power_level * 2
        
        indicator_x = cue_x + math.cos(self.aim_angle) * power_length - 5
        indicator_y = cue_y + math.sin(self.aim_angle) * power_length - 5
        
        self.power_indicator.setRect(indicator_x, indicator_y, 10, 10)
    
    def handle_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.game.game_state != "aiming" or self.game.cue_ball.is_pocketed:
            return
        
        # 计算瞄准角度
        scene_pos = self.view.mapToScene(event.pos())
        cue_x, cue_y = self.game.cue_ball.x, self.game.cue_ball.y
        
        dx = scene_pos.x() - cue_x
        dy = scene_pos.y() - cue_y
        
        if dx == 0 and dy == 0:
            return
        
        self.aim_angle = math.atan2(dy, dx)
        self.game.aim_shot(self.aim_angle)
        self.update_aim_line()
    
    def handle_mouse_press(self, event):
        """处理鼠标按下事件 - 只用于瞄准"""
        if self.game.game_state != "aiming" or self.game.cue_ball.is_pocketed:
            return
        
        # 鼠标只用于瞄准，不用于击球
        # 击球功能已改为空格键
        pass
    
    def handle_mouse_release(self, event):
        """处理鼠标释放事件 - 只用于瞄准"""
        # 鼠标只用于瞄准，不用于击球
        # 击球功能已改为空格键
        pass
    
    def start_charging(self):
        """开始蓄力"""
        if self.is_charging:
            # 根据当前力气值计算蓄力速度
            charge_speed = self._calculate_charge_speed()
            
            # 增加力量
            self.power_level = min(self.power_level + charge_speed, 100)
            self.power_slider.setValue(int(self.power_level))
            
            # 将百分比转换为实际力量值 (0-300)
            actual_power = self.power_level * 3  # 100%对应300力量
            self.game.charge_power(actual_power)
            
            # 安排下一次蓄力更新
            QTimer.singleShot(50, self.start_charging)
        else:
            # 停止蓄力后开始衰减
            self.start_decay()
    
    def _calculate_charge_speed(self) -> float:
        """计算蓄力速度
        规则（基于百分比0-100%）：
        - 0-66%：正常速度（10%/秒）
        - 67-83%：速度减半（5%/秒）
        - 84-100%：速度再减半（2.5%/秒）
        注意：start_charging每50ms调用一次，所以需要转换为每50ms的速度
        """
        if self.power_level < 66:  # 0-66%（对应0-198力量）
            return 0.5  # 10%/秒 ÷ 20次/秒 = 0.5%/50ms
        elif self.power_level < 83:  # 67-83%（对应201-249力量）
            return 0.25  # 5%/秒 ÷ 20次/秒 = 0.25%/50ms
        else:  # 84-100%（对应252-300力量）
            return 0.125  # 2.5%/秒 ÷ 20次/秒 = 0.125%/50ms
    
    def update_power(self, value):
        """更新力量值"""
        self.power_level = value
        self.power_value_label.setText(f"{value}%")
        # 将百分比转换为实际力量值 (0-300)
        actual_power = value * 3  # 100%对应300力量
        self.game.charge_power(actual_power)
        self.update_power_indicator()
    
    def start_decay(self):
        """开始力气值衰减"""
        if self.power_level > 0 and not self.is_charging and not self.is_decaying:
            self.is_decaying = True
            self.decay_timer.start()
            if self.debug_mode:
                print("[DEBUG] 开始力气值衰减")
    
    def stop_decay(self):
        """停止力气值衰减"""
        if self.is_decaying:
            self.is_decaying = False
            self.decay_timer.stop()
            if self.debug_mode:
                print("[DEBUG] 停止力气值衰减")
    
    def decay_power(self):
        """衰减力气值"""
        if self.power_level > 0 and not self.is_charging:
            # 每100ms衰减2%
            self.power_level = max(self.power_level - 2, 0)
            self.power_slider.setValue(int(self.power_level))
            
            # 将百分比转换为实际力量值 (0-300)
            actual_power = self.power_level * 3
            self.game.charge_power(actual_power)
            
            if self.debug_mode and self.power_level % 10 == 0:
                print(f"[DEBUG] 力气值衰减到: {self.power_level}%")
            
            # 如果力气值降到0，停止衰减
            if self.power_level <= 0:
                self.stop_decay()
        else:
            self.stop_decay()
    
    def take_shot(self):
        """击球"""
        if self.game.game_state == "aiming" and not self.game.cue_ball.is_pocketed:
            self.game.take_shot()
            self.shot_taken.emit()
            self.update_game_display()
            # 击球后停止衰减
            self.stop_decay()
            if self.debug_mode:
                print("[DEBUG] 击球完成，停止衰减")
    
    def keyPressEvent(self, event):
        """键盘按下事件处理"""
        key = event.key()
        
        # 只在瞄准状态下处理键盘事件
        if self.game.game_state != "aiming" or self.game.cue_ball.is_pocketed:
            super().keyPressEvent(event)
            return
        
        if key == Qt.Key.Key_Space:
            # 空格键开始蓄力
            if not self.is_charging:
                self.is_charging = True
                self.stop_decay()  # 停止衰减
                self.start_charging()
                if self.debug_mode:
                    print("[DEBUG] 空格键按下：开始蓄力")
            event.accept()
        elif key == Qt.Key.Key_W:
            # W键击球
            if self.is_charging:
                self.is_charging = False
                self.take_shot()
                if self.debug_mode:
                    print("[DEBUG] W键按下：击球")
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """键盘释放事件处理"""
        key = event.key()
        
        if key == Qt.Key.Key_Space:
            # 空格键释放，停止蓄力
            if self.is_charging:
                self.is_charging = False
                self.start_decay()  # 开始衰减
                if self.debug_mode:
                    print("[DEBUG] 空格键释放：停止蓄力，开始衰减")
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    def reset_game(self):
        """重置游戏"""
        self.game.reset_game()
        self.power_level = 0
        self.power_slider.setValue(0)
        self.is_charging = False
        
        # 重新创建球图形项
        for item in list(self.ball_items.values()):
            self.scene.removeItem(item)
        self.ball_items.clear()
        
        for ball in self.game.balls:
            ball_item = BilliardBallItem(ball, self.debug_mode)
            self.scene.addItem(ball_item)
            self.ball_items[id(ball)] = ball_item
        
        self.update_game_display()
    
    def _create_system_info_panel(self) -> QWidget:
        """创建右侧系统信息面板"""
        import psutil
        import platform
        
        # 创建右侧面板容器
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background: rgba(40, 40, 50, 220);
                border: 2px solid #555;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(15)
        
        # 系统信息标题
        title_label = QLabel("💻 系统监控面板")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-weight: bold;
                font-size: 18px;
                padding: 10px;
                border-bottom: 2px solid #FFD700;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_label)
        
        # CPU使用率
        self.cpu_label = QLabel("CPU使用率: 正在获取...")
        self.cpu_label.setStyleSheet("""
            QLabel {
                color: #87CEEB;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background: rgba(30, 30, 40, 0.8);
                border-radius: 6px;
            }
        """)
        right_layout.addWidget(self.cpu_label)
        
        # 内存使用率
        self.memory_label = QLabel("内存使用率: 正在获取...")
        self.memory_label.setStyleSheet("""
            QLabel {
                color: #98FB98;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background: rgba(30, 30, 40, 0.8);
                border-radius: 6px;
            }
        """)
        right_layout.addWidget(self.memory_label)
        
        # 存储使用率
        self.disk_label = QLabel("存储使用率: 正在获取...")
        self.disk_label.setStyleSheet("""
            QLabel {
                color: #FFA07A;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background: rgba(30, 30, 40, 0.8);
                border-radius: 6px;
            }
        """)
        right_layout.addWidget(self.disk_label)
        
        # 系统信息
        self.system_label = QLabel("系统信息: 正在获取...")
        self.system_label.setStyleSheet("""
            QLabel {
                color: #DDA0DD;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background: rgba(30, 30, 40, 0.8);
                border-radius: 6px;
            }
        """)
        right_layout.addWidget(self.system_label)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background: #555; height: 2px; margin: 10px 0;")
        right_layout.addWidget(separator)
        
        # 祝贺框
        congrats_label = QLabel("🎉 祝贺框")
        congrats_label.setStyleSheet("""
            QLabel {
                color: #FF6347;
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
                border-bottom: 2px solid #FF6347;
                margin-bottom: 10px;
            }
        """)
        congrats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(congrats_label)
        
        # 祝贺信息
        congrats_text = QLabel("哔哩哔哩：@i杨树林i\n\n成功地猜中了彩蛋！\n\n🎮 恭喜发现隐藏的台球游戏！")
        congrats_text.setStyleSheet("""
            QLabel {
                color: #FFD700;
                font-weight: bold;
                font-size: 14px;
                padding: 15px;
                background: rgba(255, 99, 71, 0.1);
                border: 2px solid #FF6347;
                border-radius: 8px;
                text-align: center;
                line-height: 1.5;
            }
        """)
        congrats_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        congrats_text.setWordWrap(True)
        right_layout.addWidget(congrats_text)
        
        # 添加弹性空间
        right_layout.addStretch()
        
        # 创建系统信息更新定时器
        self.system_info_timer = QTimer()
        self.system_info_timer.timeout.connect(self._update_system_info)
        self.system_info_timer.start(2000)  # 每2秒更新一次
        
        # 立即更新一次系统信息
        self._update_system_info()
        
        return right_widget
    
    def _update_system_info(self):
        """更新系统信息显示"""
        try:
            import psutil
            import platform
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_color = "#87CEEB"
            if cpu_percent > 80:
                cpu_color = "#FF6347"
            elif cpu_percent > 60:
                cpu_color = "#FFA500"
            
            self.cpu_label.setText(f"CPU使用率: {cpu_percent:.1f}%")
            self.cpu_label.setStyleSheet(f"""
                QLabel {{
                    color: {cpu_color};
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px;
                    background: rgba(30, 30, 40, 0.8);
                    border-radius: 6px;
                }}
            """)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_color = "#98FB98"
            if memory_percent > 80:
                memory_color = "#FF6347"
            elif memory_percent > 60:
                memory_color = "#FFA500"
            
            memory_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            self.memory_label.setText(f"内存使用率: {memory_percent:.1f}% ({memory_gb:.1f}GB/{memory_total_gb:.1f}GB)")
            self.memory_label.setStyleSheet(f"""
                QLabel {{
                    color: {memory_color};
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px;
                    background: rgba(30, 30, 40, 0.8);
                    border-radius: 6px;
                }}
            """)
            
            # 存储使用率 - 检测所有磁盘
            try:
                disk_parts = psutil.disk_partitions(all=False)
                disk_info_list = []
                
                for part in disk_parts:
                    try:
                        if platform.system() == 'Windows':
                            # Windows: 只显示本地磁盘
                            if 'cdrom' in part.opts or part.fstype == '':
                                continue
                        elif platform.system() == 'Linux':
                            # Linux: 跳过特殊文件系统
                            if part.mountpoint.startswith('/snap') or part.mountpoint.startswith('/boot'):
                                continue
                        
                        usage = psutil.disk_usage(part.mountpoint)
                        if usage.total > 0:  # 只显示有容量的磁盘
                            percent = usage.percent
                            used_gb = usage.used / (1024**3)
                            total_gb = usage.total / (1024**3)
                            
                            # 根据挂载点或设备名显示
                            if platform.system() == 'Windows':
                                # Windows: 使用设备名，如 'C:\\' 或 'D:\\'
                                disk_name = part.device.rstrip('\\')
                            else:
                                disk_name = part.mountpoint
                            
                            disk_info_list.append(f"{disk_name}: {percent:.1f}% ({used_gb:.1f}GB/{total_gb:.1f}GB)")
                            
                    except Exception:
                        continue
                
                if disk_info_list:
                    disk_text = "存储使用率:\n" + "\n".join(disk_info_list[:3])  # 最多显示3个磁盘
                    if len(disk_info_list) > 3:
                        disk_text += f"\n...等{len(disk_info_list)}个磁盘"
                    
                    # 计算平均使用率用于颜色
                    try:
                        percentages = []
                        for info in disk_info_list:
                            # 安全地提取百分比
                            parts = info.split(':')
                            if len(parts) > 1:
                                percent_part = parts[1].split('%')[0].strip()
                                try:
                                    percent = float(percent_part)
                                    percentages.append(percent)
                                except ValueError:
                                    continue
                        
                        if percentages:
                            avg_percent = sum(percentages) / len(percentages)
                            disk_color = "#FFA07A"
                            if avg_percent > 90:
                                disk_color = "#FF6347"
                            elif avg_percent > 80:
                                disk_color = "#FFA500"
                        else:
                            disk_color = "#FFA07A"  # 默认颜色
                    except Exception:
                        disk_color = "#FFA07A"  # 出错时使用默认颜色
                    
                    self.disk_label.setText(disk_text)
                    self.disk_label.setStyleSheet(f"""
                        QLabel {{
                            color: {disk_color};
                            font-weight: bold;
                            font-size: 12px;
                            padding: 8px;
                            background: rgba(30, 30, 40, 0.8);
                            border-radius: 6px;
                        }}
                    """)
                else:
                    self.disk_label.setText("存储使用率: 未检测到磁盘")
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 存储检测失败: {e}")
                self.disk_label.setText("存储使用率: 检测失败")
            
            # 系统信息 - 添加CPU详细信息
            try:
                # 获取CPU频率
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    cpu_freq_text = f"{cpu_freq.current:.1f}MHz"
                    if cpu_freq.max:
                        cpu_freq_text += f" (最大: {cpu_freq.max:.1f}MHz)"
                else:
                    cpu_freq_text = "未知"
                
                # 获取CPU核心数
                cpu_count = psutil.cpu_count(logical=True)
                cpu_cores = psutil.cpu_count(logical=False)
                
                # 获取CPU品牌
                import subprocess
                cpu_brand = platform.processor()
                if platform.system() == 'Windows':
                    try:
                        # Windows: 使用wmic获取更准确的CPU信息
                        result = subprocess.run(['wmic', 'cpu', 'get', 'name'], 
                                              capture_output=True, text=True, encoding='utf-8', 
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                        if result.returncode == 0:
                            # 改进的解析逻辑：过滤空行和标题行
                            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                            # 查找包含CPU名称的行（跳过标题行）
                            for line in lines:
                                if line and not line.startswith('Name') and 'CPU' in line:
                                    cpu_brand = line
                                    break
                            # 如果没找到，尝试其他方法
                            if cpu_brand == platform.processor():
                                # 尝试使用caption参数
                                result2 = subprocess.run(['wmic', 'cpu', 'get', 'caption'], 
                                                       capture_output=True, text=True, encoding='utf-8',
                                                       creationflags=subprocess.CREATE_NO_WINDOW)
                                if result2.returncode == 0:
                                    lines2 = [line.strip() for line in result2.stdout.strip().split('\n') if line.strip()]
                                    for line in lines2:
                                        if line and not line.startswith('Caption'):
                                            cpu_brand = line
                                            break
                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] wmic获取CPU名称失败: {e}")
                elif platform.system() == 'Linux':
                    try:
                        # Linux: 从/proc/cpuinfo获取
                        with open('/proc/cpuinfo', 'r') as f:
                            for line in f:
                                if 'model name' in line:
                                    cpu_brand = line.split(':')[1].strip()
                                    break
                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] Linux获取CPU名称失败: {e}")
                
                system_info = f"""
                系统: {platform.system()} {platform.release()}
                CPU: {cpu_brand}
                核心: {cpu_cores}物理/{cpu_count}逻辑
                频率: {cpu_freq_text}
                Python版本: {platform.python_version()}
                """
                self.system_label.setText(f"系统信息: {system_info.strip()}")
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] CPU信息获取失败: {e}")
                # 回退到基本信息
                system_info = f"""
                系统: {platform.system()} {platform.release()}
                处理器: {platform.processor()}
                Python版本: {platform.python_version()}
                平台: {platform.platform()}
                """
                self.system_label.setText(f"系统信息: {system_info.strip()}")
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 获取系统信息失败: {e}")
            self.cpu_label.setText("CPU使用率: 获取失败")
            self.memory_label.setText("内存使用率: 获取失败")
            self.disk_label.setText("存储使用率: 获取失败")
            self.system_label.setText(f"系统信息: 获取失败 ({str(e)})")
    
    def closeEvent(self, event):
        """关闭窗口事件处理 - 停止所有定时器"""
        if self.debug_mode:
            print("[DEBUG] 游戏窗口关闭，停止所有定时器...")
        
        # 停止游戏定时器
        if hasattr(self, 'game_timer'):
            try:
                if self.game_timer.isActive():
                    self.game_timer.stop()
                    if self.debug_mode:
                        print("[DEBUG] 游戏定时器已停止")
            except AttributeError:
                # 如果定时器没有isActive方法，直接停止
                self.game_timer.stop()
                if self.debug_mode:
                    print("[DEBUG] 游戏定时器已停止（无isActive方法）")
        
        # 停止力气值衰减定时器
        if hasattr(self, 'decay_timer'):
            try:
                if self.decay_timer.isActive():
                    self.decay_timer.stop()
                    if self.debug_mode:
                        print("[DEBUG] 力气值衰减定时器已停止")
            except AttributeError:
                self.decay_timer.stop()
                if self.debug_mode:
                    print("[DEBUG] 力气值衰减定时器已停止（无isActive方法）")
        
        # 停止系统信息定时器
        if hasattr(self, 'system_info_timer'):
            try:
                if self.system_info_timer.isActive():
                    self.system_info_timer.stop()
                    if self.debug_mode:
                        print("[DEBUG] 系统信息定时器已停止")
            except AttributeError:
                self.system_info_timer.stop()
                if self.debug_mode:
                    print("[DEBUG] 系统信息定时器已停止（无isActive方法）")
        
        # 停止所有球动画定时器
        if hasattr(self, 'ball_items'):
            for ball_item in self.ball_items.values():
                if hasattr(ball_item, 'animation_timer') and ball_item.animation_timer:
                    try:
                        if ball_item.animation_timer.isActive():
                            ball_item.animation_timer.stop()
                    except AttributeError:
                        ball_item.animation_timer.stop()
        
        # 清理所有定时器引用
        if hasattr(self, 'game_timer'):
            self.game_timer = None
        if hasattr(self, 'decay_timer'):
            self.decay_timer = None
        if hasattr(self, 'system_info_timer'):
            self.system_info_timer = None
        
        if self.debug_mode:
            print("[DEBUG] 所有定时器已停止，关闭窗口")
        
        # 调用父类的关闭事件
        super().closeEvent(event)