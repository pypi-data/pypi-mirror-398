#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备信息管理器模块 - ColorBridge
收集、解析和管理AI8051U设备系统信息
"""

import re
import time
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from copy import deepcopy

# 导入日志相关模块
from .colorbridge_debug_logger import get_debug_logger, debug_log, info_log, warning_log, error_log

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class DebugLogger:
    """简化的日志级别控制"""
    def __init__(self, level=LogLevel.INFO):
        self.level = level
    
    def debug(self, message):
        if self.level <= LogLevel.DEBUG:
            debug_log(message, "DeviceInfoManager")
    
    def info(self, message):
        if self.level <= LogLevel.INFO:
            info_log(message, "DeviceInfoManager")
    
    def warning(self, message):
        if self.level <= LogLevel.WARNING:
            warning_log(message, "DeviceInfoManager")
    
    def error(self, message):
        if self.level <= LogLevel.ERROR:
            error_log(message, "DeviceInfoManager")

class SafeDeviceInfoParser:
    """安全的设备信息解析器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.parse_cache = {}
        self.parse_failures = 0
        self.max_failures = 5
    
    def safe_parse_device_info(self, data: str) -> dict:
        """安全解析设备信息"""
        try:
            # 检查缓存
            data_hash = hash(data)
            if data_hash in self.parse_cache:
                return self.parse_cache[data_hash]
            
            # 安全解析
            parsed_info = self._parse_with_fallback(data)
            
            # 成功解析，重置失败计数
            self.parse_failures = 0
            
            # 缓存结果
            self.parse_cache[data_hash] = parsed_info
            
            return parsed_info
            
        except Exception as e:
            self.parse_failures += 1
            
            if self.debug_mode:
                debug_log(f"设备信息解析失败 ({self.parse_failures}/{self.max_failures}): {e}", "DeviceInfoManager")
            
            # 失败次数过多时，清空缓存重新开始
            if self.parse_failures >= self.max_failures:
                self.parse_cache.clear()
                self.parse_failures = 0
                
                if self.debug_mode:
                    debug_log("设备信息解析失败次数过多，清空缓存", "DeviceInfoManager")
            
            # 返回安全的默认信息
            return self._get_safe_default_info()
    
    def _parse_with_fallback(self, data: str) -> dict:
        """带回退机制的解析"""
        try:
            # 主要解析逻辑
            return self._parse_device_info_primary(data)
        except Exception as e:
            if self.debug_mode:
                debug_log(f"主解析失败，使用回退解析: {e}", "DeviceInfoManager")
            # 回退解析逻辑
            return self._parse_device_info_fallback(data)
    
    def _get_safe_default_info(self) -> dict:
        """获取安全的默认信息"""
        return {
            'status': 'parsing_error',
            'timestamp': time.time(),
            'message': '设备信息解析暂时不可用'
        }
    
    def _direct_parse_message(self, message: str) -> bool:
        """直接解析消息，不依赖正则表达式"""
        updated = False
        
        # 按行处理消息
        lines = message.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 直接匹配关键信息
            if '微控制器:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    mcu = parts[1].strip()
                    self.device_info['system']['mcu'] = mcu
                    if self.debug_mode:
                        debug_log(f"直接解析MCU: {mcu}", "DeviceInfoManager")
                    updated = True
            
            elif '时钟频率:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    freq = parts[1].strip()
                    self.device_info['system']['clock_frequency'] = freq
                    self.device_info['system']['clock'] = freq
                    self.device_info['system']['cpu_clock'] = freq
                    self.device_info['performance']['cpu_frequency'] = freq
                    
                    # 尝试提取TFPU频率
                    if 'TFPU:' in freq or 'tfpu:' in freq.lower():
                        # 简单提取TFPU频率
                        if '(' in freq and ')' in freq:
                            tfpu_part = freq[freq.find('(')+1:freq.find(')')]
                            if 'TFPU:' in tfpu_part:
                                tfpu_freq = tfpu_part.split(':', 1)[1].strip()
                                self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                                self.device_info['performance']['tfpu_enabled'] = True
                    
                    if self.debug_mode:
                        debug_log(f"直接解析时钟频率: {freq}", "DeviceInfoManager")
                    updated = True
            
            elif 'Flash大小:' in line or 'Flash:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    flash = parts[1].strip()
                    self.device_info['system']['flash_size'] = flash
                    self.device_info['system']['flash'] = flash
                    if self.debug_mode:
                        debug_log(f"直接解析Flash: {flash}", "DeviceInfoManager")
                    updated = True
            
            elif 'XRAM大小:' in line or 'XRAM:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    xram = parts[1].strip()
                    self.device_info['system']['xram_size'] = xram
                    self.device_info['system']['xram'] = xram
                    if self.debug_mode:
                        debug_log(f"直接解析XRAM: {xram}", "DeviceInfoManager")
                    updated = True
            
            elif 'USB-CDC:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    usb = parts[1].strip()
                    self.device_info['system']['usb_cdc'] = usb
                    if self.debug_mode:
                        debug_log(f"直接解析USB-CDC: {usb}", "DeviceInfoManager")
                    updated = True
            
            elif 'Flash已用:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    flash_used = parts[1].strip()
                    if 'memory' not in self.device_info:
                        self.device_info['memory'] = {}
                    self.device_info['memory']['flash_used'] = flash_used
                    if self.debug_mode:
                        debug_log(f"直接解析Flash已用: {flash_used}", "DeviceInfoManager")
                    updated = True
            
            elif '内部RAM:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    internal_ram = parts[1].strip()
                    if 'memory' not in self.device_info:
                        self.device_info['memory'] = {}
                    self.device_info['memory']['internal_ram'] = internal_ram
                    if self.debug_mode:
                        debug_log(f"直接解析内部RAM: {internal_ram}", "DeviceInfoManager")
                    updated = True
            
            elif '当前时间:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    rtc_time = parts[1].strip()
                    self.device_info['status']['rtc_time'] = rtc_time
                    if self.debug_mode:
                        debug_log(f"直接解析RTC时间: {rtc_time}", "DeviceInfoManager")
                    updated = True
        
        return updated
    
    def _parse_device_info_primary(self, data: str) -> dict:
        """主要解析逻辑"""
        result = {}
        
        # 解析MCU信息
        mcu_match = re.search(r'微控制器:\s*(.+)', data)
        if mcu_match:
            result['mcu'] = mcu_match.group(1).strip()
        
        # 解析时钟频率
        clock_match = re.search(r'时钟频率:\s*(.+)', data)
        if clock_match:
            result['clock_frequency'] = clock_match.group(1).strip()
        
        # 解析Flash大小
        flash_match = re.search(r'Flash大小:\s*(.+)', data)
        if flash_match:
            result['flash_size'] = flash_match.group(1).strip()
        
        # 解析XRAM大小
        xram_match = re.search(r'XRAM大小:\s*(.+)', data)
        if xram_match:
            result['xram_size'] = xram_match.group(1).strip()
        
        # 解析USB-CDC状态
        usb_match = re.search(r'USB-CDC:\s*(.+)', data)
        if usb_match:
            result['usb_cdc'] = usb_match.group(1).strip()
        
        return result
    
    def _parse_device_info_fallback(self, data: str) -> dict:
        """回退解析逻辑 - 更宽松的解析"""
        result = {}
        
        # 更宽松的MCU解析
        for pattern in [r'MCU[:\s]*(.+)', r'微控制器[:\s]*(.+)', r'控制器[:\s]*(.+)']:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result['mcu'] = match.group(1).strip()
                break
        
        # 更宽松的时钟频率解析
        for pattern in [r'时钟[:\s]*([\d.]+\s*[MG]Hz)', r'频率[:\s]*([\d.]+\s*[MG]Hz)', r'clock[:\s]*([\d.]+\s*[MG]Hz)']:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result['clock_frequency'] = match.group(1).strip()
                break
        
        # 更宽松的Flash解析
        for pattern in [r'Flash[:\s]*([\d.]+\s*[KMGT]?B)', r'闪存[:\s]*([\d.]+\s*[KMGT]?B)']:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result['flash_size'] = match.group(1).strip()
                break
        
        # 更宽松的XRAM解析
        for pattern in [r'XRAM[:\s]*([\d.]+\s*[KMGT]?B)', r'外部RAM[:\s]*([\d.]+\s*[KMGT]?B)']:
            match = re.search(pattern, data, re.IGNORECASE)
            if match:
                result['xram_size'] = match.group(1).strip()
                break
        
        return result


