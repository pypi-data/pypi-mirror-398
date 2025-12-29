#!/usr/bin/env python

"""
Author: Bitliker
Date: 2024-09-06 11:18:11
Version: 1.0
Description: 日志管理

引入库:
    logging
"""
import os
import logging


class _Colors:
    """ANSI 颜色代码。"""

    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"

    # 语义别名
    ERROR = RED
    INFO = GREEN
    WARN = YELLOW
    DEBUG = CYAN


class _ColoredFormatter(logging.Formatter):
    """支持彩色输出的格式化器"""

    def __init__(self, fmt=None, datefmt=None, style="%", use_color=True):
        super().__init__(fmt, datefmt, style)
        self.use_color = use_color

    def format(self, record):
        # 根据use_color参数决定是否添加颜色
        if self.use_color:
            # 为不同日志级别添加对应颜色
            if record.levelno == logging.ERROR:
                record.levelname = f"{_Colors.ERROR}{record.levelname}{_Colors.RESET}"
                record.msg = f"{_Colors.ERROR}{record.msg}{_Colors.RESET}"
            elif record.levelno == logging.WARNING:
                record.levelname = f"{_Colors.WARN}{record.levelname}{_Colors.RESET}"
                record.msg = f"{_Colors.WARN}{record.msg}{_Colors.RESET}"
            elif record.levelno == logging.INFO:
                record.levelname = f"{_Colors.INFO}{record.levelname}{_Colors.RESET}"
                record.msg = f"{_Colors.INFO}{record.msg}{_Colors.RESET}"
            elif record.levelno == logging.DEBUG:
                record.levelname = f"{_Colors.DEBUG}{record.levelname}{_Colors.RESET}"
                record.msg = f"{_Colors.DEBUG}{record.msg}{_Colors.RESET}"

        return super().format(record)


def init_log(_log_file: str, _log_level: int = logging.INFO):
    """初始化日志"""
    logger = logging.getLogger()
    # 清除可能已存在的处理器
    logger.handlers.clear()
    # 设置日志级别
    logger.setLevel(_log_level)
    if _log_file:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        os.makedirs(os.path.dirname(_log_file), exist_ok=True)
        file_handler = logging.FileHandler(_log_file, encoding="utf-8", mode="a")
        file_handler.formatter = formatter
        file_handler.level = _log_level
        logger.addHandler(file_handler)
    # 控制台处理器 - 使用颜色
    console_formatter = _ColoredFormatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        use_color=True,
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def info(message: str):
    """info日志"""
    logging.info(message)


def error(message: str) -> None:
    """打印错误日志（红色）。

    Args:
        message: 日志消息
    """
    logging.error(message)


def warn(message: str) -> None:
    """打印警告日志（黄色）。

    Args:
        message: 日志消息
    """
    logging.warning(message)


def debug(message: str) -> None:
    """打印调试日志（青色）。

    Args:
        message: 日志消息
    """
    logging.debug(message)
