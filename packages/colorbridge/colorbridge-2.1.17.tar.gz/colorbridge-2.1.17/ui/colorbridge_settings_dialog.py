#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框模块 - ColorBridge
处理应用程序设置和配置
"""

import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QLineEdit, QPushButton, QSlider, 
                            QCheckBox, QGroupBox, QFileDialog, QSpinBox,
                            QTabWidget, QTextEdit, QComboBox, QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

class SettingsDialog(QDialog):
    """设置对话框类"""
    
    # 信号定义
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ColorBridge 设置")
        self.setGeometry(200, 200, 500, 600)
        self.setModal(True)
        
        # 设置文件路径
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'colorbridge_settings.json')
        
        # 从父窗口获取当前设置，如果没有则使用默认值
        if parent and hasattr(parent, 'global_text_color'):
            self.settings = {
                'opacity': int(parent.windowOpacity() * 100) if parent.windowOpacity() > 0 else 90,
                'wallpaper': getattr(parent, 'current_wallpaper_path', ''),
                'timestamp': getattr(parent, 'show_timestamp', True),
                'font_size': 12,
                'mono_font_size': 11,
                'ui_scale': 100,
                'theme': 'dopamine',
                'auto_connect': False,
                'default_port': '',
                'default_baud': '115200',
                'global_text_color': f"rgb({parent.global_text_color.red()}, "
                     f"{parent.global_text_color.green()}, "
                     f"{parent.global_text_color.blue()})",
                'ai8051u_detection_enabled': getattr(parent, 'ai8051u_detection_enabled', True),
                'use_global_text_color': getattr(parent, 'use_global_text_color', False),
                'terminal_log_enabled': getattr(parent, 'terminal_log_enabled', False),
            }
        else:
            # 默认设置
            self.settings = {
                'opacity': 90,
                'wallpaper': '',
                'timestamp': True,
                'font_size': 12,
                'mono_font_size': 11,
                'ui_scale': 100,
                'theme': 'dopamine',
                'auto_connect': False,
                'default_port': '',
                'default_baud': '115200',
                'global_text_color': 'rgb(200, 200, 200)',
                'ai8051u_detection_enabled': True,
                'use_global_text_color': False,
                'terminal_log_enabled': False,
            }
        
        self.init_ui()
        
        # 加载设置（覆盖从父窗口获取的默认值）
        self.load_settings()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 界面设置选项卡
        self.create_ui_tab(tab_widget)
        
        # 显示设置选项卡
        self.create_display_tab(tab_widget)
        
        # 串口设置选项卡
        self.create_serial_tab(tab_widget)
        
        # 设备信息选项卡
        self.create_device_info_tab(tab_widget)
        
        # 帮助中心选项卡
        self.create_help_tab(tab_widget)
        
        # 对话框按钮
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置默认")
        self.apply_btn = QPushButton("应用")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn = QPushButton("确定")
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.setup_connections()
        
    def create_ui_tab(self, parent):
        """创建界面设置选项卡"""
        ui_widget = QWidget()
        ui_layout = QVBoxLayout(ui_widget)
        
        # 透明度设置
        opacity_group = QGroupBox("透明度设置")
        opacity_layout = QVBoxLayout(opacity_group)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(self.settings['opacity'])
        self.opacity_label = QLabel(f"透明度: {self.settings['opacity']}%")
        
        opacity_layout.addWidget(self.opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        ui_layout.addWidget(opacity_group)
        
        # 壁纸设置
        wallpaper_group = QGroupBox("壁纸设置")
        wallpaper_layout = QVBoxLayout(wallpaper_group)
        
        # 壁纸路径输入
        self.wallpaper_path = QLineEdit()
        self.wallpaper_path.setText(self.settings['wallpaper'])
        self.wallpaper_path.setPlaceholderText("选择壁纸文件路径...")
        
        # 壁纸按钮
        wallpaper_btn_layout = QHBoxLayout()
        self.browse_btn = QPushButton("浏览...")
        self.clear_wallpaper_btn = QPushButton("清除")
        wallpaper_btn_layout.addWidget(self.browse_btn)
        wallpaper_btn_layout.addWidget(self.clear_wallpaper_btn)
        
        
        
        wallpaper_layout.addWidget(QLabel("壁纸路径:"))
        wallpaper_layout.addWidget(self.wallpaper_path)
        wallpaper_layout.addLayout(wallpaper_btn_layout)
        ui_layout.addWidget(wallpaper_group)
        
        # 显示设置
        display_group = QGroupBox("显示设置")
        display_layout = QVBoxLayout(display_group)
        
        self.timestamp_cb = QCheckBox("显示时间戳")
        self.timestamp_cb.setChecked(self.settings['timestamp'])
        
        display_layout.addWidget(self.timestamp_cb)
        
        # 字体大小设置
        font_group_inner = QGroupBox("字体设置")
        font_inner_layout = QVBoxLayout(font_group_inner)
        
        # 主字体大小
        main_font_layout = QHBoxLayout()
        main_font_layout.addWidget(QLabel("主字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setValue(self.settings.get('font_size', 12))
        self.font_size_spin.setSuffix(" px")
        main_font_layout.addWidget(self.font_size_spin)
        main_font_layout.addStretch()
        font_inner_layout.addLayout(main_font_layout)
        
        # 等宽字体大小
        mono_font_layout = QHBoxLayout()
        mono_font_layout.addWidget(QLabel("等宽字体大小:"))
        self.mono_font_size_spin = QSpinBox()
        self.mono_font_size_spin.setRange(8, 20)
        self.mono_font_size_spin.setValue(self.settings.get('mono_font_size', 11))
        self.mono_font_size_spin.setSuffix(" px")
        mono_font_layout.addWidget(self.mono_font_size_spin)
        mono_font_layout.addStretch()
        font_inner_layout.addLayout(mono_font_layout)
        
        # UI缩放
        ui_scale_layout = QHBoxLayout()
        ui_scale_layout.addWidget(QLabel("界面缩放:"))
        self.ui_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.ui_scale_slider.setRange(80, 150)
        self.ui_scale_slider.setValue(int(self.settings.get('ui_scale', 100)))
        self.ui_scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.ui_scale_slider.setTickInterval(10)
        ui_scale_layout.addWidget(self.ui_scale_slider)
        
        self.ui_scale_label = QLabel(f"{self.ui_scale_slider.value()}%")
        ui_scale_layout.addWidget(self.ui_scale_label)
        
        # 连接缩放滑块信号
        self.ui_scale_slider.valueChanged.connect(self.update_ui_scale_label)
        
        font_inner_layout.addLayout(ui_scale_layout)
        
        display_layout.addWidget(font_group_inner)
        ui_layout.addWidget(display_group)
        
        # 主题设置
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        # 添加样式表
        self.theme_combo.setStyleSheet("""
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
        # 添加中文主题名称，但保存英文值
        self.theme_combo.addItem("多巴胺浅色系", "dopamine")
        self.theme_combo.addItem("深色主题", "dark")
        self.theme_combo.addItem("浅色主题", "light")
        self.theme_combo.addItem("自定义主题", "custom")
        
        # 设置当前选中的主题
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == self.settings['theme']:
                self.theme_combo.setCurrentIndex(i)
                break
        
        theme_layout.addWidget(QLabel("选择主题:"))
        theme_layout.addWidget(self.theme_combo)
        ui_layout.addWidget(theme_group)
        
        ui_layout.addStretch()
        parent.addTab(ui_widget, "界面设置")
        
    def create_serial_tab(self, parent):
        """创建串口设置选项卡"""
        serial_widget = QWidget()
        serial_layout = QVBoxLayout(serial_widget)
        
        # 连接设置
        connection_group = QGroupBox("连接设置")
        connection_layout = QVBoxLayout(connection_group)
        
        self.auto_connect_cb = QCheckBox("自动连接默认设备")
        self.auto_connect_cb.setChecked(self.settings['auto_connect'])
        connection_layout.addWidget(self.auto_connect_cb)
        
        # 默认端口
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("默认端口:"))
        self.default_port_combo = QComboBox()
        self.default_port_combo.setEditable(True)
        self.default_port_combo.setStyleSheet("""
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
        self.default_port_combo.setCurrentText(self.settings['default_port'])
        port_layout.addWidget(self.default_port_combo)
        connection_layout.addLayout(port_layout)
        
        # 默认波特率
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("默认波特率:"))
        self.default_baud_combo = QComboBox()
        self.default_baud_combo.setStyleSheet(self.default_port_combo.styleSheet())
        self.default_baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.default_baud_combo.setCurrentText(self.settings['default_baud'])
        baud_layout.addWidget(self.default_baud_combo)
        connection_layout.addLayout(baud_layout)
        
        serial_layout.addWidget(connection_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 10000)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" ms")
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("连接超时:"))
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        
        advanced_layout.addLayout(timeout_layout)
        
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_count_spin.setValue(3)
        
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("重试次数:"))
        retry_layout.addWidget(self.retry_count_spin)
        retry_layout.addStretch()
        
        advanced_layout.addLayout(retry_layout)
        serial_layout.addWidget(advanced_group)
        
        serial_layout.addStretch()
        parent.addTab(serial_widget, "串口设置")
        
    def create_help_tab(self, parent):
        """创建帮助中心选项卡"""
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        
        # 帮助内容
        help_group = QGroupBox("使用帮助")
        help_group_layout = QVBoxLayout(help_group)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>🌈 ColorBridge 使用指南</h3>
        
        <h4>📋 基础操作</h4>
        <ul>
        <li><b>连接设备:</b> 选择串口和波特率，点击"连接"按钮</li>
        <li><b>发送命令:</b> 在输入框中输入命令，按回车或点击"发送"</li>
        <li><b>快捷命令:</b> 点击右侧快捷按钮直接发送常用命令</li>
        <li><b>清空显示:</b> 点击"清空"按钮清除消息显示区域</li>
        </ul>
        
        <h4>🎨 界面定制</h4>
        <ul>
        <li><b>透明度:</b> 拖动滑块调整窗口透明度</li>
        <li><b>壁纸:</b> 点击"浏览..."选择自定义壁纸图片</li>
        <li><b>主题:</b> 选择不同的颜色主题</li>
        <li><b>字体:</b> 调整显示区域的字体大小</li>
        </ul>
        
        <h4>⚡ AI8051U 氢原子终端特殊功能</h4>
        <ul>
        <li><b>智能着色:</b> 自动识别消息类型并着色显示</li>
        <li><b>命令识别:</b> 特殊识别AI8051U命令输出</li>
        <li><b>硬件测试:</b> 专门优化的硬件测试结果显示</li>
        <li><b>性能数据:</b> 高亮显示性能测试结果</li>
        <li><b>状态指示:</b> 启用AI8051U检测后，右侧系统状态栏显示实时状态</li>
        <li><b>自动滚动:</b> 默认启用自动滚动到底部，无需手动设置</li>
        </ul>
        
        <h4>🔧 故障排除</h4>
        <ul>
        <li><b>无法连接:</b> 检查串口是否被其他程序占用</li>
        <li><b>显示乱码:</b> 确认波特率设置正确</li>
        <li><b>响应慢:</b> 检查USB连接和驱动程序</li>
        <li><b>AI8051U状态不显示:</b> 确保已启用AI8051U检测选项，状态显示在右侧系统状态栏</li>
        <li><b>发送间隔过长:</b> 默认发送间隔已优化为200ms</li>
        </ul>
        
        <h4>📞 技术支持</h4>
        <p>
        项目地址: <a href="https://atomgit.com/H076lik/ColorBridge">https://atomgit.com/H076lik/ColorBridge</a><br>
        问题反馈: 请在项目仓库提交Issue<br>
        开源协议: GPLV3
        </p>
        """)
        
        help_group_layout.addWidget(help_text)
        help_layout.addWidget(help_group)
        
        # 更新设置
        update_group = QGroupBox("在线更新")
        update_layout = QVBoxLayout(update_group)
        
        self.check_update_btn = QPushButton("检查更新")
        self.download_help_btn = QPushButton("下载最新帮助文档")
        
        update_layout.addWidget(self.check_update_btn)
        update_layout.addWidget(self.download_help_btn)
        help_layout.addWidget(update_group)
        
        help_layout.addStretch()
        parent.addTab(help_widget, "帮助中心")
        
    def create_display_tab(self, parent):
        """创建显示设置选项卡"""
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        
        # 全局文本颜色设置
        color_group = QGroupBox("全局文本颜色")
        color_layout = QVBoxLayout(color_group)
        
        # 使用全局文本颜色复选框
        self.use_global_color_cb = QCheckBox("使用全局文本颜色（覆盖消息类型着色）")
        self.use_global_color_cb.setChecked(self.settings.get('use_global_text_color', False))
        color_layout.addWidget(self.use_global_color_cb)
        
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("接收消息区文本颜色:"))
        self.color_button = QPushButton("选择颜色")
        self.color_button.setMinimumWidth(100)
        color_row.addWidget(self.color_button)
        color_row.addStretch()
        color_layout.addLayout(color_row)
        
        # 颜色预览
        self.color_preview = QLabel("颜色预览文本")
        self.color_preview.setStyleSheet(
            f"background-color: rgb(240, 240, 240); padding: 10px; color: {self.settings['global_text_color']};"
        )
        color_layout.addWidget(self.color_preview)
        
        display_layout.addWidget(color_group)
        
        # AI8051U检测设置
        ai8051u_group = QGroupBox("AI8051U 系统检测")
        ai8051u_layout = QVBoxLayout(ai8051u_group)
        
        self.ai8051u_cb = QCheckBox("启用 AI8051U 系统信息自动识别")
        self.ai8051u_cb.setChecked(self.settings['ai8051u_detection_enabled'])
        ai8051u_layout.addWidget(self.ai8051u_cb)
        
        ai8051u_info = QLabel("启用后，检测到 AI8051U 系统信息时右侧系统状态栏会显示实时状态指示")
        ai8051u_info.setWordWrap(True)
        ai8051u_layout.addWidget(ai8051u_info)
        
        display_layout.addWidget(ai8051u_group)
        
        # 终端日志设置
        log_group = QGroupBox("终端消息日志")
        log_layout = QVBoxLayout(log_group)
        
        self.terminal_log_cb = QCheckBox("启用终端消息日志记录")
        self.terminal_log_cb.setChecked(self.settings.get('terminal_log_enabled', False))
        log_layout.addWidget(self.terminal_log_cb)
        
        log_info = QLabel("启用后，所有终端显示的消息（发送和接收）将记录到单独的日志文件中")
        log_info.setWordWrap(True)
        log_layout.addWidget(log_info)
        
        # 日志目录显示
        log_dir_layout = QHBoxLayout()
        log_dir_layout.addWidget(QLabel("日志目录:"))
        self.log_dir_label = QLabel("logs/terminal/")
        self.log_dir_label.setStyleSheet("color: #666666;")
        log_dir_layout.addWidget(self.log_dir_label)
        log_dir_layout.addStretch()
        log_layout.addLayout(log_dir_layout)
        
        display_layout.addWidget(log_group)
        display_layout.addStretch()
        parent.addTab(display_widget, "显示设置")
        
    def setup_connections(self):
        """设置信号连接"""
        # 透明度滑块
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        # 壁纸按钮
        self.browse_btn.clicked.connect(self.browse_wallpaper)
        self.clear_wallpaper_btn.clicked.connect(self.clear_wallpaper)
        
        # 颜色选择按钮
        self.color_button.clicked.connect(self.choose_color)
        
        # 对话框按钮
        self.reset_btn.clicked.connect(self.reset_settings)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.clicked.connect(self.ok_clicked)
        
        # 更新按钮
        self.check_update_btn.clicked.connect(self.check_for_updates)
        self.download_help_btn.clicked.connect(self.download_help_docs)
        
    def on_opacity_changed(self, value):
        """透明度改变处理"""
        self.opacity_label.setText(f"透明度: {value}%")
        if self.parent():
            # 确保透明度设置立即生效
            opacity = value / 100.0
            self.parent().setWindowOpacity(opacity)
            # 强制更新窗口显示
            self.parent().update()
            self.parent().repaint()
            
    def browse_wallpaper(self):
        """浏览壁纸文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择壁纸文件", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)"
        )
        if file_path:
            self.wallpaper_path.setText(file_path)
            # 立即预览壁纸
            if self.parent():
                self.parent().set_wallpaper(file_path)
                
    def clear_wallpaper(self):
        """清除壁纸"""
        self.wallpaper_path.clear()
        if self.parent():
            self.parent().clear_wallpaper()
    
    
            
    def choose_color(self):
        """选择颜色"""
        # 获取当前颜色作为默认值
        current_color = self.settings.get('global_text_color', 'rgb(200, 200, 200)')
        # 解析RGB颜色字符串
        import re
        match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', current_color)
        if match:
            default_color = QColor(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        else:
            default_color = QColor(200, 200, 200)
            
        color = QColorDialog.getColor(default_color)
        if color.isValid():
            # 更新预览
            rgb_color = f"rgb({color.red()}, {color.green()}, {color.blue()})"
            self.color_preview.setStyleSheet(
            f"background-color: rgb(240, 240, 240); padding: 10px; color: {rgb_color};"
        )
            self.settings['global_text_color'] = rgb_color
            
            # 立即应用到父窗口
            if self.parent():
                self.parent().apply_settings({'global_text_color': rgb_color})
            
    def reset_settings(self):
        """重置设置为默认值"""
        self.settings = {
            'opacity': 90,
            'wallpaper': '',
            'wallpaper_opacity': 70,
            'timestamp': True,
            'font_size': 12,
            'mono_font_size': 11,
            'ui_scale': 100,
            'theme': 'dopamine',
            'auto_connect': False,
            'default_port': '',
            'default_baud': '115200',
            'global_text_color': 'rgb(200, 200, 200)',
            'ai8051u_detection_enabled': True,
            'use_global_text_color': False,
        }
        self.load_settings()
        
    def apply_settings(self):
        """应用设置"""
        self.save_settings()
        if self.parent():
            self.parent().apply_settings(self.settings)
        
    def ok_clicked(self):
        """确定按钮点击"""
        self.apply_settings()
        self.accept()
        
    def update_ui_scale_label(self, value):
        """更新UI缩放标签显示"""
        self.ui_scale_label.setText(f"{value}%")
        # 实时预览缩放效果
        if self.parent():
            scale_factor = value / 100.0
            self.parent().setWindowScale(scale_factor)

    def save_settings(self):
        """保存设置"""
        # 保存设置
        self.settings['opacity'] = self.opacity_slider.value()
        self.settings['wallpaper'] = self.wallpaper_path.text()
        self.settings['timestamp'] = self.timestamp_cb.isChecked()
        print(f"[DEBUG] save_settings: timestamp={self.settings['timestamp']}")
        self.settings['font_size'] = self.font_size_spin.value()
        if hasattr(self, 'mono_font_size_spin'):
            self.settings['mono_font_size'] = self.mono_font_size_spin.value()
        if hasattr(self, 'ui_scale_slider'):
            self.settings['ui_scale'] = self.ui_scale_slider.value()
        self.settings['theme'] = self.theme_combo.currentData()
        self.settings['auto_connect'] = self.auto_connect_cb.isChecked()
        self.settings['default_port'] = self.default_port_combo.currentText()
        self.settings['default_baud'] = self.default_baud_combo.currentText()
        self.settings['global_text_color'] = self.settings.get('global_text_color', 'rgb(200, 200, 200)')
        self.settings['ai8051u_detection_enabled'] = self.ai8051u_cb.isChecked()
        self.settings['use_global_text_color'] = self.use_global_color_cb.isChecked()
        
        # 保存终端日志设置
        if hasattr(self, 'terminal_log_cb'):
            self.settings['terminal_log_enabled'] = self.terminal_log_cb.isChecked()
        
        # 保存到文件
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] 设置已保存到: {self.settings_file}")
            
            # 发送设置改变信号
            self.settings_changed.emit(self.settings)
        except Exception as e:
            print(f"[ERROR] 保存设置失败: {e}")
        
    def load_settings_from_file(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                print(f"[DEBUG] 从文件加载设置: {self.settings_file}")
                return loaded_settings
            else:
                print(f"[DEBUG] 设置文件不存在，使用默认设置: {self.settings_file}")
                return self.settings
        except Exception as e:
            print(f"[ERROR] 加载设置失败: {e}")
            return self.settings
    
    def load_settings(self):
        """加载设置"""
        # 先从文件加载
        file_settings = self.load_settings_from_file()
        self.settings.update(file_settings)
        
        # 应用到界面控件
        self.opacity_slider.setValue(self.settings['opacity'])
        self.wallpaper_path.setText(self.settings['wallpaper'])
        if hasattr(self, 'wallpaper_opacity_slider'):
            self.wallpaper_opacity_slider.setValue(int(self.settings.get('wallpaper_opacity', 70)))
        self.timestamp_cb.setChecked(self.settings['timestamp'])
        self.font_size_spin.setValue(self.settings.get('font_size', 12))
        
        # 设置新的字体控件
        if hasattr(self, 'mono_font_size_spin'):
            self.mono_font_size_spin.setValue(self.settings.get('mono_font_size', 11))
        if hasattr(self, 'ui_scale_slider'):
            self.ui_scale_slider.setValue(self.settings.get('ui_scale', 100))
            self.update_ui_scale_label(self.settings.get('ui_scale', 100))
            
        # 根据保存的英文主题名称设置下拉框
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == self.settings['theme']:
                self.theme_combo.setCurrentIndex(i)
                break
        self.auto_connect_cb.setChecked(self.settings['auto_connect'])
        
        # 设置默认端口
        if self.settings['default_port']:
            index = self.default_port_combo.findText(self.settings['default_port'])
            if index >= 0:
                self.default_port_combo.setCurrentIndex(index)
                
        # 设置默认波特率
        if self.settings['default_baud']:
            index = self.default_baud_combo.findText(self.settings['default_baud'])
            if index >= 0:
                self.default_baud_combo.setCurrentIndex(index)
                
        # 设置AI8051U检测
        if hasattr(self, 'ai8051u_cb'):
            self.ai8051u_cb.setChecked(self.settings.get('ai8051u_detection_enabled', True))
            
        # 设置全局文本颜色
        if hasattr(self, 'use_global_color_cb'):
            self.use_global_color_cb.setChecked(self.settings.get('use_global_text_color', False))
            
        # 设置终端日志记录
        if hasattr(self, 'terminal_log_cb'):
            self.terminal_log_cb.setChecked(self.settings.get('terminal_log_enabled', False))
        
    def check_for_updates(self):
        """检查更新"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "检查更新", "当前版本是最新版本！")
        
    def download_help_docs(self):
        """下载最新帮助文档"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "下载帮助", "帮助文档已是最新版本！")
        
    def send_hardware_test_command(self, command):
        """发送硬件测试命令"""
        if self.parent() and self.parent().serial_manager.is_connected():
            self.parent().serial_manager.send_command(command)
            # 使用QTimer延迟调用UI操作，确保在主线程中执行
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.parent().add_message(f"📤 发送硬件测试命令: {command}", "info"))
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请先连接设备后再发送硬件测试命令！")
        
    def create_device_info_tab(self, parent):
        """创建设备信息选项卡"""
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        
        # 创建水平布局，将设备信息和状态并排显示
        info_status_layout = QHBoxLayout()
        
        # 设备信息显示区域
        info_group = QGroupBox("AI8051U 设备信息")
        info_layout = QVBoxLayout(info_group)
        
        # 创建设备信息显示文本框
        self.device_info_text = QTextEdit()
        self.device_info_text.setReadOnly(True)
        self.device_info_text.setFont(QFont("Consolas", 9))
        self.device_info_text.setMaximumHeight(300)
        
        info_layout.addWidget(self.device_info_text)
        
        # 刷新和自动发送选项
        refresh_layout = QHBoxLayout()
        self.refresh_device_info_btn = QPushButton("刷新")
        self.refresh_device_info_btn.setMaximumWidth(60)
        self.refresh_device_info_btn.clicked.connect(self.refresh_device_info)
        refresh_layout.addWidget(self.refresh_device_info_btn)
        refresh_layout.addStretch()
        
        info_layout.addLayout(refresh_layout)
        
        # 设备状态信息
        status_group = QGroupBox("设备状态")
        status_layout = QVBoxLayout(status_group)
        
        self.device_status_text = QTextEdit()
        self.device_status_text.setReadOnly(True)
        self.device_status_text.setFont(QFont("Consolas", 9))
        self.device_status_text.setMaximumHeight(150)
        
        status_layout.addWidget(self.device_status_text)
        
        # 将设备信息和状态添加到水平布局
        info_status_layout.addWidget(info_group, 2)  # 设备信息占2/3宽度
        info_status_layout.addWidget(status_group, 1)  # 设备状态占1/3宽度
        
        device_layout.addLayout(info_status_layout)
        
        # 硬件测试按钮和使用说明 - 使用水平布局
        test_help_layout = QHBoxLayout()
        
        # 硬件测试按钮组
        test_group = QGroupBox("硬件测试")
        test_group_layout = QVBoxLayout(test_group)
        
        # 第一行按钮
        test_row1 = QHBoxLayout()
        self.hwtest_btn = QPushButton("hwtest")
        self.hwtest_btn.setToolTip("硬件加速单元测试(MDU32+TFPU)")
        self.hwtest_btn.clicked.connect(lambda: self.send_hardware_test_command("hwtest"))
        
        self.mdu32_btn = QPushButton("mdu32")
        self.mdu32_btn.setToolTip("MDU32硬件乘除单元详细测试")
        self.mdu32_btn.clicked.connect(lambda: self.send_hardware_test_command("mdu32"))
        
        test_row1.addWidget(self.hwtest_btn)
        test_row1.addWidget(self.mdu32_btn)
        
        # 第二行按钮
        test_row2 = QHBoxLayout()
        self.tfpu_btn = QPushButton("tfpu")
        self.tfpu_btn.setToolTip("TFPU浮点运算单元详细测试")
        self.tfpu_btn.clicked.connect(lambda: self.send_hardware_test_command("tfpu"))
        
        self.benchmark_btn = QPushButton("benchmark")
        self.benchmark_btn.setToolTip("硬件加速性能基准测试")
        self.benchmark_btn.clicked.connect(lambda: self.send_hardware_test_command("benchmark"))
        
        test_row2.addWidget(self.tfpu_btn)
        test_row2.addWidget(self.benchmark_btn)
        
        # 第三行按钮
        test_row3 = QHBoxLayout()
        self.clockinfo_btn = QPushButton("clockinfo")
        self.clockinfo_btn.setToolTip("AI8051U时钟系统详细信息")
        self.clockinfo_btn.clicked.connect(lambda: self.send_hardware_test_command("clockinfo"))
        
        self.voltage_btn = QPushButton("voltage")
        self.voltage_btn.setToolTip("测量电源电压")
        self.voltage_btn.clicked.connect(lambda: self.send_hardware_test_command("voltage"))
        
        test_row3.addWidget(self.clockinfo_btn)
        test_row3.addWidget(self.voltage_btn)
        
        test_group_layout.addLayout(test_row1)
        test_group_layout.addLayout(test_row2)
        test_group_layout.addLayout(test_row3)
        
        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QLabel(
            "• 连接设备后点击'刷新'按钮获取信息\n"
            "• 硬件测试命令序列: hwtest→mdu32→tfpu→benchmark\n"
            "• 每个命令间隔200ms确保快速响应\n"
            "• 手动刷新需设备已连接\n"
            "• 启用AI8051U检测时，左上角显示状态指示"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: rgb(100, 100, 100); font-size: 11px; padding: 5px;")
        
        help_layout.addWidget(help_text)
        
        # 将测试按钮和说明添加到水平布局
        test_help_layout.addWidget(test_group)
        test_help_layout.addWidget(help_group)
        
        device_layout.addLayout(test_help_layout)
        
        device_layout.addStretch()
        parent.addTab(device_widget, "设备信息")
        
        # 初始加载设备信息
        self.refresh_device_info()
        
    def refresh_device_info(self):
        """刷新设备信息显示"""
        if self.parent() and hasattr(self.parent(), 'device_info_manager'):
            device_info = self.parent().device_info_manager.get_device_info()
            
            # 格式化设备信息显示
            info_text = "=== AI8051U 设备信息 ===\n\n"
            
            # 系统信息
            info_text += "【系统信息】\n"
            info_text += f"微控制器: {device_info['system'].get('mcu', '未知')}\n"
            info_text += f"系统名称: {device_info['system'].get('system', 'AI8051U氢原子系统' if device_info['system'].get('mcu') == 'AI8051U' else '未知')}\n"
            
            # 版本信息 - 如果为空则显示相应提示
            version = device_info['system'].get('version', '')
            if version:
                info_text += f"版本: {version}\n"
            else:
                info_text += "版本: 等待设备信息更新...\n"
                
            # 作者信息 - 如果为空则显示相应提示
            author = device_info['system'].get('author', '')
            if author:
                info_text += f"作者: {author}\n"
            else:
                info_text += "作者: 等待设备信息更新...\n"
                
            info_text += f"编译日期: {device_info['system'].get('build_date', '未知')}\n"
            info_text += f"编译时间: {device_info['system'].get('build_time', '未知')}\n\n"
            
            # 硬件信息
            info_text += "【硬件信息】\n"
            info_text += f"CPU频率: {device_info['system'].get('cpu_clock', device_info['system'].get('clock_frequency', '未知'))}\n"
            info_text += f"Flash大小: {device_info['system'].get('flash_size', '未知')}\n"
            info_text += f"XRAM大小: {device_info['system'].get('xram_size', '未知')}\n"
            info_text += f"RTC时钟: {device_info['system'].get('rtc', '未知')}\n"
            info_text += f"USB-CDC: {device_info['system'].get('usb_cdc', '未知')}\n"
            info_text += f"硬件加速: {device_info['system'].get('hw_acceleration', '未知')}\n\n"
            
            # 外设信息
            if device_info.get('peripherals'):
                info_text += "【外设信息】\n"
                for peripheral, status in device_info['peripherals'].items():
                    info_text += f"{peripheral}: {status}\n"
                info_text += "\n"
            
            # 内存使用
            memory_info = device_info.get('memory', {})
            memory_has_data = any(memory_info.get(key) for key in ['flash_used', 'flash_constants', 'xram_used', 'internal_ram_used'])
            if memory_has_data:
                info_text += "【内存使用】\n"
                if memory_info.get('flash_used'):
                    info_text += f"Flash已用: {memory_info['flash_used']}\n"
                if memory_info.get('flash_constants'):
                    info_text += f"常量存储: {memory_info['flash_constants']}\n"
                if memory_info.get('xram_used'):
                    info_text += f"XRAM已用: {memory_info['xram_used']}\n"
                if memory_info.get('internal_ram_used'):
                    info_text += f"内部RAM: {memory_info['internal_ram_used']}\n"
                info_text += "\n"
            
            # 性能数据
            performance_info = device_info.get('performance', {})
            performance_has_data = any(
                performance_info.get(key) 
                for key in ['overall_score', 'mdu32_efficiency', 'tfpu_efficiency', 
                           'mdu32_multiply_perf', 'mdu32_multiply_avg', 'tfpu_add_perf',
                           'tfpu_multiply_avg', 'tfpu_sin_avg', 'benchmark_completed']
                if performance_info.get(key) not in [None, '', False]
            )
            if performance_has_data:
                info_text += "【性能数据】\n"
                if performance_info.get('mdu32_multiply_perf'):
                    info_text += f"MDU32乘法性能: {performance_info['mdu32_multiply_perf']}\n"
                if performance_info.get('mdu32_multiply_avg'):
                    info_text += f"MDU32乘法平均: {performance_info['mdu32_multiply_avg']}\n"
                if performance_info.get('tfpu_add_perf'):
                    info_text += f"TFPU加法性能: {performance_info['tfpu_add_perf']}\n"
                if performance_info.get('tfpu_multiply_avg'):
                    info_text += f"TFPU乘法平均: {performance_info['tfpu_multiply_avg']}\n"
                if performance_info.get('tfpu_sin_avg'):
                    info_text += f"TFPU正弦平均: {performance_info['tfpu_sin_avg']}\n"
                if performance_info.get('benchmark_completed'):
                    info_text += f"基准测试: {'已完成' if performance_info['benchmark_completed'] else '未完成'}\n"
            
            self.device_info_text.setText(info_text)
            
            # 格式化设备状态
            status_text = "=== 设备状态 ===\n\n"
            status_text += f"系统信息模式: {'已启用' if device_info['status']['system_info_mode'] else '未启用'}\n"
            status_text += f"最后更新: {device_info['status']['last_update']}\n"
            status_text += f"连接状态: {'已连接' if self.parent() and self.parent().serial_manager.is_connected() else '未连接'}\n"
            
            self.device_status_text.setText(status_text)
        else:
            self.device_info_text.setText("设备信息不可用\n请确保设备已连接并执行info命令")
            
            # 即使设备信息不可用，也显示当前时间戳
            status_text = "=== 设备状态 ===\n\n"
            status_text += f"系统信息模式: 未启用\n"
            status_text += f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            status_text += f"连接状态: {'已连接' if self.parent() and hasattr(self.parent(), 'serial_manager') and self.parent().serial_manager.is_connected() else '未连接'}\n"
            self.device_status_text.setText(status_text)
    
    def showEvent(self, event):
        """对话框显示事件"""
        super().showEvent(event)
        
        # 连接设备信息更新信号
        if self.parent() and hasattr(self.parent(), 'device_info_manager'):
            self.parent().device_info_manager.device_info_updated.connect(self.on_device_info_updated)
            
        # 刷新设备信息
        self.refresh_device_info()
    
    def closeEvent(self, event):
        """对话框关闭事件"""
        # 断开设备信息更新信号
        if self.parent() and hasattr(self.parent(), 'device_info_manager'):
            self.parent().device_info_manager.device_info_updated.disconnect(self.on_device_info_updated)
        
        super().closeEvent(event)
    
    def on_device_info_updated(self):
        """设备信息更新处理"""
        # 使用QTimer确保在主线程中执行UI更新
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self.refresh_device_info)
        print("[DEBUG] 设置对话框收到设备信息更新信号，刷新显示")