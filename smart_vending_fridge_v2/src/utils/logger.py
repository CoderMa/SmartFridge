#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志模块 - 提供日志记录功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(log_level=logging.INFO, log_file=None, max_bytes=10*1024*1024, backup_count=5):
    """
    设置日志记录器
    
    Args:
        log_level (int): 日志级别
        log_file (str, optional): 日志文件路径
        max_bytes (int, optional): 单个日志文件最大字节数
        backup_count (int, optional): 备份日志文件数量
    """
    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加控制台处理器
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，则添加文件处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # 添加文件处理器
        logger.addHandler(file_handler)
    
    return logger