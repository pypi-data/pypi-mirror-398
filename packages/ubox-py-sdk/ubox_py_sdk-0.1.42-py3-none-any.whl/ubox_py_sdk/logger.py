"""
优测 UBox 日志配置模块

提供统一的日志配置，支持控制台和文件输出。
"""

import logging
import sys
import os
from typing import Optional

# 全局日志配置状态
_logging_configured = False
_logging_config = {
    'level': logging.INFO,
    'format_string': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_to_file': False,
    'log_file_path': 'ubox/ubox_sdk.log'
}


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_to_file: bool = False,
    log_file_path: str = "ubox/ubox_sdk.log"
) -> None:
    """
    配置全局日志系统
    
    Args:
        level: 日志级别
        format_string: 日志格式字符串
        log_to_file: 是否输出到文件
        log_file_path: 日志文件路径
    """
    global _logging_configured, _logging_config
    
    # 更新配置
    _logging_config['level'] = level
    _logging_config['format_string'] = format_string or _logging_config['format_string']
    _logging_config['log_to_file'] = log_to_file
    _logging_config['log_file_path'] = log_file_path
    _logging_configured = True
    
    # 创建格式化器
    formatter = logging.Formatter(_logging_config['format_string'])
    
    # 配置所有 ubox_py_sdk 相关的日志器
    for logger_name in list(logging.root.manager.loggerDict.keys()):
        if logger_name.startswith('ubox_py_sdk'):
            _configure_logger(logger_name, level, formatter, log_to_file, log_file_path)
    
    # 记录配置成功信息
    root_logger = logging.getLogger('ubox_py_sdk')
    if log_to_file:
        root_logger.info(f"日志系统已配置 - 级别: {logging.getLevelName(level)}, 文件输出: {log_file_path}")
    else:
        root_logger.info(f"日志系统已配置 - 级别: {logging.getLevelName(level)}")


def _configure_logger(logger_name: str, level: int, formatter: logging.Formatter, 
                     log_to_file: bool, log_file_path: str) -> None:
    """
    配置单个日志器
    
    Args:
        logger_name: 日志器名称
        level: 日志级别
        formatter: 格式化器
        log_to_file: 是否输出到文件
        log_file_path: 日志文件路径
    """
    logger = logging.getLogger(logger_name)
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置日志级别和传播
    logger.setLevel(level)
    logger.propagate = False
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果启用文件日志，添加文件处理器
    if log_to_file:
        try:
            # 确保日志文件所在目录存在
            log_dir = os.path.dirname(log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建文件日志处理器: {e}")


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则使用默认名称
        
    Returns:
        日志器实例
    """
    if name is None:
        name = "ubox_py_sdk"
    
    # 获取日志器
    logger = logging.getLogger(name)
    
    # 如果日志系统还没有配置，使用默认配置
    if not _logging_configured and not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# 默认日志器
default_logger = get_logger("ubox_py_sdk")
