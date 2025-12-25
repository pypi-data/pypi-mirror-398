# -*- coding: UTF-8 -*-
import logging
import logging.handlers
import logging.handlers
import os
from typing import Optional

from logzero import setup_logger, INFO, LogFormatter


def zero_log(log_name, log_file=None, level=INFO):
    """定义日志使用为默认使用zero的logger，为每个任务以及主要运行步骤单独生成_logger"""
    """按照logzero格式自定义logger并去除颜色提示"""
    if log_file and not os.path.isdir(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    fmt = '%(color)s[%(levelname)1.1s %(asctime)s %(filename)16s:%(lineno)3d]%(end_color)s %(message)s'
    return setup_logger(
        name=log_name, logfile=log_file, maxBytes=int(10e6), backupCount=15, level=level,
        formatter=LogFormatter(color=True, fmt=fmt))


# 默认配置
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE_NAME = "app.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '[%(levelname)1.1s %(asctime)s %(filename)16s:%(lineno)3d] %(message)s'
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_BACKUP_COUNT = 7  # 保留最近 7 天日志
DEFAULT_LOG_FILE_MAX_BYTES = 10485760  # 10MB（仅用于 RotatingFileHandler）


class LoggerConfig:
    """日志配置类，便于集中管理配置项"""

    def __init__(
            self,
            log_dir: str = DEFAULT_LOG_DIR,
            log_filename: str = DEFAULT_LOG_FILE_NAME,
            level: int = DEFAULT_LOG_LEVEL,
            format_str: str = DEFAULT_LOG_FORMAT,
            date_format: str = DEFAULT_DATE_FORMAT,
            backup_count: int = DEFAULT_BACKUP_COUNT,
            max_bytes: int = DEFAULT_LOG_FILE_MAX_BYTES,
            use_timed_rotation: bool = True,  # True: 按天滚动；False: 按大小滚动
            encoding: str = "utf-8",
    ):
        self.log_dir = log_dir
        self.log_filename = log_filename
        self.level = level
        self.format_str = format_str
        self.date_format = date_format
        self.backup_count = backup_count
        self.max_bytes = max_bytes
        self.use_timed_rotation = use_timed_rotation
        self.encoding = encoding


def get_logger(
        name: str = __name__, config: Optional[LoggerConfig] = None
) -> logging.Logger:
    """
    创建并返回一个配置好的 logger 实例。

    :param name: Logger 名称（通常用模块名）
    :param config: LoggerConfig 配置对象，使用默认值如果未提供
    :return: 配置好的 Logger 实例
    """
    config = config or LoggerConfig()

    # 创建日志目录
    os.makedirs(config.log_dir, exist_ok=True)

    # 完整的日志文件路径
    log_filepath = os.path.join(config.log_dir, config.log_filename)

    # 获取 logger
    logger = logging.getLogger(name)
    logger.setLevel(config.level)
    logger.propagate = False  # 防止日志向上层 logger 传播（避免重复输出）

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 格式化器
    formatter = logging.Formatter(config.format_str, datefmt=config.date_format)

    # 文件处理器（按天或按大小滚动）
    file_handler: logging.Handler
    if config.use_timed_rotation:
        # 按时间滚动（每天一个文件）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filepath,
            when="midnight",
            backupCount=config.backup_count,
            encoding=config.encoding,
        )
        file_handler.suffix = "%Y-%m-%d.log"  # 文件名后缀如 app.log.2025-07-28
    else:
        # 按大小滚动
        file_handler = logging.handlers.RotatingFileHandler(
            log_filepath,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding=config.encoding,
        )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(config.level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(config.level)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


if __name__ == '__main__':
    app_logger = get_logger()
    app_logger.info("这是一条测试日志")
