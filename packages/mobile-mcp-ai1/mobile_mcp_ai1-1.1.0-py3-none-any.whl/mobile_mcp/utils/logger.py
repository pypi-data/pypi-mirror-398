#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具 - 统一的日志管理

功能：
1. 统一的日志格式
2. 日志级别控制
3. 文件日志和控制台日志
4. 性能日志记录
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class MobileMCPLogger:
    """Mobile MCP 日志管理器"""
    
    _instance: Optional['MobileMCPLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger('mobile_mcp')
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()
        
        self._initialized = True
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（可选）
        try:
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"mobile_mcp_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        except Exception as e:
            # 如果无法创建文件日志，只使用控制台日志
            pass
    
    def set_level(self, level: str):
        """设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info=False):
        """错误日志"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info=False):
        """严重错误日志"""
        self.logger.critical(message, exc_info=exc_info)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """性能日志"""
        extra_info = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"⏱️  {operation} 耗时: {duration:.3f}s {extra_info}")


# 全局日志实例
_logger: Optional[MobileMCPLogger] = None


def get_logger() -> MobileMCPLogger:
    """获取日志实例"""
    global _logger
    if _logger is None:
        _logger = MobileMCPLogger()
    return _logger

