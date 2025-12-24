#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题管理器 - ColorBridge
统一管理UI主题、颜色和样式
"""

import json
import os
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFont

class ThemeManager(QObject):
    """主题管理器"""
    
    # 信号定义
    theme_changed = pyqtSignal(str)  # 主题改变信号
    color_changed = pyqtSignal(str, QColor)  # 颜色改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 内置主题
        self.builtin_themes = {
            'dopamine': self.create_dopamine_theme(),
            'dark': self.create_dark_theme(),
            'light': self.create_light_theme(),
            'professional': self.create_professional_theme()
        }
        
        # 当前主题
        self.current_theme_name = 'dopamine'
        self.current_theme = self.builtin_themes['dopamine']
        
        # 自定义主题
        self.custom_themes = {}
        
        # 主题文件路径
        self.themes_dir = os.path.join(os.path.dirname(__file__), '..', 'themes')
        self.ensure_themes_directory()
        
        # 加载保存的主题
        self.load_custom_themes()
        
    def ensure_themes_directory(self):
        """确保主题目录存在"""
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)
            
    def create_dopamine_theme(self) -> Dict[str, Any]:
        """创建多巴胺主题"""
        return {
            'name': 'dopamine',
            'display_name': '多巴胺',
            'description': '充满活力的半透明多巴胺配色方案',
            'colors': {
                'primary': QColor(100, 200, 255),
                'secondary': QColor(255, 150, 200),
                'accent': QColor(150, 255, 150),
                'background': QColor(45, 45, 55),
                'surface': QColor(60, 60, 70),
                'text': QColor(220, 220, 230),
                'text_secondary': QColor(180, 180, 190),
                'error': QColor(255, 100, 100),
                'warning': QColor(255, 200, 100),
                'success': QColor(100, 255, 100),
                'info': QColor(150, 200, 255)
            },
            'opacity': {
                'window': 0.85,
                'panel': 0.9,
                'widget': 0.95
            },
            'fonts': {
                'default_family': 'Microsoft YaHei',
                'default_size': 12,
                'mono_family': 'Consolas',
                'mono_size': 9,
                'title_size': 14,
                'label_size': 10,
                'button_size': 11,
                'small_size': 9
            },
            'spacing': {
                'small': 6,
                'medium': 12,
                'large': 18
            },
            'border_radius': {
                'small': 4,
                'medium': 6,
                'large': 8
            }
        }
        
    def create_dark_theme(self) -> Dict[str, Any]:
        """创建深色主题"""
        return {
            'name': 'dark',
            'display_name': '深色',
            'description': '经典的深色主题，适合长时间使用',
            'colors': {
                'primary': QColor(66, 165, 245),
                'secondary': QColor(121, 85, 72),
                'accent': QColor(102, 187, 106),
                'background': QColor(33, 33, 33),
                'surface': QColor(66, 66, 66),
                'text': QColor(255, 255, 255),
                'text_secondary': QColor(189, 189, 189),
                'error': QColor(244, 67, 54),
                'warning': QColor(255, 160, 0),
                'success': QColor(76, 175, 80),
                'info': QColor(33, 150, 243)
            },
            'opacity': {
                'window': 0.95,
                'panel': 1.0,
                'widget': 1.0
            },
            'fonts': {
                'default_family': 'Microsoft YaHei',
                'default_size': 12,
                'mono_family': 'Consolas',
                'mono_size': 9,
                'title_size': 14,
                'label_size': 10,
                'button_size': 11,
                'small_size': 9
            },
            'spacing': {
                'small': 6,
                'medium': 12,
                'large': 18
            },
            'border_radius': {
                'small': 3,
                'medium': 5,
                'large': 7
            }
        }
        
    def create_light_theme(self) -> Dict[str, Any]:
        """创建浅色主题"""
        return {
            'name': 'light',
            'display_name': '浅色',
            'description': '清新的浅色主题，适合白天使用',
            'colors': {
                'primary': QColor(25, 118, 210),
                'secondary': QColor(141, 110, 99),
                'accent': QColor(56, 142, 60),
                'background': QColor(250, 250, 250),
                'surface': QColor(255, 255, 255),
                'text': QColor(33, 33, 33),
                'text_secondary': QColor(117, 117, 117),
                'error': QColor(211, 47, 47),
                'warning': QColor(245, 124, 0),
                'success': QColor(46, 125, 50),
                'info': QColor(2, 136, 209)
            },
            'opacity': {
                'window': 1.0,
                'panel': 1.0,
                'widget': 1.0
            },
            'fonts': {
                'default_family': 'Microsoft YaHei',
                'default_size': 12,
                'mono_family': 'Consolas',
                'mono_size': 9,
                'title_size': 14,
                'label_size': 10,
                'button_size': 11,
                'small_size': 9
            },
            'spacing': {
                'small': 6,
                'medium': 12,
                'large': 18
            },
            'border_radius': {
                'small': 3,
                'medium': 5,
                'large': 7
            }
        }
        
    def create_professional_theme(self) -> Dict[str, Any]:
        """创建专业主题"""
        return {
            'name': 'professional',
            'display_name': '专业',
            'description': '专业的商务主题，适合正式场合',
            'colors': {
                'primary': QColor(30, 136, 229),
                'secondary': QColor(156, 39, 176),
                'accent': QColor(0, 150, 136),
                'background': QColor(248, 249, 250),
                'surface': QColor(255, 255, 255),
                'text': QColor(33, 37, 41),
                'text_secondary': QColor(108, 117, 125),
                'error': QColor(220, 53, 69),
                'warning': QColor(255, 193, 7),
                'success': QColor(40, 167, 69),
                'info': QColor(23, 162, 184)
            },
            'opacity': {
                'window': 0.98,
                'panel': 1.0,
                'widget': 1.0
            },
            'fonts': {
                'default_family': 'Microsoft YaHei',
                'default_size': 12,
                'mono_family': 'Consolas',
                'mono_size': 9,
                'title_size': 14,
                'label_size': 10,
                'button_size': 11,
                'small_size': 9
            },
            'spacing': {
                'small': 6,
                'medium': 12,
                'large': 18
            },
            'border_radius': {
                'small': 2,
                'medium': 4,
                'large': 6
            }
        }
        
    def get_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """获取指定主题"""
        if theme_name in self.builtin_themes:
            return self.builtin_themes[theme_name]
        elif theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        return None
        
    def apply_theme(self, theme_name: str, target_widget: QWidget) -> bool:
        """应用主题到指定组件"""
        theme = self.get_theme(theme_name)
        if not theme:
            return False
            
        self.current_theme_name = theme_name
        self.current_theme = theme
        
        # 应用主题到组件
        self._apply_theme_to_widget(theme, target_widget)
        
        # 发出主题改变信号
        self.theme_changed.emit(theme_name)
        
        return True
        
    def _apply_theme_to_widget(self, theme: Dict[str, Any], widget: QWidget):
        """将主题应用到组件"""
        # 创建调色板
        palette = widget.palette()
        
        # 设置颜色
        colors = theme['colors']
        palette.setColor(QPalette.ColorRole.Window, colors['background'])
        palette.setColor(QPalette.ColorRole.WindowText, colors['text'])
        palette.setColor(QPalette.ColorRole.Base, colors['surface'])
        palette.setColor(QPalette.ColorRole.Text, colors['text'])
        palette.setColor(QPalette.ColorRole.Button, colors['surface'])
        palette.setColor(QPalette.ColorRole.ButtonText, colors['text'])
        palette.setColor(QPalette.ColorRole.Highlight, colors['primary'])
        palette.setColor(QPalette.ColorRole.HighlightedText, colors['text'])
        
        widget.setPalette(palette)
        
        # 生成样式表
        stylesheet = self._generate_stylesheet(theme)
        widget.setStyleSheet(stylesheet)
        
    def _generate_stylesheet(self, theme: Dict[str, Any]) -> str:
        """生成样式表"""
        colors = theme['colors']
        opacity = theme['opacity']
        spacing = theme['spacing']
        border_radius = theme['border_radius']
        
        stylesheet = f"""
        QMainWindow {{
            background-color: {self._rgba_to_css(colors['background'], opacity['window'])};
        }}
        
        QFrame {{
            background-color: {self._rgba_to_css(colors['surface'], opacity['panel'])};
            border-radius: {border_radius['medium']}px;
            border: 1px solid {self._rgba_to_css(colors['primary'], 0.3)};
        }}
        
        QPushButton {{
            background-color: {self._rgba_to_css(colors['primary'], opacity['widget'])};
            color: {self._color_to_css(colors['text'])};
            border: none;
            border-radius: {border_radius['medium']}px;
            padding: {spacing['small']}px {spacing['medium']}px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {self._rgba_to_css(colors['primary'], 1.0)};
        }}
        
        QPushButton:pressed {{
            background-color: {self._rgba_to_css(colors['secondary'], opacity['widget'])};
        }}
        
        QLineEdit, QTextEdit {{
            background-color: {self._rgba_to_css(colors['surface'], opacity['widget'])};
            border: 2px solid {self._rgba_to_css(colors['primary'], 0.5)};
            border-radius: {border_radius['medium']}px;
            padding: {spacing['small']}px;
            color: {self._color_to_css(colors['text'])};
        }}
        
        QComboBox {{
            background-color: {self._rgba_to_css(colors['surface'], opacity['widget'])};
            border: 2px solid {self._rgba_to_css(colors['primary'], 0.5)};
            border-radius: {border_radius['medium']}px;
            padding: {spacing['small']}px;
            color: {self._color_to_css(colors['text'])};
        }}
        
        QLabel {{
            color: {self._color_to_css(colors['text'])};
            font-weight: bold;
        }}
        
        QScrollBar:vertical {{
            background-color: {self._rgba_to_css(colors['surface'], 0.5)};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self._rgba_to_css(colors['primary'], 0.7)};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self._rgba_to_css(colors['primary'], 1.0)};
        }}
        """
        
        return stylesheet
        
    def _color_to_css(self, color: QColor) -> str:
        """将QColor转换为CSS颜色字符串"""
        return f"rgb({color.red()}, {color.green()}, {color.blue()})"
        
    def _rgba_to_css(self, color: QColor, alpha: float) -> str:
        """将QColor和透明度转换为CSS RGBA字符串"""
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"
        
    def get_color(self, color_name: str) -> QColor:
        """获取主题中的指定颜色"""
        return self.current_theme['colors'].get(color_name, QColor(128, 128, 128))
        
    def set_color(self, color_name: str, color: QColor):
        """设置主题中的指定颜色"""
        if color_name in self.current_theme['colors']:
            self.current_theme['colors'][color_name] = color
            self.color_changed.emit(color_name, color)
            
    def get_font(self, font_type: str = 'default', scale_factor: float = 1.0) -> QFont:
        """获取指定类型的字体，支持缩放"""
        fonts = self.current_theme['fonts']
        
        font_mapping = {
            'default': (fonts['default_family'], fonts['default_size']),
            'mono': (fonts['mono_family'], fonts['mono_size']),
            'title': (fonts['default_family'], fonts['title_size']),
            'label': (fonts['default_family'], fonts['label_size']),
            'button': (fonts['default_family'], fonts['button_size']),
            'small': (fonts['default_family'], fonts['small_size'])
        }
        
        family, size = font_mapping.get(font_type, font_mapping['default'])
        scaled_size = int(size * scale_factor)
        
        font = QFont(family, scaled_size)
        if font_type == 'title':
            font.setBold(True)
        elif font_type in ['label', 'button']:
            font.setWeight(QFont.Weight.Bold)
            
        return font
        
    def set_font_scale(self, scale_factor: float):
        """设置全局字体缩放因子"""
        if not hasattr(self, 'font_scale_factor'):
            self.font_scale_factor = 1.0
        self.font_scale_factor = max(0.5, min(2.0, scale_factor))  # 限制在0.5-2.0之间
        
    def get_font_scale(self) -> float:
        """获取当前字体缩放因子"""
        return getattr(self, 'font_scale_factor', 1.0)
            
    def create_custom_theme(self, theme_name: str, base_theme: str = 'dopamine') -> bool:
        """创建自定义主题"""
        base = self.get_theme(base_theme)
        if not base:
            return False
            
        # 复制基础主题
        import copy
        custom_theme = copy.deepcopy(base)
        custom_theme['name'] = theme_name
        custom_theme['display_name'] = theme_name
        custom_theme['description'] = f'基于{base["display_name"]}的自定义主题'
        
        self.custom_themes[theme_name] = custom_theme
        self.save_custom_themes()
        
        return True
        
    def save_custom_themes(self):
        """保存自定义主题"""
        try:
            themes_file = os.path.join(self.themes_dir, 'custom_themes.json')
            with open(themes_file, 'w', encoding='utf-8') as f:
                # 转换QColor为可序列化的格式
                serializable_themes = {}
                for name, theme in self.custom_themes.items():
                    serializable_themes[name] = self._serialize_theme(theme)
                    
                json.dump(serializable_themes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存自定义主题失败: {e}")
            
    def load_custom_themes(self):
        """加载自定义主题"""
        try:
            themes_file = os.path.join(self.themes_dir, 'custom_themes.json')
            if os.path.exists(themes_file):
                with open(themes_file, 'r', encoding='utf-8') as f:
                    serializable_themes = json.load(f)
                    
                for name, theme_data in serializable_themes.items():
                    self.custom_themes[name] = self._deserialize_theme(theme_data)
        except Exception as e:
            print(f"加载自定义主题失败: {e}")
            
    def _serialize_theme(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        """序列化主题（转换QColor为字典）"""
        serializable = theme.copy()
        
        # 转换颜色字典
        if 'colors' in serializable:
            colors = {}
            for name, color in serializable['colors'].items():
                if isinstance(color, QColor):
                    colors[name] = {
                        'red': color.red(),
                        'green': color.green(),
                        'blue': color.blue(),
                        'alpha': color.alpha()
                    }
                else:
                    colors[name] = color
            serializable['colors'] = colors
            
        return serializable
        
    def _deserialize_theme(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """反序列化主题（转换字典为QColor）"""
        theme = theme_data.copy()
        
        # 转换颜色字典
        if 'colors' in theme:
            colors = {}
            for name, color_data in theme['colors'].items():
                if isinstance(color_data, dict):
                    colors[name] = QColor(
                        color_data['red'],
                        color_data['green'],
                        color_data['blue'],
                        color_data.get('alpha', 255)
                    )
                else:
                    colors[name] = color_data
            theme['colors'] = colors
            
        return theme
        
    def get_available_themes(self) -> Dict[str, str]:
        """获取所有可用主题"""
        themes = {}
        
        # 添加内置主题
        for name, theme in self.builtin_themes.items():
            themes[name] = theme['display_name']
            
        # 添加自定义主题
        for name, theme in self.custom_themes.items():
            themes[name] = theme['display_name']
            
        return themes
        
    def get_current_theme_name(self) -> str:
        """获取当前主题名称"""
        return self.current_theme_name
        
    def export_theme(self, theme_name: str, file_path: str) -> bool:
        """导出主题到文件"""
        theme = self.get_theme(theme_name)
        if not theme:
            return False
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_theme(theme), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出主题失败: {e}")
            return False
            
    def import_theme(self, file_path: str, theme_name: str) -> bool:
        """从文件导入主题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
                
            theme = self._deserialize_theme(theme_data)
            theme['name'] = theme_name
            theme['display_name'] = theme_name
            
            self.custom_themes[theme_name] = theme
            self.save_custom_themes()
            
            return True
        except Exception as e:
            print(f"导入主题失败: {e}")
            return False