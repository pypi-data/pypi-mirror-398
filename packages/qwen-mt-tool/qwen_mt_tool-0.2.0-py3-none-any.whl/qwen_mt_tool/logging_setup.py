# -*- coding: utf-8 -*-
"""
日志模块 - 配置彩色日志和使用统计日志
"""

import logging
import os

import colorlog

# 日志颜色配置
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}

# 创建彩色日志格式器
_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    reset=True,
    log_colors=LOG_COLORS,
)

# 控制台处理器
_handler = logging.StreamHandler()
_handler.setFormatter(_formatter)

# 主日志器
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)

# 使用统计日志器（稍后配置）
usage_logger = logging.getLogger("usage")
usage_logger.setLevel(logging.INFO)


def setup_logging(enable_logging: bool, log_file: str) -> None:
    """
    配置文件日志。
    
    Args:
        enable_logging: 是否启用文件日志
        log_file: 日志文件路径
    """
    if not enable_logging:
        return

    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def setup_usage_logging(enable_usage_log: bool, usage_log_file: str) -> None:
    """
    配置使用统计日志。
    
    Args:
        enable_usage_log: 是否启用使用统计日志
        usage_log_file: 使用统计日志文件路径
    """
    if not enable_usage_log:
        return
        
    # 检查文件是否存在，决定是否写入表头
    write_header = not os.path.exists(usage_log_file)
    
    usage_handler = logging.FileHandler(usage_log_file)
    usage_formatter = logging.Formatter("%(message)s")
    usage_handler.setFormatter(usage_formatter)
    usage_logger.addHandler(usage_handler)
    usage_logger.propagate = False
    
    if write_header:
        usage_logger.info("Time,File Path,Input Token,Output Token,Total Token")
