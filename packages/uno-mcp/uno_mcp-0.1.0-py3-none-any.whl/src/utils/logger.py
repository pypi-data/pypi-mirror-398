"""
日志模块
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..config import settings


# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 颜色代码
COLORS = {
    "DEBUG": "\033[36m",     # 青色
    "INFO": "\033[32m",      # 绿色
    "WARNING": "\033[33m",   # 黄色
    "ERROR": "\033[31m",     # 红色
    "CRITICAL": "\033[35m",  # 紫色
    "RESET": "\033[0m"
}


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    设置日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
    """
    level = level or settings.log_level
    log_file = log_file or settings.log_file
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(file_handler)
    
    # 抑制第三方库的日志
    for lib in ["httpx", "httpcore", "motor", "pymongo", "asyncio"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    # 抑制 MCP SDK 的冗余日志（保留 WARNING 及以上）
    # logging.getLogger("mcp").setLevel(logging.WARNING)
    # logging.getLogger("mcp.client").setLevel(logging.WARNING)
    # logging.getLogger("mcp.client.streamable_http").setLevel(logging.WARNING)
    # logging.getLogger("mcp.client.sse").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    return logging.getLogger(f"uno.{name}")