class ColorBridgeDeviceInfoManager(QObject):
    """设备信息管理器 - 清理版本"""
    
    # 信号定义
    device_info_updated = pyqtSignal(dict)
    
    def __init__(self, serial_manager=None):
        super().__init__()
        self.debug_mode = False  # 默认关闭调试模式
        self.logger = DebugLogger(LogLevel.INFO)
        self.logger = DebugLogger(LogLevel.DEBUG if self.debug_mode else LogLevel.INFO)
        
        # 保存串口管理器引用用于连接状态检查
        self.serial_manager = serial_manager
        
        # 初始化安全解析器
        self.safe_parser = SafeDeviceInfoParser(debug_mode=self.debug_mode)
        
        # 设备信息存储
        self.device_info = {
            'system': {
                'mcu': '',
                'clock': '',
                'clock_frequency': '',  # 新增字段
                'flash': '',
                'flash_size': '',  # 新增字段
                'flash_used': '',
                'xram': '',
                'xram_size': '',  # 新增字段
                'xram_used': '',
                'internal_ram': '',
                'usb_cdc': '',
                'compile_date': '',
                'compile_time': '',
                'build_date': '',  # 兼容字段
                'build_time': '',  # 兼容字段
                'rtc_time': '',
                'power_management': '',
                'version': '',  # 版本信息
                'author': '',  # 作者信息
                'system': ''  # 系统名称
            },
            'hardware': {
                'gpio': {
                    'count': '',
                    'type': '',
                    'interrupts': ''
                },
                'timers': {
                    'count': '',
                    'types': '',
                    'pwm_channels': ''
                },
                'uart': {
                    'count': '',
                    'baud_rates': '',
                    'flow_control': ''
                },
                'spi': {
                    'count': '',
                    'max_speed': '',
                    'modes': ''
                },
                'i2c': {
                    'count': '',
                    'max_speed': '',
                    'address_bits': ''
                },
                'adc': {
                    'resolution': '',
                    'channels': '',
                    'reference': ''
                },
                'dac': {
                    'resolution': '',
                    'channels': '',
                    'output_range': ''
                },
                'mdu32': {
                    'status': '',
                    'description': '',
                    'multiply_result': '',
                    'multiply_time': '',
                    'multiply_ratio': '',
                    'divide_result': '',
                    'divide_time': '',
                    'divide_ratio': ''
                },
                'tfpu': {
                    'status': '',
                    'description': '',
                    'add_result': '',
                    'add_time': '',
                    'add_ratio': '',
                    'multiply_result': '',
                    'multiply_time': '',
                    'multiply_ratio': '',
                    'divide_result': '',
                    'divide_time': '',
                    'divide_ratio': '',
                    'sin_result': '',
                    'sin_time': '',
                    'sin_ratio': ''
                }
            },
            'performance': {
                'cpu_frequency': '',
                'instruction_cycle': '',
                'multiply_divide_cycles': '',
                'tfpu_enabled': False,
                'tfpu_frequency': '',
                'benchmark_results': '',
                'memory_usage': '',
                'power_consumption': ''
            },
            'memory': {  # 添加缺失的memory键
                'flash_used': '',
                'flash_constants': '',
                'xram_used': '',
                'internal_ram_used': ''
            },
            'status': {
                'connection_status': '',
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error_count': 0,
                'warning_count': 0,
                'system_info_mode': False,
                'hardware_test_mode': False,
                'memory_mode': False,
                'voltage_mode': False,
                'clock_info_mode': False,
                'neofetch_mode': False,
                'system_startup_mode': False  # 新增：系统启动信息解析模式
            }
        }
        
        # 解析状态
        self.parsing_mode = None
        self.current_section = None
        
        # 性能监控
        self.last_update_time = time.time()
        self.update_count = 0
        
        # 去重机制 - 避免重复更新，但允许时间戳更新
        self.last_device_info_hash = None
        self.dedup_window = 2.0  # 2秒去重窗口，允许时间戳变化
        self.last_update_time = 0
        self.content_dedup_window = 0.5  # 内容去重窗口（更短，避免重复内容）
        self.last_content_hash = None
        
        # 添加模式超时机制
        self.mode_start_time = {}
        self.mode_timeout = 5  # 5秒超时
        
        # 初始化正则表达式模式
        self._initialize_patterns()
        
    def _update_timestamp(self):
        """更新时间戳"""
        try:
            self.device_info['status']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            if self.debug_mode:
                debug_log(f"更新时间戳失败: {e}", "DeviceInfoManager")
    
    def _safe_emit_device_info_update(self):
        """安全地发送设备信息更新信号，同时更新时间戳"""
        self._update_timestamp()
        self.device_info_updated.emit(self.device_info)
        
    def _initialize_patterns(self):
        """初始化正则表达式模式"""
        # 编译正则表达式
        self.patterns = {
            'system_info': re.compile(r'系统信息:'),
            'mcu': re.compile(r'微控制器:\s*(.+)'),
            'system_mcu': re.compile(r'ℹ️ 微控制器:\s*(.+)'),  # 新版本格式
            'clock': re.compile(r'时钟频率:\s*(.+)'),
            'system_clock': re.compile(r'ℹ️ 时钟频率:\s*(.+)'),  # 新版本格式
            'flash': re.compile(r'Flash大小:\s*(.+)'),
            'system_flash': re.compile(r'🖥️ Flash:\s*(.+)'),  # 新版本格式
            'xram': re.compile(r'XRAM大小:\s*(.+)'),
            'system_xram': re.compile(r'🖥️ XRAM:\s*(.+)'),  # 新版本格式
            'usb_cdc': re.compile(r'USB-CDC:\s*(.+)'),
            'system_usb_cdc': re.compile(r'✅ USB-CDC:\s*(.+)'),  # 新版本格式
            'build_date': re.compile(r'编译日期:\s*(.+)'),
            'build_time': re.compile(r'编译时间:\s*(.+)'),
            'rtc_time': re.compile(r'当前时间:\s*(.+)'),
            'flash_constants': re.compile(r'常量存储:\s*(.+)'),
            'voltage': re.compile(r'电源电压:\s*(.+)'),
            'voltage_raw': re.compile(r'ADC原始值:\s*(.+)'),
            'voltage_channel': re.compile(r'测量通道:\s*(.+)'),
            'voltage_reference': re.compile(r'参考电压:\s*(.+)'),
            'voltage_resolution': re.compile(r'分辨率:\s*(.+)'),
            'voltage_samples': re.compile(r'采样次数:\s*(.+)'),
            'flash_used': re.compile(r'Flash已用:\s*(.+)'),
            'xram_used': re.compile(r'XRAM已用:\s*(.+)'),
            'internal_ram': re.compile(r'内部RAM:\s*(.+)'),
            'tfpu_clock': re.compile(r'TFPU时钟源:\s*(.+)'),
            'cpu_clock': re.compile(r'CPU时钟:\s*(.+)'),
            'tfpu_clkdiv_reg': re.compile(r'TFPU_CLKDIV寄存器:\s*(.+)'),
            'mdu32_multiply': re.compile(r'乘法测试:\s*(.+)'),
            'mdu32_multiply_time': re.compile(r'执行时间:\s*(.+)'),
            'mdu32_multiply_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'mdu32_divide': re.compile(r'除法测试:\s*(.+)'),
            'mdu32_divide_time': re.compile(r'执行时间:\s*(.+)'),
            'mdu32_divide_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'tfpu_add': re.compile(r'加法测试:\s*(.+)'),
            'tfpu_add_time': re.compile(r'执行时间:\s*(.+)'),
            'tfpu_add_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'tfpu_multiply': re.compile(r'乘法测试:\s*(.+)'),
            'tfpu_multiply_time': re.compile(r'执行时间:\s*(.+)'),
            'tfpu_multiply_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'tfpu_sin': re.compile(r'正弦测试:\s*(.+)'),
            'tfpu_sin_time': re.compile(r'执行时间:\s*(.+)'),
            'tfpu_sin_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'tfpu_cos': re.compile(r'余弦测试:\s*(.+)'),
            'tfpu_cos_time': re.compile(r'执行时间:\s*(.+)'),
            'tfpu_cos_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'tfpu_sqrt': re.compile(r'平方根测试:\s*(.+)'),
            'tfpu_sqrt_time': re.compile(r'执行时间:\s*(.+)'),
            'tfpu_sqrt_ratio': re.compile(r'硬件加速比:\s*(.+)'),
            'hardware_status': re.compile(r'硬件状态:'),
            'neofetch_system': re.compile(r'AI8051U氢原子系统'),
            'neofetch_version': re.compile(r'版本:\s*(.+)'),
            'neofetch_author': re.compile(r'作者:\s*(.+)')
        }
        
        # 新增2.0.5版本的解析模式
        self.v205_patterns = {
            'clock_info_header': re.compile(r'AI8051U时钟系统详细信息'),
            'system_clock_config': re.compile(r'系统时钟配置:'),
            'sys_clock': re.compile(r'系统时钟\(SYSCLK\):\s*(.+)'),
            'pll_output': re.compile(r'PLL输出时钟:\s*([\d.]+MHz\s*\(.*\))|PLL输出时钟:\s*(.+)'),
            'high_speed_peripheral': re.compile(r'高速外设时钟:\s*(.+)'),
            'tfpu_clock_config': re.compile(r'TFPU时钟配置:'),
            'tfpu_clkdiv_reg': re.compile(r'TFPU_CLKDIV寄存器:\s*(.+)'),
            'prescaler': re.compile(r'预分频系数:\s*(.+)'),
            'calc_frequency': re.compile(r'计算频率:\s*(.+)'),
            'cpu_freq_ratio': re.compile(r'与CPU频率比:\s*(.+)'),
            'key_registers': re.compile(r'关键寄存器状态:'),
            'clksel_reg': re.compile(r'CLKSEL寄存器:\s*(.+)'),
            'usbclk_reg': re.compile(r'USBCLK寄存器:\s*(.+)'),
            't4t3m_reg': re.compile(r'T4T3M寄存器:\s*(.+)'),
            'dmair_reg': re.compile(r'DMAIR寄存器:\s*(.+)'),
            'conclusion': re.compile(r'结论:'),
            'tfpu_freq_verification': re.compile(r'TFPU运行在(.+)\s*\(需要进一步验证\)'),
            'tfpu_freq_conclusion': re.compile(r'TFPU运行在约(.+)\s*\(PLL时钟源，\d+分频\)'),
            'performance_header': re.compile(r'AI8051U 硬件加速性能基准测试'),
            'tfpu_status_check': re.compile(r'TFPU状态检查完成'),
            'mdu32_perf_header': re.compile(r'MDU32性能基准测试:'),
            'mdu32_multiply_avg': re.compile(r'乘法平均:\s*([\d.]+)\s*时钟周期/次'),
            'mdu32_multiply_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'mdu32_divide_avg': re.compile(r'除法平均:\s*([\d.]+)\s*时钟周期/次'),
            'mdu32_divide_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'tfpu_perf_header': re.compile(r'TFPU性能基准测试:'),
            'timing_warning': re.compile(r'\[计时异常\]\s*开始:(\d+)\s*结束:(\d+)\s*差值:(\d+)'),
            'warning_skip': re.compile(r'警告:\s*(.+)\s*第\d+轮测试计时异常，已跳过'),
            'tfpu_add_avg': re.compile(r'加法平均:\s*([\d.]+)\s*时钟周期/次'),
            'tfpu_add_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'tfpu_multiply_avg': re.compile(r'乘法平均:\s*([\d.]+)\s*时钟周期/次'),
            'tfpu_multiply_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'tfpu_divide_avg': re.compile(r'除法平均:\s*([\d.]+)\s*时钟周期/次'),
            'tfpu_divide_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'tfpu_sin_avg': re.compile(r'正弦平均:\s*([\d.]+)\s*时钟周期/次'),
            'tfpu_sin_ratio': re.compile(r'硬件加速比:\s*([\d.]+)x\s*\(理论\d+周期\)'),
            'hardware_state': re.compile(r'硬件状态:'),
            'tfpu_clock_source': re.compile(r'TFPU时钟源:\s*(.+)'),
            'cpu_clock_source': re.compile(r'CPU时钟:\s*(.+)'),
            'acceleration_ratio': re.compile(r'加速比:\s*(.+)'),
            'power_management': re.compile(r'功耗管理:\s*(.+)')
        }
    
    def _direct_parse_message(self, message: str) -> bool:
        """直接解析消息，不依赖正则表达式"""
        updated = False
        
        # 按行处理消息
        lines = message.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 直接匹配关键信息
            if '微控制器:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    mcu = parts[1].strip()
                    self.device_info['system']['mcu'] = mcu
                    if self.debug_mode:
                        debug_log(f"直接解析MCU: {mcu}", "DeviceInfoManager")
                    updated = True
            
            elif '时钟频率:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    freq = parts[1].strip()
                    self.device_info['system']['clock_frequency'] = freq
                    self.device_info['system']['clock'] = freq
                    self.device_info['system']['cpu_clock'] = freq
                    self.device_info['performance']['cpu_frequency'] = freq
                    
                    # 尝试提取TFPU频率
                    if 'TFPU:' in freq or 'tfpu:' in freq.lower():
                        # 简单提取TFPU频率
                        if '(' in freq and ')' in freq:
                            tfpu_part = freq[freq.find('(')+1:freq.find(')')]
                            if 'TFPU:' in tfpu_part:
                                tfpu_freq = tfpu_part.split(':', 1)[1].strip()
                                self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                                self.device_info['performance']['tfpu_enabled'] = True
                    
                    if self.debug_mode:
                        debug_log(f"直接解析时钟频率: {freq}", "DeviceInfoManager")
                    updated = True
            
            elif 'Flash大小:' in line or 'Flash:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    flash = parts[1].strip()
                    self.device_info['system']['flash_size'] = flash
                    self.device_info['system']['flash'] = flash
                    if self.debug_mode:
                        debug_log(f"直接解析Flash: {flash}", "DeviceInfoManager")
                    updated = True
            
            elif 'XRAM大小:' in line or 'XRAM:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    xram = parts[1].strip()
                    self.device_info['system']['xram_size'] = xram
                    self.device_info['system']['xram'] = xram
                    if self.debug_mode:
                        debug_log(f"直接解析XRAM: {xram}", "DeviceInfoManager")
                    updated = True
            
            elif 'USB-CDC:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    usb = parts[1].strip()
                    self.device_info['system']['usb_cdc'] = usb
                    if self.debug_mode:
                        debug_log(f"直接解析USB-CDC: {usb}", "DeviceInfoManager")
                    updated = True
            
            elif 'Flash已用:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    flash_used = parts[1].strip()
                    if 'memory' not in self.device_info:
                        self.device_info['memory'] = {}
                    self.device_info['memory']['flash_used'] = flash_used
                    if self.debug_mode:
                        debug_log(f"直接解析Flash已用: {flash_used}", "DeviceInfoManager")
                    updated = True
            
            elif '内部RAM:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    internal_ram = parts[1].strip()
                    if 'memory' not in self.device_info:
                        self.device_info['memory'] = {}
                    self.device_info['memory']['internal_ram'] = internal_ram
                    if self.debug_mode:
                        debug_log(f"直接解析内部RAM: {internal_ram}", "DeviceInfoManager")
                    updated = True
            
            elif '当前时间:' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    rtc_time = parts[1].strip()
                    self.device_info['status']['rtc_time'] = rtc_time
                    self.device_info['system']['rtc'] = rtc_time  # 同时设置system.rtc字段
                    if self.debug_mode:
                        debug_log(f"直接解析RTC时间: {rtc_time}", "DeviceInfoManager")
                    updated = True
        
        return updated
        
    def parse_message(self, message: str) -> bool:
        """解析消息并更新设备信息（带超时保护和去重机制）"""
        start_time = time.time()
        updated = False
        current_time = time.time()
        
        # 消息处理超时保护 - 最多处理5秒
        max_processing_time = 5.0
        
        # 调试信息
        if "微控制器" in message or "时钟频率" in message or "Flash" in message:
            debug_log(f"解析设备信息: {message.strip()}", "DeviceInfoManager")
        
        # 检查处理时间
        if time.time() - start_time > max_processing_time:
            if self.debug_mode:
                debug_log(f"消息处理超时，跳过: {message[:50]}...", "DeviceInfoManager")
            return False
        
        # 直接解析各种信息，不使用模式
        
        # 增强的直接解析逻辑 - 不依赖正则表达式
        updated = self._direct_parse_message(message) or updated
        
        # 解析UI显示格式的设备信息
        if '=== AI8051U 设备信息 ===' in message:
            # 标记进入UI设备信息解析模式
            self.device_info['status']['ui_device_info_mode'] = True
            if self.debug_mode:
                debug_log(f"进入UI设备信息解析模式", "DeviceInfoManager")
            updated = True
        
        # 解析UI设备信息模式中的具体信息
        elif self.device_info['status'].get('ui_device_info_mode', False):
            # 解析版本信息
            if '版本:' in message and '等待设备信息更新...' not in message:
                version_match = re.search(r'版本[:：]\s*(.+)', message)
                if version_match:
                    version = version_match.group(1).strip()
                    if version and version != '等待设备信息更新...':
                        self.device_info['system']['version'] = version
                        updated = True
                        if self.debug_mode:
                            debug_log(f"UI模式解析到版本信息: {version}", "DeviceInfoManager")
            
            # 解析作者信息
            elif '作者:' in message and '等待设备信息更新...' not in message:
                author_match = re.search(r'作者[:：]\s*(.+)', message)
                if author_match:
                    author = author_match.group(1).strip()
                    if author and author != '等待设备信息更新...':
                        self.device_info['system']['author'] = author
                        updated = True
                        if self.debug_mode:
                            debug_log(f"UI模式解析到作者信息: {author}", "DeviceInfoManager")
            
            # 解析RTC时钟信息
            elif 'RTC时钟:' in message:
                rtc_match = re.search(r'RTC时钟[:：]\s*(.+)', message)
                if rtc_match:
                    rtc_info = rtc_match.group(1).strip()
                    if rtc_info and rtc_info != '未知':
                        self.device_info['system']['rtc'] = rtc_info
                        self.device_info['status']['rtc_time'] = rtc_info
                        updated = True
                        if self.debug_mode:
                            debug_log(f"UI模式解析到RTC时钟: {rtc_info}", "DeviceInfoManager")
            
            # 检查是否结束UI设备信息模式
            elif '【性能数据】' in message or 'MDU32乘法性能:' in message:
                # 性能数据部分，保持模式继续解析
                pass
            elif message.strip() == '' or '===' in message:
                # 空行或新的分隔符表示结束
                self.device_info['status']['ui_device_info_mode'] = False
                if self.debug_mode:
                    debug_log(f"退出UI设备信息解析模式", "DeviceInfoManager")
        
        # 解析系统信息
        if self.patterns['system_info'].search(message):
            self.device_info['status']['system_info_mode'] = True
            self.mode_start_time['system_info_mode'] = current_time
            if self.debug_mode:
                debug_log(f"进入系统信息解析模式: {message.strip()}", "DeviceInfoManager")
            updated = True
        
        # 解析2.0.5版本的启动信息中的硬件加速配置
        if '硬件加速:' in message and 'MDU32' in message and 'TFPU' in message:
            parts = message.split(':', 1)
            if len(parts) > 1:
                hw_info = parts[1].strip()
                self.device_info['system']['hw_acceleration'] = hw_info
                # 解析MDU32和TFPU状态
                if 'MDU32' in hw_info:
                    self.device_info['hardware']['mdu32']['status'] = '已启用'
                    # 提取MDU32详细信息
                    mdu32_detail = re.search(r'MDU32\(([^)]+)\)', hw_info)
                    if mdu32_detail:
                        self.device_info['hardware']['mdu32']['description'] = mdu32_detail.group(1).strip()
                if 'TFPU' in hw_info:
                    self.device_info['hardware']['tfpu']['status'] = '已启用'
                    # 提取TFPU详细信息
                    tfpu_detail = re.search(r'TFPU\(([^)]+)\)', hw_info)
                    if tfpu_detail:
                        self.device_info['hardware']['tfpu']['description'] = tfpu_detail.group(1).strip()
                updated = True
        
        # 直接解析各种信息
        if self.patterns['mcu'].search(message):
            match = self.patterns['mcu'].search(message)
            self.device_info['system']['mcu'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到MCU信息: {match.group(1).strip()}")
            updated = True
        elif self.patterns['system_mcu'].search(message):
            match = self.patterns['system_mcu'].search(message)
            self.device_info['system']['mcu'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到MCU信息(新格式): {match.group(1).strip()}")
            updated = True
            
        if self.patterns['clock'].search(message):
            match = self.patterns['clock'].search(message)
            freq = match.group(1).strip()
            self.device_info['system']['clock_frequency'] = freq
            self.device_info['system']['clock'] = freq  # 兼容性字段
            # 同时更新CPU频率
            self.device_info['system']['cpu_clock'] = freq
            # 更新性能信息中的CPU频率
            self.device_info['performance']['cpu_frequency'] = freq
            # 尝试从时钟频率中提取TFPU频率
            if 'TFPU:' in freq or 'tfpu:' in freq.lower():
                tfpu_match = re.search(r'\(?TFPU[:\s]*([\d\.]+MHz)\)?', freq, re.IGNORECASE)
                if tfpu_match:
                    tfpu_freq = tfpu_match.group(1).strip()
                    self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                    self.device_info['performance']['tfpu_enabled'] = True
            if self.debug_mode:
                print(f"[DEBUG] 解析到时钟频率: {freq}")
            updated = True
        elif self.patterns['system_clock'].search(message):
            match = self.patterns['system_clock'].search(message)
            freq = match.group(1).strip()
            self.device_info['system']['clock_frequency'] = freq
            self.device_info['system']['clock'] = freq  # 兼容性字段
            # 同时更新CPU频率
            self.device_info['system']['cpu_clock'] = freq
            # 更新性能信息中的CPU频率
            self.device_info['performance']['cpu_frequency'] = freq
            # 尝试从时钟频率中提取TFPU频率
            if 'TFPU:' in freq or 'tfpu:' in freq.lower():
                tfpu_match = re.search(r'\(?TFPU[:\s]*([\d\.]+MHz)\)?', freq, re.IGNORECASE)
                if tfpu_match:
                    tfpu_freq = tfpu_match.group(1).strip()
                    self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                    self.device_info['performance']['tfpu_enabled'] = True
            if self.debug_mode:
                print(f"[DEBUG] 解析到时钟频率(新格式): {freq}")
            updated = True
            
        if self.patterns['flash'].search(message):
            match = self.patterns['flash'].search(message)
            size = match.group(1).strip()
            self.device_info['system']['flash_size'] = size
            self.device_info['system']['flash'] = size  # 兼容性字段
            if self.debug_mode:
                print(f"[DEBUG] 解析到Flash大小: {size}")
            updated = True
        elif self.patterns['system_flash'].search(message):
            match = self.patterns['system_flash'].search(message)
            size = match.group(1).strip()
            self.device_info['system']['flash_size'] = size
            self.device_info['system']['flash'] = size  # 兼容性字段
            if self.debug_mode:
                print(f"[DEBUG] 解析到Flash大小(新格式): {size}")
            updated = True
            
        if self.patterns['xram'].search(message):
            match = self.patterns['xram'].search(message)
            size = match.group(1).strip()
            self.device_info['system']['xram_size'] = size
            self.device_info['system']['xram'] = size  # 兼容性字段
            if self.debug_mode:
                print(f"[DEBUG] 解析到XRAM大小: {size}")
            updated = True
        elif self.patterns['system_xram'].search(message):
            match = self.patterns['system_xram'].search(message)
            size = match.group(1).strip()
            self.device_info['system']['xram_size'] = size
            self.device_info['system']['xram'] = size  # 兼容性字段
            if self.debug_mode:
                print(f"[DEBUG] 解析到XRAM大小(新格式): {size}")
            updated = True
            
        if self.patterns['usb_cdc'].search(message):
            match = self.patterns['usb_cdc'].search(message)
            self.device_info['system']['usb_cdc'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到USB-CDC状态: {match.group(1).strip()}")
            updated = True
        elif self.patterns['system_usb_cdc'].search(message):
            match = self.patterns['system_usb_cdc'].search(message)
            self.device_info['system']['usb_cdc'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到USB-CDC状态(新格式): {match.group(1).strip()}")
            updated = True
            
        if self.patterns['build_date'].search(message):
            match = self.patterns['build_date'].search(message)
            self.device_info['system']['build_date'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到编译日期: {match.group(1).strip()}")
            updated = True
            
        if self.patterns['build_time'].search(message):
            match = self.patterns['build_time'].search(message)
            self.device_info['system']['build_time'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到编译时间: {match.group(1).strip()}")
            updated = True
            
        if self.patterns['rtc_time'].search(message):
            match = self.patterns['rtc_time'].search(message)
            self.device_info['status']['rtc_time'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到RTC时间: {match.group(1).strip()}")
            updated = True
            
        if self.patterns['flash_constants'].search(message):
            try:
                match = self.patterns['flash_constants'].search(message)
                if match and 'memory' in self.device_info:
                    self.device_info['memory']['flash_constants'] = match.group(1).strip()
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到常量存储: {match.group(1).strip()}")
                    updated = True
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 解析常量存储失败: {e}")
        
        # 检查系统信息模式是否应该结束
        if self.device_info['status'].get('system_info_mode', False):
            # 更灵活的结束条件：如果收到内存使用信息、RTC时间信息或空行，说明系统信息解析完成
            if ('Flash已用:' in message or '内部RAM:' in message or '当前时间:' in message or 
                '内存使用:' in message or message.strip() == '' or '终端> ' in message):
                self.device_info['status']['system_info_mode'] = False
                if self.debug_mode:
                    print(f"[DEBUG] 系统信息解析模式结束: {message.strip()}")
                updated = True
                
                # 总是更新时间戳，无论设备信息是否有变化
                try:
                    self.device_info['status']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] 更新状态时间失败: {e}")
                
                # 更智能的去重检查 - 分别处理内容和时间戳
                current_info_hash = self._calculate_device_info_hash()
                current_time = time.time()
                
                # 计算内容哈希（用于内容去重）
                content_fingerprint = self._generate_content_fingerprint(current_info_hash)
                
                # 内容去重检查（更短窗口，避免重复内容）
                content_is_duplicate = False
                if (self.last_content_hash == content_fingerprint and 
                    current_time - self.last_update_time <= self.content_dedup_window):
                    content_is_duplicate = True
                
                # 检查是否需要发送更新信号
                should_emit = False
                update_reason = ""
                
                if current_info_hash != self.last_device_info_hash:
                    # 设备信息内容发生变化
                    should_emit = True
                    update_reason = "内容变化"
                elif current_time - self.last_update_time > self.dedup_window:
                    # 时间戳窗口过期，允许更新
                    should_emit = True
                    update_reason = "时间戳窗口过期"
                elif not content_is_duplicate:
                    # 内容不重复，允许更新
                    should_emit = True
                    update_reason = "内容不重复"
                
                # 总是更新时间戳和状态
                self.last_device_info_hash = current_info_hash
                self.last_content_hash = content_fingerprint
                self.last_update_time = current_time
                
                # 根据条件发送更新信号
                if should_emit:
                    self._safe_emit_device_info_update()
                    if self.debug_mode:
                        print(f"[DEBUG] 设备信息已更新（{update_reason}），哈希: {current_info_hash[:8]}...")
                else:
                    # 只更新时间戳，不发送完整的设备信息更新信号
                    if self.debug_mode:
                        print(f"[DEBUG] 设备信息未变化，但时间戳已更新")
                
                updated = True  # 确保总是返回True，表示设备信息已被处理
                return updated  # 提前返回，避免重复处理
        
        # 解析硬件测试信息
        if '硬件加速单元测试' in message:
            self.device_info['status']['hardware_test_mode'] = True
            self.mode_start_time['hardware_test_mode'] = current_time
            self.device_info['hardware']['mdu32']['status'] = '测试中'
            self.device_info['hardware']['tfpu']['status'] = '测试中'
            updated = True
            
        elif self.device_info['status'].get('hardware_test_mode', False):
            if 'MDU32硬件乘除单元测试:' in message:
                self.device_info['hardware']['mdu32']['status'] = '测试中'
                updated = True
            elif 'TFPU浮点运算单元测试:' in message:
                self.device_info['hardware']['tfpu']['status'] = '测试中'
                updated = True
            elif self.patterns['mdu32_multiply'].search(message):
                match = self.patterns['mdu32_multiply'].search(message)
                self.device_info['hardware']['mdu32']['multiply_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['mdu32_multiply_time'].search(message):
                match = self.patterns['mdu32_multiply_time'].search(message)
                self.device_info['hardware']['mdu32']['multiply_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['mdu32_multiply_ratio'].search(message):
                match = self.patterns['mdu32_multiply_ratio'].search(message)
                self.device_info['hardware']['mdu32']['multiply_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['mdu32_divide'].search(message):
                match = self.patterns['mdu32_divide'].search(message)
                self.device_info['hardware']['mdu32']['divide_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['mdu32_divide_time'].search(message):
                match = self.patterns['mdu32_divide_time'].search(message)
                self.device_info['hardware']['mdu32']['divide_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['mdu32_divide_ratio'].search(message):
                match = self.patterns['mdu32_divide_ratio'].search(message)
                self.device_info['hardware']['mdu32']['divide_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_add'].search(message):
                match = self.patterns['tfpu_add'].search(message)
                self.device_info['hardware']['tfpu']['add_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_add_time'].search(message):
                match = self.patterns['tfpu_add_time'].search(message)
                self.device_info['hardware']['tfpu']['add_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_add_ratio'].search(message):
                match = self.patterns['tfpu_add_ratio'].search(message)
                self.device_info['hardware']['tfpu']['add_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_multiply'].search(message):
                match = self.patterns['tfpu_multiply'].search(message)
                self.device_info['hardware']['tfpu']['multiply_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_multiply_time'].search(message):
                match = self.patterns['tfpu_multiply_time'].search(message)
                self.device_info['hardware']['tfpu']['multiply_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_multiply_ratio'].search(message):
                match = self.patterns['tfpu_multiply_ratio'].search(message)
                self.device_info['hardware']['tfpu']['multiply_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sin'].search(message):
                match = self.patterns['tfpu_sin'].search(message)
                self.device_info['hardware']['tfpu']['sin_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sin_time'].search(message):
                match = self.patterns['tfpu_sin_time'].search(message)
                self.device_info['hardware']['tfpu']['sin_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sin_ratio'].search(message):
                match = self.patterns['tfpu_sin_ratio'].search(message)
                self.device_info['hardware']['tfpu']['sin_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_cos'].search(message):
                match = self.patterns['tfpu_cos'].search(message)
                self.device_info['hardware']['tfpu']['cos_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_cos_time'].search(message):
                match = self.patterns['tfpu_cos_time'].search(message)
                self.device_info['hardware']['tfpu']['cos_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_cos_ratio'].search(message):
                match = self.patterns['tfpu_cos_ratio'].search(message)
                self.device_info['hardware']['tfpu']['cos_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sqrt'].search(message):
                match = self.patterns['tfpu_sqrt'].search(message)
                self.device_info['hardware']['tfpu']['sqrt_result'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sqrt_time'].search(message):
                match = self.patterns['tfpu_sqrt_time'].search(message)
                self.device_info['hardware']['tfpu']['sqrt_time'] = match.group(1).strip()
                updated = True
            elif self.patterns['tfpu_sqrt_ratio'].search(message):
                match = self.patterns['tfpu_sqrt_ratio'].search(message)
                self.device_info['hardware']['tfpu']['sqrt_ratio'] = match.group(1).strip()
                updated = True
            elif self.patterns['hardware_status'].search(message):
                self.device_info['status']['hardware_test_mode'] = False
                self.device_info['hardware']['mdu32']['status'] = '完成'
                self.device_info['hardware']['tfpu']['status'] = '完成'
                updated = True
                self._safe_emit_device_info_update()
        # 解析时钟信息 (2.0.5版本新增)
        elif self.v205_patterns['clock_info_header'].search(message):
            self.device_info['status']['clock_info_mode'] = True
            updated = True
        elif self.device_info['status'].get('clock_info_mode', False):
            # 确保clock_system字典存在
            if 'clock_system' not in self.device_info:
                self.device_info['clock_system'] = {
                    'system_clock': '',
                    'pll_output_clock': '',
                    'high_speed_peripheral_clock': '',
                    'tfpu_clock_divider': '',
                    'prescaler_coefficient': '',
                    'calculated_frequency': '',
                    'cpu_frequency_ratio': '',
                    'clksel_register': '',
                    'usbclk_register': '',
                    't4t3m_register': '',
                    'dmair_register': '',
                    'tfpu_frequency_verification': '',
                    'conclusion': ''
                }
            if self.v205_patterns['system_clock_config'].search(message):
                updated = True
            elif self.v205_patterns['sys_clock'].search(message):
                match = self.v205_patterns['sys_clock'].search(message)
                self.device_info['clock_system']['system_clock'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['pll_output'].search(message):
                match = self.v205_patterns['pll_output'].search(message)
                # 处理两种格式的PLL输出时钟信息
                if match.group(1):
                    self.device_info['clock_system']['pll_output_clock'] = match.group(1).strip()
                elif match.group(2):
                    self.device_info['clock_system']['pll_output_clock'] = match.group(2).strip()
                updated = True
            elif self.v205_patterns['high_speed_peripheral'].search(message):
                match = self.v205_patterns['high_speed_peripheral'].search(message)
                self.device_info['clock_system']['high_speed_peripheral_clock'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['tfpu_clkdiv_reg'].search(message):
                match = self.v205_patterns['tfpu_clkdiv_reg'].search(message)
                self.device_info['clock_system']['tfpu_clock_divider'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['prescaler'].search(message):
                match = self.v205_patterns['prescaler'].search(message)
                self.device_info['clock_system']['prescaler_coefficient'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['calc_frequency'].search(message):
                match = self.v205_patterns['calc_frequency'].search(message)
                self.device_info['clock_system']['calculated_frequency'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['cpu_freq_ratio'].search(message):
                match = self.v205_patterns['cpu_freq_ratio'].search(message)
                self.device_info['clock_system']['cpu_frequency_ratio'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['clksel_reg'].search(message):
                match = self.v205_patterns['clksel_reg'].search(message)
                self.device_info['clock_system']['clksel_register'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['usbclk_reg'].search(message):
                match = self.v205_patterns['usbclk_reg'].search(message)
                self.device_info['clock_system']['usbclk_register'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['t4t3m_reg'].search(message):
                match = self.v205_patterns['t4t3m_reg'].search(message)
                self.device_info['clock_system']['t4t3m_register'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['dmair_reg'].search(message):
                match = self.v205_patterns['dmair_reg'].search(message)
                self.device_info['clock_system']['dmair_register'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['tfpu_freq_verification'].search(message):
                match = self.v205_patterns['tfpu_freq_verification'].search(message)
                self.device_info['clock_system']['tfpu_frequency_verification'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['tfpu_freq_conclusion'].search(message):
                match = self.v205_patterns['tfpu_freq_conclusion'].search(message)
                self.device_info['clock_system']['tfpu_frequency_verification'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['conclusion'].search(message):
                self.device_info['status']['clock_info_mode'] = False
                updated = True
                self._safe_emit_device_info_update()
                
        # 解析详细性能基准测试 (2.0.5版本新增)
        elif self.v205_patterns['performance_header'].search(message):
            self.device_info['status']['performance_mode'] = True
            self.device_info['current_test_unit'] = ''
            updated = True
        elif self.device_info['status'].get('performance_mode', False):
            # 确保performance字典存在
            if 'performance' not in self.device_info:
                self.device_info['performance'] = {
                    'mdu32_multiply_perf': '',
                    'mdu32_multiply_avg': '',
                    'mdu32_multiply_ratio': '',
                    'mdu32_divide_perf': '',
                    'mdu32_divide_avg': '',
                    'mdu32_divide_ratio': '',
                    'tfpu_add_perf': '',
                    'tfpu_add_avg': '',
                    'tfpu_add_ratio': '',
                    'tfpu_add_time': '',
                    'tfpu_multiply_perf': '',
                    'tfpu_multiply_avg': '',
                    'tfpu_multiply_ratio': '',
                    'tfpu_multiply_time': '',
                    'tfpu_divide_avg': '',
                    'tfpu_divide_ratio': '',
                    'tfpu_sin_avg': '',
                    'tfpu_sin_ratio': '',
                    'tfpu_sin_time': '',
                    'tfpu_sqrt_time': '',
                    'tfpu_cos_time': '',
                    'benchmark_completed': False,
                    'last_warning': '',
                    'timing_warnings': []
                }
            if self.v205_patterns['timing_warning'].search(message):
                match = self.v205_patterns['timing_warning'].search(message)
                warning_info = {
                    'start': match.group(1),
                    'end': match.group(2),
                    'diff': match.group(3)
                }
                self.device_info['performance']['timing_warnings'].append(warning_info)
                updated = True
            elif 'MDU32性能基准测试:' in message:
                self.device_info['current_test_unit'] = 'MDU32'
                updated = True
            elif 'TFPU性能基准测试:' in message:
                self.device_info['current_test_unit'] = 'TFPU'
                updated = True
            elif self.v205_patterns['warning_skip'].search(message):
                match = self.v205_patterns['warning_skip'].search(message)
                self.device_info['performance']['last_warning'] = match.group(1).strip()
                updated = True
            elif '乘法平均:' in message and '时钟周期/次' in message and self.device_info['status'].get('performance_mode', False):
                match = re.search(r'乘法平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    # 判断是MDU32还是TFPU的乘法平均
                    if 'MDU32' in str(self.device_info.get('current_test_unit', '')):
                        self.device_info['performance']['mdu32_multiply_avg'] = f"{match.group(1)}时钟周期/次"
                    else:
                        self.device_info['performance']['tfpu_multiply_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '硬件加速比:' in message and 'x' in message and self.device_info['status'].get('performance_mode', False):
                match = re.search(r'硬件加速比: ([\d.]+)x', message)
                if match:
                    # 判断是MDU32还是TFPU的加速比
                    current_unit = str(self.device_info.get('current_test_unit', ''))
                    if 'MDU32' in current_unit:
                        if self._check_performance_ratio('mdu32_multiply', 'mdu32_multiply_ratio'):
                            self.device_info['performance']['mdu32_multiply_ratio'] = f"{match.group(1)}x"
                        elif not self.device_info['performance'].get('mdu32_divide_ratio'):
                            self.device_info['performance']['mdu32_divide_ratio'] = f"{match.group(1)}x"
                    elif 'TFPU' in current_unit:
                        if self.device_info['performance'].get('tfpu_add_avg') and not self.device_info['performance'].get('tfpu_add_ratio'):
                            self.device_info['performance']['tfpu_add_ratio'] = f"{match.group(1)}x"
                        elif self._check_performance_ratio('tfpu_multiply', 'tfpu_multiply_ratio'):
                            self.device_info['performance']['tfpu_multiply_ratio'] = f"{match.group(1)}x"
                        elif not self.device_info['performance'].get('tfpu_sin_ratio'):
                            self.device_info['performance']['tfpu_sin_ratio'] = f"{match.group(1)}x"
                    updated = True
            elif '除法平均:' in message and '时钟周期/次' in message and self.device_info['status'].get('performance_mode', False):
                match = re.search(r'除法平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    self.device_info['performance']['mdu32_divide_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '加法平均:' in message and '时钟周期/次' in message and self.device_info['status'].get('performance_mode', False):
                match = re.search(r'加法平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    self.device_info['performance']['tfpu_add_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '正弦平均:' in message and '时钟周期/次' in message and self.device_info['status'].get('performance_mode', False):
                match = re.search(r'正弦平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    self.device_info['performance']['tfpu_sin_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif self.v205_patterns['tfpu_multiply_avg'].search(message):
                match = self.v205_patterns['tfpu_multiply_avg'].search(message)
                self.device_info['performance']['tfpu_multiply_avg'] = f"{match.group(1)}时钟周期/次"
                updated = True
            elif self.v205_patterns['tfpu_multiply_ratio'].search(message):
                match = self.v205_patterns['tfpu_multiply_ratio'].search(message)
                self.device_info['performance']['tfpu_multiply_ratio'] = f"{match.group(1)}x"
                updated = True
            elif self.v205_patterns['tfpu_divide_avg'].search(message):
                match = self.v205_patterns['tfpu_divide_avg'].search(message)
                self.device_info['performance']['tfpu_divide_avg'] = f"{match.group(1)}时钟周期/次"
                updated = True
            elif self.v205_patterns['tfpu_divide_ratio'].search(message):
                match = self.v205_patterns['tfpu_divide_ratio'].search(message)
                self.device_info['performance']['tfpu_divide_ratio'] = f"{match.group(1)}x"
                updated = True
            elif self.v205_patterns['tfpu_sin_avg'].search(message):
                match = self.v205_patterns['tfpu_sin_avg'].search(message)
                self.device_info['performance']['tfpu_sin_avg'] = f"{match.group(1)}时钟周期/次"
                updated = True
            elif self.v205_patterns['tfpu_sin_ratio'].search(message):
                match = self.v205_patterns['tfpu_sin_ratio'].search(message)
                self.device_info['performance']['tfpu_sin_ratio'] = f"{match.group(1)}x"
                updated = True
            elif self.v205_patterns['tfpu_clock_source'].search(message):
                match = self.v205_patterns['tfpu_clock_source'].search(message)
                self.device_info['system']['tfpu_clock'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['cpu_clock_source'].search(message):
                match = self.v205_patterns['cpu_clock_source'].search(message)
                self.device_info['system']['cpu_clock'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['acceleration_ratio'].search(message):
                match = self.v205_patterns['acceleration_ratio'].search(message)
                self.device_info['system']['acceleration_ratio'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['power_management'].search(message):
                match = self.v205_patterns['power_management'].search(message)
                self.device_info['system']['power_management'] = match.group(1).strip()
                updated = True
            elif '性能基准测试完成！' in message:
                self.device_info['status']['performance_mode'] = False
                self.device_info['performance']['benchmark_completed'] = True
                updated = True
                self._safe_emit_device_info_update()
                
        # 解析性能数据
        elif '性能基准测试:' in message:
            self.device_info['status']['performance_mode'] = True
            updated = True
        
        # 性能数据解析 - 独立的条件检查
        if self.device_info['status'].get('performance_mode', False):
            # 确保performance字典存在
            if 'performance' not in self.device_info:
                self.device_info['performance'] = {
                    'mdu32_multiply_perf': '',
                    'mdu32_multiply_avg': '',
                    'mdu32_multiply_ratio': '',
                    'mdu32_divide_perf': '',
                    'mdu32_divide_avg': '',
                    'mdu32_divide_ratio': '',
                    'tfpu_add_perf': '',
                    'tfpu_add_avg': '',
                    'tfpu_add_ratio': '',
                    'tfpu_add_time': '',
                    'tfpu_multiply_perf': '',
                    'tfpu_multiply_avg': '',
                    'tfpu_multiply_ratio': '',
                    'tfpu_multiply_time': '',
                    'tfpu_divide_avg': '',
                    'tfpu_divide_ratio': '',
                    'tfpu_sin_avg': '',
                    'tfpu_sin_ratio': '',
                    'tfpu_sin_time': '',
                    'tfpu_sqrt_time': '',
                    'tfpu_cos_time': '',
                    'benchmark_completed': False,
                    'last_warning': '',
                    'timing_warnings': []
                }
            
            # 解析性能数据
            if '乘法性能:' in message:
                match = re.search(r'乘法性能: (\d+)次运算耗时 (\d+) 时钟周期', message)
                if match:
                    self.device_info['performance']['mdu32_multiply_perf'] = f"{match.group(2)}时钟周期/{match.group(1)}次"
                    updated = True
            elif '平均每次:' in message:
                match = re.search(r'平均每次: ([\d.]+) 时钟周期', message)
                if match:
                    # 根据上下文判断是乘法还是除法平均
                    if self.device_info['performance'].get('mdu32_multiply_perf') and not self.device_info['performance'].get('mdu32_multiply_avg'):
                        self.device_info['performance']['mdu32_multiply_avg'] = f"{match.group(1)}时钟周期/次"
                    elif self.device_info['performance'].get('mdu32_divide_perf') and not self.device_info['performance'].get('mdu32_divide_avg'):
                        self.device_info['performance']['mdu32_divide_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '加法性能:' in message:
                match = re.search(r'加法性能: (\d+)次运算耗时 (\d+) 时钟周期', message)
                if match:
                    self.device_info['performance']['tfpu_add_perf'] = f"{match.group(2)}时钟周期/{match.group(1)}次"
                    updated = True
            elif '除法性能:' in message:
                match = re.search(r'除法性能: (\d+)次运算耗时 (\d+) 时钟周期', message)
                if match:
                    self.device_info['performance']['mdu32_divide_perf'] = f"{match.group(2)}时钟周期/{match.group(1)}次"
                    updated = True
            elif '乘法平均:' in message and '时钟周期/次' in message:
                match = re.search(r'乘法平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    self.device_info['performance']['tfpu_multiply_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '正弦平均:' in message and '时钟周期/次' in message:
                match = re.search(r'正弦平均: ([\d.]+) 时钟周期/次', message)
                if match:
                    self.device_info['performance']['tfpu_sin_avg'] = f"{match.group(1)}时钟周期/次"
                    updated = True
            elif '性能基准测试完成！' in message:
                self.device_info['status']['performance_mode'] = False
                self.device_info['performance']['benchmark_completed'] = True
                updated = True
                self._safe_emit_device_info_update()
                
        # 解析电压信息
        elif '电源电压测量结果:' in message:
            self.device_info['status']['voltage_mode'] = True
            updated = True
        elif self.device_info['status'].get('voltage_mode', False):
            if self.patterns['voltage'].search(message):
                match = self.patterns['voltage'].search(message)
                self.device_info['hardware']['adc']['voltage'] = match.group(1).strip()
                updated = True
            elif self.patterns['voltage_raw'].search(message):
                match = self.patterns['voltage_raw'].search(message)
                self.device_info['hardware']['adc']['raw_value'] = match.group(1).strip()
                updated = True
            elif self.patterns['voltage_channel'].search(message):
                match = self.patterns['voltage_channel'].search(message)
                self.device_info['hardware']['adc']['channel'] = match.group(1).strip()
                updated = True
            elif self.patterns['voltage_reference'].search(message):
                match = self.patterns['voltage_reference'].search(message)
                self.device_info['hardware']['adc']['reference'] = match.group(1).strip()
                updated = True
            elif self.patterns['voltage_resolution'].search(message):
                match = self.patterns['voltage_resolution'].search(message)
                self.device_info['hardware']['adc']['resolution'] = match.group(1).strip()
                updated = True
            elif self.patterns['voltage_samples'].search(message):
                match = self.patterns['voltage_samples'].search(message)
                self.device_info['hardware']['adc']['samples'] = match.group(1).strip()
                updated = True
            elif message.strip() == '终端> ':
                self.device_info['status']['voltage_mode'] = False
                updated = True
                self._safe_emit_device_info_update()
                
        # 解析内存使用信息 - 增强版本（带异常处理）
        elif '内存使用:' in message:
            try:
                self.device_info['status']['memory_mode'] = True
                updated = True
                if self.debug_mode:
                    print(f"[DEBUG] 进入内存使用解析模式")
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 设置内存模式失败: {e}")
        elif (self.device_info['status'].get('memory_mode', False) or 
              '内存使用:' in message or 'Flash已用:' in message or 
              'XRAM已用:' in message or '内部RAM:' in message):
            try:
                # 确保 memory 字段存在
                if 'memory' not in self.device_info:
                    self.device_info['memory'] = {
                        'flash_used': '',
                        'flash_constants': '',
                        'xram_used': '',
                        'internal_ram_used': ''
                    }
                
                if self.patterns['flash_used'].search(message):
                    match = self.patterns['flash_used'].search(message)
                    if match:
                        self.device_info['memory']['flash_used'] = match.group(1).strip()
                        if self.debug_mode:
                            print(f"[DEBUG] 解析到Flash已用: {match.group(1).strip()}")
                        updated = True
                elif self.patterns['xram_used'].search(message):
                    match = self.patterns['xram_used'].search(message)
                    if match:
                        self.device_info['memory']['xram_used'] = match.group(1).strip()
                        if self.debug_mode:
                            print(f"[DEBUG] 解析到XRAM已用: {match.group(1).strip()}")
                        updated = True
                elif self.patterns['internal_ram'].search(message):
                    match = self.patterns['internal_ram'].search(message)
                    if match:
                        self.device_info['memory']['internal_ram_used'] = match.group(1).strip()
                        if self.debug_mode:
                            print(f"[DEBUG] 解析到内部RAM: {match.group(1).strip()}")
                        updated = True
                elif '常量存储:' in message:
                    # 解析常量存储信息
                    parts = message.split(':', 1)  # 只分割第一个冒号
                    if len(parts) > 1:
                        self.device_info['memory']['flash_constants'] = parts[1].strip()
                        if self.debug_mode:
                            print(f"[DEBUG] 解析到常量存储: {parts[1].strip()}")
                        updated = True
                # 检查内存信息是否结束
                elif (message.strip() == '' or message.strip() == '终端> ' or 
                      (self.device_info.get('memory', {}).get('flash_used') and 
                       self.device_info.get('memory', {}).get('xram_used') and 
                       self.device_info.get('memory', {}).get('internal_ram_used'))):
                    self.device_info['status']['memory_mode'] = False
                    if self.debug_mode:
                        print(f"[DEBUG] 内存使用解析模式结束")
                    updated = True
                    self._safe_emit_device_info_update()
            except (AttributeError, KeyError, IndexError) as e:
                # 特定异常不需要打印，避免噪音
                if self.debug_mode:
                    print(f"[DEBUG] 内存信息解析轻微错误: {type(e).__name__}")
                # 不重置内存模式，继续解析下一条消息
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] 解析内存信息失败: {e}")
                # 发生错误时重置内存模式
                try:
                    self.device_info['status']['memory_mode'] = False
                except:
                    pass
                
        # 解析neofetch信息
        # 注意：AI8051U氢原子系统现在由system_startup_mode处理
        # 不再使用neofetch_system模式检测
        elif self.device_info['status'].get('neofetch_mode', False):
            if self.patterns['neofetch_version'].search(message):
                match = self.patterns['neofetch_version'].search(message)
                self.device_info['system']['version'] = match.group(1).strip()
                updated = True
            elif self.patterns['neofetch_author'].search(message):
                match = self.patterns['neofetch_author'].search(message)
                self.device_info['system']['author'] = match.group(1).strip()
                updated = True
            elif message.strip() == '║系统就绪║':
                self.device_info['status']['neofetch_mode'] = False
                updated = True
                self._safe_emit_device_info_update()
        # 解析reset命令输出中的版本和作者信息
        elif '版本:' in message:
            # 更精确的版本信息解析，支持多种格式
            version_match = re.search(r'版本[:：]\s*(.+)', message)
            if version_match:
                self.device_info['system']['version'] = version_match.group(1).strip()
                updated = True
                if self.debug_mode:
                    print(f"[DEBUG] 解析到版本信息: {self.device_info['system']['version']}")
                # 立即发送更新信号，确保UI同步更新
                self._safe_emit_device_info_update()
        elif '作者:' in message:
            # 更精确的作者信息解析，支持多种格式
            author_match = re.search(r'作者[:：]\s*(.+)', message)
            if author_match:
                self.device_info['system']['author'] = author_match.group(1).strip()
                updated = True
                if self.debug_mode:
                    print(f"[DEBUG] 解析到作者信息: {self.device_info['system']['author']}")
                # 立即发送更新信号，确保UI同步更新
                self._safe_emit_device_info_update()
        elif 'AI8051U氢原子系统' in message:
            self.device_info['system']['system'] = 'AI8051U氢原子系统'
            updated = True
            if self.debug_mode:
                print(f"[DEBUG] 解析到系统名称: AI8051U氢原子系统")
        # 解析reset命令的启动信息
        elif '正在启动' in message or '系统启动' in message:
            # reset命令启动信息，更新时间戳
            self.device_info['status']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated = True
            if self.debug_mode:
                print(f"[DEBUG] 检测到系统启动信息: {message.strip()}")
        
        # 更灵活的版本和作者信息解析
        elif any(keyword in message.lower() for keyword in ['version', 'ver']):
            # 尝试从各种格式中提取版本信息
            version_patterns = [
                r'ver[sion]*[:\s]*([vV]?[\d\.]+[a-zA-Z0-9\-_]*)',
                r'([vV]?[\d\.]+[a-zA-Z0-9\-_]*)',
                r'版本[:\s]*([vV]?[\d\.]+[a-zA-Z0-9\-_]*)'
            ]
            for pattern in version_patterns:
                match = re.search(pattern, message)
                if match:
                    self.device_info['system']['version'] = match.group(1).strip()
                    updated = True
                    print(f"[DEBUG] 灵活解析到版本信息: {self.device_info['system']['version']}")
                    # 立即发送更新信号，确保UI同步更新
                    self._safe_emit_device_info_update()
                    break
        
        elif any(keyword in message.lower() for keyword in ['author', 'by']):
            # 尝试从各种格式中提取作者信息
            author_patterns = [
                r'author[:\s]*([a-zA-Z0-9\u4e00-\u9fff\s]+)',
                r'by[:\s]*([a-zA-Z0-9\u4e00-\u9fff\s]+)',
                r'作者[:\s]*([a-zA-Z0-9\u4e00-\u9fff\s]+)'
            ]
            for pattern in author_patterns:
                match = re.search(pattern, message)
                if match:
                    author = match.group(1).strip()
                    if len(author) > 0 and len(author) < 50:  # 合理的作者名长度
                        self.device_info['system']['author'] = author
                        updated = True
                        print(f"[DEBUG] 灵活解析到作者信息: {self.device_info['system']['author']}")
                        # 立即发送更新信号，确保UI同步更新
                        self._safe_emit_device_info_update()
                        break
                
        # 解析硬件状态信息
        elif self.patterns['tfpu_clock'].search(message):
            match = self.patterns['tfpu_clock'].search(message)
            tfpu_freq = match.group(1).strip()
            self.device_info['system']['tfpu_clock'] = tfpu_freq
            # 更新性能信息中的TFPU频率
            self.device_info['performance']['tfpu_frequency'] = tfpu_freq
            self.device_info['performance']['tfpu_enabled'] = True
            updated = True
        elif self.patterns['cpu_clock'].search(message):
            match = self.patterns['cpu_clock'].search(message)
            cpu_freq = match.group(1).strip()
            self.device_info['system']['cpu_clock'] = cpu_freq
            # 更新性能信息中的CPU频率
            self.device_info['performance']['cpu_frequency'] = cpu_freq
            updated = True
        elif self.patterns['tfpu_clkdiv_reg'].search(message):
            match = self.patterns['tfpu_clkdiv_reg'].search(message)
            self.device_info['system']['tfpu_clkdiv_reg'] = match.group(1).strip()
            if self.debug_mode:
                print(f"[DEBUG] 解析到TFPU_CLKDIV寄存器: {match.group(1).strip()}")
            updated = True
        elif self.patterns['rtc_time'].search(message):
            match = self.patterns['rtc_time'].search(message)
            self.device_info['system']['rtc'] = match.group(1).strip()
            updated = True
        # 解析硬件加速信息（包含版本、作者、编译信息的新格式）
        elif '硬件加速:' in message:
            parts = message.split(':', 1)  # 只分割第一个冒号
            if len(parts) > 1:
                hw_info = parts[1].strip()
                self.device_info['system']['hw_acceleration'] = hw_info
                # 解析MDU32和TFPU状态
                if 'MDU32' in hw_info:
                    self.device_info['hardware']['mdu32']['status'] = '已启用'
                if 'TFPU' in hw_info:
                    self.device_info['hardware']['tfpu']['status'] = '已启用'
                    # 更新性能信息中的TFPU启用状态
                    self.device_info['performance']['tfpu_enabled'] = True
                
                # 设置硬件加速信息
                self.device_info['system']['hw_acceleration'] = hw_info
                updated = True
                if self.debug_mode if hasattr(self, 'debug_mode') else False:
                    print(f"[DEBUG] 解析到硬件加速信息: {self.device_info['system']['hw_acceleration']}")
                    
        # 增强解析：处理reset命令的完整输出格式
        # 格式示例：
        # AI8051U氢原子系统
        # 版本: 2.1.0
        # 作者: 076lik
        # 编译: 2025年12月03日 18:51:45
        # ========================================
        # 系统信息:
        #   CPU时钟: 30MHz (TFPU: 90MHz)
        #   Flash: 64KB
        #   XRAM: 32KB
        #   硬件加速: MDU32(32位乘除单元), TFPU(浮点运算+三角函数)
        elif 'AI8051U氢原子系统' in message:
            # 标记进入系统启动信息解析模式（系统名称在下面的elif块中设置）
            self.device_info['status']['system_startup_mode'] = True
            updated = True
            if self.debug_mode:
                print(f"[DEBUG] 进入系统启动信息解析模式")
                
        elif self.device_info['status'].get('system_startup_mode', False):
            # 解析版本信息
            if '版本:' in message:
                version_match = re.search(r'版本[:：]\s*(.+)', message)
                if version_match:
                    self.device_info['system']['version'] = version_match.group(1).strip()
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到版本信息: {self.device_info['system']['version']}")
            
            # 解析作者信息
            elif '作者:' in message:
                author_match = re.search(r'作者[:：]\s*(.+)', message)
                if author_match:
                    self.device_info['system']['author'] = author_match.group(1).strip()
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到作者信息: {self.device_info['system']['author']}")
            
            # 解析编译信息
            elif '编译:' in message:
                compile_match = re.search(r'编译[:：]\s*(.+)', message)
                if compile_match:
                    compile_info = compile_match.group(1).strip()
                    # 尝试从编译信息中提取日期和时间
                    date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', compile_info)
                    time_match = re.search(r'(\d{1,2}:\d{1,2}:\d{1,2})', compile_info)
                    
                    if date_match:
                        self.device_info['system']['build_date'] = date_match.group(1).strip()
                    if time_match:
                        self.device_info['system']['build_time'] = time_match.group(1).strip()
                    
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到编译信息: {compile_info}")
            
            # 解析CPU时钟信息（可能包含TFPU时钟）
            elif 'CPU时钟:' in message:
                cpu_match = re.search(r'CPU时钟[:：]\s*(.+)', message)
                if cpu_match:
                    cpu_info = cpu_match.group(1).strip()
                    self.device_info['system']['cpu_clock'] = cpu_info
                    # 更新性能信息中的CPU频率
                    self.device_info['performance']['cpu_frequency'] = cpu_info
                    # 尝试从CPU时钟信息中提取TFPU时钟
                    tfpu_match = re.search(r'TFPU[:：]\s*([\d\.]+MHz)', cpu_info)
                    if tfpu_match:
                        tfpu_freq = tfpu_match.group(1).strip()
                        self.device_info['system']['tfpu_clock'] = tfpu_freq
                        # 更新性能信息中的TFPU频率
                        self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                        self.device_info['performance']['tfpu_enabled'] = True
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到CPU时钟信息: {cpu_info}")
            
            # 解析Flash信息
            elif 'Flash:' in message:
                flash_match = re.search(r'Flash[:：]\s*(.+)', message)
                if flash_match:
                    self.device_info['system']['flash_size'] = flash_match.group(1).strip()
                    self.device_info['system']['flash'] = flash_match.group(1).strip()  # 兼容性字段
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到Flash信息: {self.device_info['system']['flash_size']}")
            
            # 解析XRAM信息
            elif 'XRAM:' in message:
                xram_match = re.search(r'XRAM[:：]\s*(.+)', message)
                if xram_match:
                    self.device_info['system']['xram_size'] = xram_match.group(1).strip()
                    self.device_info['system']['xram'] = xram_match.group(1).strip()  # 兼容性字段
                    updated = True
                    if self.debug_mode:
                        print(f"[DEBUG] 解析到XRAM信息: {self.device_info['system']['xram_size']}")
            
            # 检查是否结束系统启动信息解析模式
            # 当遇到分隔线或系统信息结束标志时退出
            elif '========================================' in message or '系统信息:' in message:
                # 继续解析，不退出模式，因为后面还有更多系统信息
                updated = True
            elif '可用命令:' in message or '基础命令:' in message:
                # 遇到命令列表，说明系统信息部分结束
                self.device_info['status']['system_startup_mode'] = False
                updated = True
                # 发送设备信息更新信号
                self._safe_emit_device_info_update()
                if self.debug_mode:
                    print(f"[DEBUG] 系统启动信息解析完成，已发送更新信号")
                    
        # 解析2.0.5版本的硬件状态详细信息
        elif self.v205_patterns['hardware_state'].search(message):
            # 标记进入硬件状态解析模式
            self.device_info['status']['hardware_state_mode'] = True
            updated = True
        elif self.device_info['status'].get('hardware_state_mode', False):
            if self.v205_patterns['tfpu_clock_source'].search(message):
                match = self.v205_patterns['tfpu_clock_source'].search(message)
                tfpu_freq = match.group(1).strip()
                self.device_info['system']['tfpu_clock'] = tfpu_freq
                # 更新TFPU状态为已启用
                self.device_info['hardware']['tfpu']['status'] = '已启用'
                # 更新性能信息中的TFPU频率
                self.device_info['performance']['tfpu_frequency'] = tfpu_freq
                self.device_info['performance']['tfpu_enabled'] = True
                updated = True
            elif self.v205_patterns['cpu_clock_source'].search(message):
                match = self.v205_patterns['cpu_clock_source'].search(message)
                cpu_freq = match.group(1).strip()
                self.device_info['system']['cpu_clock'] = cpu_freq
                # 更新性能信息中的CPU频率
                self.device_info['performance']['cpu_frequency'] = cpu_freq
                updated = True
            elif self.v205_patterns['acceleration_ratio'].search(message):
                match = self.v205_patterns['acceleration_ratio'].search(message)
                self.device_info['system']['acceleration_ratio'] = match.group(1).strip()
                updated = True
            elif self.v205_patterns['power_management'].search(message):
                match = self.v205_patterns['power_management'].search(message)
                self.device_info['system']['power_management'] = match.group(1).strip()
                updated = True
            elif '硬件加速测试完成' in message:
                self.device_info['status']['hardware_state_mode'] = False
                updated = True
                self._safe_emit_device_info_update()
            
        if updated:
            # 添加调试信息
            if hasattr(self, 'debug_mode') and self.debug_mode:
                print(f"[DEBUG] 设备信息已更新: {message[:50]}...")
            # 注意：信号已经在parse_system_info中发送，这里避免重复发送
            if '硬件加速测试完成' in message:
                self._safe_emit_device_info_update()
            
        return updated
        
    def send_info_command(self) -> str:
        """生成info命令"""
        return "info"
        
    def get_formatted_device_info(self) -> str:
        """获取格式化的设备信息"""
        info = []
        info.append("=" * 50)
        info.append("AI8051U 设备系统信息")
        info.append("=" * 50)
        info.append("")
        
        # 系统信息
        info.append("【系统信息】")
        
        # 安全访问系统信息
        try:
            if self.device_info['system'].get('mcu'):
                info.append(f"微控制器: {self.device_info['system']['mcu']}")
            
            # 系统名称
            if self.device_info['system'].get('system'):
                info.append(f"系统名称: {self.device_info['system']['system']}")
            
            # 版本信息
            if self.device_info['system'].get('version'):
                info.append(f"版本: {self.device_info['system']['version']}")
            
            # 作者信息
            if self.device_info['system'].get('author'):
                info.append(f"作者: {self.device_info['system']['author']}")
            
            # 时钟频率 - 优先使用clock_frequency，其次使用clock
            clock_freq = self.device_info['system'].get('clock_frequency') or self.device_info['system'].get('clock')
            if clock_freq:
                info.append(f"时钟频率: {clock_freq}")
            
            # Flash大小 - 优先使用flash_size，其次使用flash
            flash_size = self.device_info['system'].get('flash_size') or self.device_info['system'].get('flash')
            if flash_size:
                info.append(f"Flash大小: {flash_size}")
            
            # XRAM大小 - 优先使用xram_size，其次使用xram
            xram_size = self.device_info['system'].get('xram_size') or self.device_info['system'].get('xram')
            if xram_size:
                info.append(f"XRAM大小: {xram_size}")
            
            if self.device_info['system'].get('usb_cdc'):
                info.append(f"USB-CDC: {self.device_info['system']['usb_cdc']}")
            
            if self.device_info['system'].get('build_date'):
                info.append(f"编译日期: {self.device_info['system']['build_date']}")
            
            if self.device_info['system'].get('build_time'):
                info.append(f"编译时间: {self.device_info['system']['build_time']}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 访问系统信息出错: {e}")
            info.append("系统信息解析出错")
        
        # RTC时钟信息
        if self.device_info['system'].get('rtc_time'):
            info.append("")
            info.append("【RTC时钟】")
            info.append(f"当前时间: {self.device_info['system']['rtc_time']}")
        
        # 内存信息（从memory字段获取）
        info.append("")
        info.append("【内存使用】")
        
        # 调试：检查memory字段内容
        if self.debug_mode:
            print(f"[DEBUG] Memory字段内容: {self.device_info['memory']}")
        
        memory_data_available = False
        
        # 安全访问内存信息
        try:
            if self.device_info['memory'].get('flash_used'):
                info.append(f"Flash已用: {self.device_info['memory']['flash_used']}")
                memory_data_available = True
            if self.device_info['memory'].get('flash_constants'):
                info.append(f"常量存储: {self.device_info['memory']['flash_constants']}")
                memory_data_available = True
            if self.device_info['memory'].get('xram_used'):
                info.append(f"XRAM已用: {self.device_info['memory']['xram_used']}")
                memory_data_available = True
            if self.device_info['memory'].get('internal_ram_used'):
                info.append(f"内部RAM: {self.device_info['memory']['internal_ram_used']}")
                memory_data_available = True
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 访问内存信息出错: {e}")
        
        # 如果内存信息为空，显示提示
        if not memory_data_available:
            info.append("暂无内存使用信息")
        
        # 硬件信息
        if any(self.device_info['hardware']['adc'].values()):
            info.append("")
            info.append("【硬件信息】")
            if self.device_info['hardware']['adc']['resolution']:
                info.append(f"ADC分辨率: {self.device_info['hardware']['adc']['resolution']}")
            if self.device_info['hardware']['adc']['channels']:
                info.append(f"ADC通道数: {self.device_info['hardware']['adc']['channels']}")
            if self.device_info['hardware']['adc']['reference']:
                info.append(f"ADC参考电压: {self.device_info['hardware']['adc']['reference']}")
        
        # 性能信息
        if any(self.device_info['performance'].values()):
            info.append("")
            info.append("【性能信息】")
            if self.device_info['performance']['cpu_frequency']:
                info.append(f"CPU频率: {self.device_info['performance']['cpu_frequency']}")
            if self.device_info['performance']['tfpu_enabled']:
                info.append(f"TFPU状态: {'已启用' if self.device_info['performance']['tfpu_enabled'] else '未启用'}")
            if self.device_info['performance']['tfpu_frequency']:
                info.append(f"TFPU频率: {self.device_info['performance']['tfpu_frequency']}")
            if self.device_info['performance']['benchmark_results']:
                info.append(f"基准测试: {self.device_info['performance']['benchmark_results']}")
        
        # 状态信息
        info.append("")
        info.append("【状态信息】")
        info.append(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(info)
        
    def reset(self):
        """重置设备信息管理器"""
        # 简化重置逻辑
        try:
            # 重置系统信息
            for key in self.device_info['system']:
                self.device_info['system'][key] = ''
            
            # 重置硬件信息
            for hw_type in self.device_info['hardware']:
                if isinstance(self.device_info['hardware'][hw_type], dict):
                    for key in self.device_info['hardware'][hw_type]:
                        self.device_info['hardware'][hw_type][key] = ''
            
            # 重置状态
            for key in self.device_info['status']:
                if isinstance(self.device_info['status'][key], bool):
                    self.device_info['status'][key] = False
                else:
                    self.device_info['status'][key] = ''
            
            # 重置性能信息
            if 'performance' in self.device_info and isinstance(self.device_info['performance'], dict):
                for key in self.device_info['performance']:
                    if isinstance(self.device_info['performance'][key], bool):
                        self.device_info['performance'][key] = False
                    else:
                        self.device_info['performance'][key] = ''
            
            # 重置内存信息
            if 'memory' in self.device_info and isinstance(self.device_info['memory'], dict):
                for key in self.device_info['memory']:
                    if isinstance(self.device_info['memory'][key], bool):
                        self.device_info['memory'][key] = False
                    else:
                        self.device_info['memory'][key] = ''
            
            # 重置时钟系统信息
            if 'clock_system' in self.device_info and isinstance(self.device_info['clock_system'], dict):
                for key in self.device_info['clock_system']:
                    self.device_info['clock_system'][key] = ''
            
            # 重置当前测试单元
            if 'current_test_unit' in self.device_info:
                self.device_info['current_test_unit'] = ''
        except Exception as e:
            print(f"[DEBUG] 重置设备信息出错: {e}")
            pass
            self.device_info['performance']['tfpu_sin_ratio'] = ''
            self.device_info['performance']['timing_warnings'] = []
            
            # 重置时钟系统信息
            self.device_info['clock_system']['system_clock'] = ''
            self.device_info['clock_system']['pll_output_clock'] = ''
            self.device_info['clock_system']['high_speed_peripheral_clock'] = ''
            self.device_info['clock_system']['tfpu_clock_divider'] = ''
            self.device_info['clock_system']['prescaler_coefficient'] = ''
            self.device_info['clock_system']['calculated_frequency'] = ''
            self.device_info['clock_system']['cpu_frequency_ratio'] = ''
            self.device_info['clock_system']['clksel_register'] = ''
            self.device_info['clock_system']['usbclk_register'] = ''
            self.device_info['system']['t4t3m_register'] = ''
            self.device_info['clock_system']['dmair_register'] = ''
            self.device_info['clock_system']['tfpu_frequency_verification'] = ''
            self.device_info['clock_system']['conclusion'] = ''
            
            # 重置外设信息
            self.device_info['peripherals'] = {}
            
    def check_mode_timeout(self, current_time):
        """检查模式超时 - 增强版本"""
        for mode in ['system_info_mode', 'hardware_test_mode', 'voltage_mode', 'clock_info_mode']:
            if self.device_info['status'].get(mode, False):
                if mode not in self.mode_start_time:
                    self.mode_start_time[mode] = current_time
                else:
                    # 动态超时时间 - 根据模式类型调整
                    if mode == 'hardware_test_mode':
                        timeout = self.mode_timeout * 2  # 硬件测试需要更长时间
                    elif mode == 'clock_info_mode':
                        timeout = self.mode_timeout * 1.5  # 时钟信息需要中等时间
                    else:
                        timeout = self.mode_timeout  # 默认超时时间
                    
                    # 检查超时
                    if isinstance(current_time, time.struct_time):
                        current_seconds = time.mktime(current_time)
                        start_seconds = time.mktime(self.mode_start_time[mode])
                        elapsed = current_seconds - start_seconds
                    else:
                        elapsed = current_time - self.mode_start_time[mode]
                    
                    if elapsed > timeout:
                        # 超时，退出模式
                        self.device_info['status'][mode] = False
                        del self.mode_start_time[mode]
                        if self.debug_mode:
                            print(f"[DEBUG] {mode} 超时({timeout:.1f}s)，自动退出")
                        self.device_info_updated.emit(self.device_info)
    
    def get_device_info(self) -> dict:
        """获取设备信息字典"""
        return self.device_info
    
    def _safe_access_nested_dict(self, dict_obj, key_path, default_value=''):
        """安全访问嵌套字典"""
        try:
            keys = key_path.split('.')
            current = dict_obj
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default_value
            return current if current is not None else default_value
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 访问嵌套字典失败 {key_path}: {e}")
            return default_value
    
    def _check_performance_ratio(self, base_field, ratio_field):
        """检查性能比值是否存在"""
        return (self.device_info['performance'].get(f'{base_field}_avg') and 
                not self.device_info['performance'].get(f'{ratio_field}_ratio'))

    def _calculate_device_info_hash(self):
        """计算设备信息的哈希值，用于检测变化"""
        try:
            # 将设备信息转换为JSON字符串
            info_str = json.dumps(self.device_info, sort_keys=True, separators=(',', ':'))
            # 计算MD5哈希
            return hashlib.md5(info_str.encode()).hexdigest()
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 计算设备信息哈希失败: {e}")
            try:
                # 返回默认哈希值
                return hashlib.md5(b'default').hexdigest()
            except Exception as fallback_e:
                # 如果hashlib完全不可用，返回基于时间的简单哈希
                return f"fallback_{int(time.time())}"
    
    def _generate_content_fingerprint(self, full_hash: str = None) -> str:
        """生成内容指纹，忽略时间戳变化"""
        try:
            # 提取设备信息的核心内容，不包含时间戳
            core_info = {}
            
            # 系统信息
            if 'system' in self.device_info:
                system_info = self.device_info['system'].copy()
                # 移除时间相关字段
                system_info.pop('last_update', None)
                # 移除其他可能的时间戳字段
                time_fields = ['updated_at', 'timestamp', 'last_check']
                for field in time_fields:
                    system_info.pop(field, None)
                core_info['system'] = system_info
            
            # 硬件信息
            if 'hardware' in self.device_info:
                core_info['hardware'] = self.device_info['hardware']
            
            # 性能信息
            if 'performance' in self.device_info:
                core_info['performance'] = self.device_info['performance']
            
            # 内存信息
            if 'memory' in self.device_info:
                core_info['memory'] = self.device_info['memory']
            
            # 状态信息（但移除时间戳相关字段）
            if 'status' in self.device_info:
                status_info = self.device_info['status'].copy()
                status_info.pop('last_update', None)
                for field in ['updated_at', 'timestamp', 'last_check']:
                    status_info.pop(field, None)
                core_info['status'] = status_info
            
            # 生成内容指纹
            content_str = json.dumps(core_info, sort_keys=True, ensure_ascii=False)
            import hashlib
            return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:16]  # 使用MD5并截断
            
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] 生成内容指纹失败: {e}")
            if full_hash:
                return full_hash[:16]  # 返回完整哈希的前16位作为后备
            else:
                return f"fingerprint_{int(time.time())}"  # 返回基于时间的指纹作为后备