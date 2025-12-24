"""
游戏模块包 - ColorBridge
包含各种娱乐游戏，如2D模仿3D台球等
"""

__version__ = "2.1.17"
__author__ = "ColorBridge开发团队"
__description__ = "ColorBridge游戏模块包 - 包含2D模仿3D台球游戏，已修复模块加载问题"

# 导出游戏模块
try:
    from .billiard_3d import *
except ImportError as e:
    print(f"[WARNING] 游戏模块导入失败: {e}")

__all__ = ["billiard_3d"]