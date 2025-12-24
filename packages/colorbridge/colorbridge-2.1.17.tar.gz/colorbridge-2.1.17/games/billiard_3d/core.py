"""
台球游戏核心逻辑模块
实现2D模仿3D的台球物理引擎
"""

import math
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BallType(Enum):
    """台球类型"""
    CUE = "cue"      # 母球
    SOLID = "solid"  # 实心球
    STRIPE = "stripe"  # 条纹球
    BLACK = "black"  # 黑8


@dataclass
class Ball:
    """台球类"""
    x: float
    y: float
    radius: float
    ball_type: BallType
    number: int = 0
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 1.0
    friction: float = 0.98
    is_pocketed: bool = False
    
    def update(self, dt: float):
        """更新球的位置"""
        if self.is_pocketed:
            return
            
        # 应用速度
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # 应用摩擦力
        self.vx *= self.friction
        self.vy *= self.friction
        
        # 速度过小时停止
        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0
    
    def apply_force(self, fx: float, fy: float):
        """应用力"""
        self.vx += fx / self.mass
        self.vy += fy / self.mass
    
    def distance_to(self, other: 'Ball') -> float:
        """计算到另一个球的距离"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def collides_with(self, other: 'Ball') -> bool:
        """检测是否与另一个球碰撞"""
        if self.is_pocketed or other.is_pocketed:
            return False
        return self.distance_to(other) < (self.radius + other.radius)
    
    def resolve_collision(self, other: 'Ball'):
        """解析球与球的碰撞"""
        if not self.collides_with(other):
            return
            
        # 计算碰撞法向量
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
            
        nx = dx / distance
        ny = dy / distance
        
        # 计算相对速度
        dvx = other.vx - self.vx
        dvy = other.vy - self.vy
        
        # 计算相对速度在法向量上的投影
        dvn = dvx * nx + dvy * ny
        
        # 如果球正在分离，不处理碰撞
        if dvn > 0:
            return
            
        # 计算冲量
        impulse = 2 * dvn / (self.mass + other.mass)
        
        # 应用冲量
        self.vx += impulse * other.mass * nx
        self.vy += impulse * other.mass * ny
        other.vx -= impulse * self.mass * nx
        other.vy -= impulse * self.mass * ny
        
        # 防止球重叠
        overlap = (self.radius + other.radius) - distance
        if overlap > 0:
            self.x -= overlap * nx * 0.5
            self.y -= overlap * ny * 0.5
            other.x += overlap * nx * 0.5
            other.y += overlap * ny * 0.5


class Table:
    """台球桌类"""
    def __init__(self, width: float = 800, height: float = 400):
        self.width = width
        self.height = height
        self.cushion_width = 20
        self.pocket_radius = 25
        
        # 定义球袋位置
        self.pockets = [
            (self.cushion_width, self.cushion_width),  # 左上
            (self.width // 2, self.cushion_width),     # 上中
            (self.width - self.cushion_width, self.cushion_width),  # 右上
            (self.cushion_width, self.height - self.cushion_width),  # 左下
            (self.width // 2, self.height - self.cushion_width),    # 下中
            (self.width - self.cushion_width, self.height - self.cushion_width)  # 右下
        ]
    
    def check_pocket(self, ball: Ball) -> bool:
        """检查球是否进袋"""
        if ball.is_pocketed:
            return True
            
        for px, py in self.pockets:
            distance = math.sqrt((ball.x - px)**2 + (ball.y - py)**2)
            if distance < self.pocket_radius:
                ball.is_pocketed = True
                ball.vx = 0
                ball.vy = 0
                # 将球移动到屏幕外，避免卡在洞口
                ball.x = -100
                ball.y = -100
                return True
        return False
    
    def check_wall_collision(self, ball: Ball):
        """检查球与桌边的碰撞"""
        if ball.is_pocketed:
            return
            
        # 左墙
        if ball.x - ball.radius < self.cushion_width:
            ball.x = self.cushion_width + ball.radius
            ball.vx = -ball.vx * 0.9
            
        # 右墙
        if ball.x + ball.radius > self.width - self.cushion_width:
            ball.x = self.width - self.cushion_width - ball.radius
            ball.vx = -ball.vx * 0.9
            
        # 上墙
        if ball.y - ball.radius < self.cushion_width:
            ball.y = self.cushion_width + ball.radius
            ball.vy = -ball.vy * 0.9
            
        # 下墙
        if ball.y + ball.radius > self.height - self.cushion_width:
            ball.y = self.height - self.cushion_width - ball.radius
            ball.vy = -ball.vy * 0.9


class BilliardGame:
    """台球游戏主类"""
    def __init__(self):
        self.table = Table()
        self.balls: List[Ball] = []
        self.cue_ball: Optional[Ball] = None
        self.game_state = "setup"  # setup, aiming, shooting, moving, game_over
        self.shot_power = 0.0
        self.max_power = 300.0  # 最大力气值提高到300%
        self.player_score = 0  # 单人游戏，只有一个分数
        self.game_type = "8ball"  # 8球规则
        self.new_pocketed_balls: List[Ball] = []  # 本次回合新进袋的球
        
        self.setup_game()
    
    def setup_game(self):
        """设置游戏初始状态"""
        self.balls.clear()
        
        # 创建母球
        self.cue_ball = Ball(
            x=self.table.width * 0.25,
            y=self.table.height // 2,
            radius=12,
            ball_type=BallType.CUE,
            number=0
        )
        self.balls.append(self.cue_ball)
        
        # 创建目标球（三角形排列）
        ball_radius = 11
        positions = self._create_triangle_formation(
            self.table.width * 0.75,
            self.table.height // 2,
            ball_radius
        )
        
        # 分配球类型
        ball_numbers = list(range(1, 16))
        random.shuffle(ball_numbers)
        
        for i, (x, y) in enumerate(positions):
            if i == 4:  # 顶点球
                ball_type = BallType.BLACK
                number = 8
            elif i % 2 == 0:
                ball_type = BallType.SOLID
                number = ball_numbers.pop()
            else:
                ball_type = BallType.STRIPE
                number = ball_numbers.pop()
                
            ball = Ball(
                x=x, y=y,
                radius=ball_radius,
                ball_type=ball_type,
                number=number
            )
            self.balls.append(ball)
        
        self.game_state = "aiming"
        self.shot_power = 0.0
    
    def _create_triangle_formation(self, center_x: float, center_y: float, radius: float) -> List[Tuple[float, float]]:
        """创建三角形排列"""
        positions = []
        row_count = 5
        
        for row in range(row_count):
            balls_in_row = row + 1
            start_x = center_x - (balls_in_row - 1) * radius * 2 * 0.866  # 水平间距
            for col in range(balls_in_row):
                x = start_x + col * radius * 2 * 0.866 * 2
                y = center_y - (row_count - row - 1) * radius * 2
                positions.append((x, y))
        
        return positions
    
    def update(self, dt: float):
        """更新游戏状态"""
        if self.game_state != "moving":
            return
            
        # 更新所有球
        for ball in self.balls:
            # 保存进袋状态
            was_pocketed = ball.is_pocketed
            
            ball.update(dt)
            
            # 检查球袋
            if self.table.check_pocket(ball):
                # 如果是新进袋的球，添加到列表
                if not was_pocketed:
                    self.new_pocketed_balls.append(ball)
            
            # 检查墙壁碰撞
            self.table.check_wall_collision(ball)
        
        # 检查球与球之间的碰撞
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                if self.balls[i].collides_with(self.balls[j]):
                    self.balls[i].resolve_collision(self.balls[j])
        
        # 检查是否所有球都停止
        if self._all_balls_stopped():
            self._end_turn()
    
    def _all_balls_stopped(self) -> bool:
        """检查是否所有球都停止运动"""
        for ball in self.balls:
            if not ball.is_pocketed and (abs(ball.vx) > 0.1 or abs(ball.vy) > 0.1):
                return False
        return True
    
    def aim_shot(self, angle: float):
        """瞄准击球"""
        if self.game_state != "aiming" or self.cue_ball.is_pocketed:
            return
            
        self.shot_angle = angle
    
    def charge_power(self, power: float):
        """蓄力"""
        if self.game_state != "aiming":
            return
            
        self.shot_power = min(power, self.max_power)
    
    def take_shot(self):
        """击球"""
        if self.game_state != "aiming" or self.cue_ball.is_pocketed:
            return
            
        # 计算击球力（增加力量乘数，让球飞得更远）
        power_multiplier = 10.0  # 增加10倍力量
        force_x = math.cos(self.shot_angle) * self.shot_power * power_multiplier
        force_y = math.sin(self.shot_angle) * self.shot_power * power_multiplier
        
        # 应用力到母球
        self.cue_ball.apply_force(force_x, force_y)
        
        # 更新游戏状态
        self.game_state = "moving"
        self.shot_power = 0.0
        # 重置新进袋球列表
        self.new_pocketed_balls.clear()
    
    def _end_turn(self):
        """结束当前回合"""
        # 使用本次回合新进袋的球
        pocketed_balls = self.new_pocketed_balls
        
        # 更新分数（单人游戏，所有进袋球都加分）
        for ball in pocketed_balls:
            if ball.ball_type != BallType.CUE:  # 母球进袋不加分
                self.player_score += 1
        
        # 检查黑8是否进袋
        for ball in pocketed_balls:
            if ball.ball_type == BallType.BLACK:
                # 黑8进袋，游戏结束
                self._end_game()
                return
        
        # 单人游戏，不切换玩家，直接回到瞄准状态
        self.game_state = "aiming"
        
        # 如果母球进袋，重置位置
        if self.cue_ball.is_pocketed:
            # 调试信息：母球重置
            print(f"[DEBUG] 母球进袋，重置位置到 ({self.table.width * 0.25:.1f}, {self.table.height // 2:.1f})")
            self.cue_ball.is_pocketed = False
            self.cue_ball.x = self.table.width * 0.25
            self.cue_ball.y = self.table.height // 2
            self.cue_ball.vx = 0
            self.cue_ball.vy = 0
    
    def _check_black_8_valid(self) -> bool:
        """检查黑8是否合法进袋（单人游戏简化版）"""
        # 单人游戏：只要黑8进袋就有效
        return True
    
    def _end_game(self):
        """结束游戏"""
        self.game_state = "game_over"
        self.winner = f"玩家 (得分: {self.player_score})"
    
    def reset_game(self):
        """重置游戏"""
        self.setup_game()
        self.player_score = 0
        self.game_state = "aiming"
        self.new_pocketed_balls.clear()