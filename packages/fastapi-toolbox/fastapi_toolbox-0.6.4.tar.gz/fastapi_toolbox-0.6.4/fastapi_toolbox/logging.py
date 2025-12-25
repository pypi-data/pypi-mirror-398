# encoding=utf-8
import datetime
import logging
import multiprocessing
import os
from itertools import chain
from typing import Any, Optional

import loguru

__all__ = ["JSON_LOGS", "LOG_LEVEL", "logger", "InterceptHandler", "Rotator", "setup_logging", "add_file_log", "get_log_level"]

logger = loguru.logger


def get_log_level():
    """获取日志级别，从环境变量LOG_LEVEL中读取，默认INFO级别"""
    try:
        _key = "LOG_LEVEL"
        level = os.environ.get(_key, "")

        if level.lower() == "error":
            return logging.ERROR
        elif level.lower() == "warning":
            return logging.WARNING
        elif level.lower() == "debug":
            return logging.DEBUG
    except:
        pass
    return logging.INFO


class InterceptHandler(logging.Handler):
    """拦截标准库logging的Handler，将日志转发到loguru"""

    # 过滤回调列表
    filter_callbacks = []

    @classmethod
    def add_filter_callback(cls, callback):
        """添加过滤回调函数，回调函数接收record参数，返回True表示过滤掉该日志"""
        cls.filter_callbacks.append(callback)

    @classmethod
    def remove_filter_callback(cls, callback):
        """移除过滤回调函数"""
        if callback in cls.filter_callbacks:
            cls.filter_callbacks.remove(callback)

    def emit(self, record):
        # 获取对应的loguru日志级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            # 如果无法获取对应的level名称,则使用数字级别
            level = record.levelno

        # 获取日志发出的调用位置信息
        frame, depth = logging.currentframe(), 0
        logging_name = logging.__file__
        # 处理.pyc文件的情况
        if logging_name.endswith(".pyc"):
            logging_name = logging_name.rstrip("c")
        # 向上查找调用栈,直到找到最初的调用位置
        while frame.f_back and frame.f_code.co_filename in (logging_name, __file__):
            frame = frame.f_back
            depth += 1

        # 执行所有注册的过滤回调
        for callback in self.filter_callbacks:
            if callback(record):
                return

        # 使用loguru记录日志,传入调用深度和异常信息
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


LOG_LEVEL = get_log_level()
JSON_LOGS = True if os.environ.get("JSON_LOGS", "0") == "1" else False


def setup_logging(filter_callbacks=None):
    """设置日志配置，拦截所有标准logging的日志并转发到loguru

    Args:
        filter_callbacks: 过滤回调函数列表，每个回调接收record参数，返回True表示过滤掉该日志
    """
    # 注册过滤回调
    if filter_callbacks:
        for callback in filter_callbacks:
            InterceptHandler.add_filter_callback(callback)

    # 设置根日志记录器的处理器，包括拦截器和流处理器
    logging.root.handlers = [InterceptHandler()]
    # 设置根日志记录器的日志级别
    logging.root.setLevel(LOG_LEVEL)

    # 移除所有其他日志记录器的处理器
    # 并将日志传播到根日志记录器

    # 需要特殊处理的日志记录器列表
    loggers = (
        "uvicorn",  # uvicorn web服务器主日志
        "uvicorn.access",  # uvicorn访问日志
        "uvicorn.error",  # uvicorn错误日志
        "fastapi",  # FastAPI框架日志
        "asyncio",  # 异步IO日志
        "starlette",  # Starlette框架日志
    )

    # 处理所有日志记录器
    for name in chain(loggers, logging.root.manager.loggerDict.keys()):
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = []  # 清空处理器
        logging_logger.propagate = True  # 启用日志传播


class Rotator:
    """
    日志轮转器，支持按文件大小和时间轮转

    Args:
        size: 文件大小限制（字节）
        at: 每天轮转的时间点
    """
    def __init__(self, *, size: int, at: datetime.time):
        now = datetime.datetime.now()

        self._size_limit = size
        self._time_limit = now.replace(hour=at.hour, minute=at.minute, second=at.second)

        if now >= self._time_limit:
            # The current time is already past the target time so it would rotate already.
            # Add one day to prevent an immediate rotation.
            self._time_limit += datetime.timedelta(days=1)

    def should_rotate(self, message, file):
        """判断是否应该轮转日志文件"""
        file.seek(0, 2)
        if file.tell() + len(message) > self._size_limit:
            return True
        if message.record["time"].timestamp() > self._time_limit.timestamp():
            self._time_limit += datetime.timedelta(days=1)
            return True
        return False


def add_file_log(
    log_path: str,
    _format: Optional[str] = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    patcher: Optional[Any] = None,
    workers: int = 1,
    rotation_size: int = 10 * 1024 * 1024,  # 默认10MB
    rotation_time: str = "00:00",  # 默认午夜轮转
    retention: str = "10 Days",  # 默认保留10天
    compression: str = "zip"  # 默认使用zip压缩
):
    """
    添加文件日志处理器

    Args:
        log_path: 日志文件路径
        _format: 日志格式
        patcher: loguru的patcher函数
        workers: 工作进程数，大于1时启用异步日志
        rotation_size: 文件大小限制（字节），默认10MB
        rotation_time: 每天轮转的时间点，格式"HH:MM"，默认"00:00"
        retention: 日志保留时间，默认"10 Days"
        compression: 日志压缩格式，默认"zip"
    """
    rotator = Rotator(
        size=rotation_size,
        at=datetime.datetime.strptime(rotation_time, "%H:%M").time(),
    )
    if workers > 1:
        spawn_context = multiprocessing.get_context("spawn")
        enqueue = True
    else:
        spawn_context = None
        enqueue = False

    logger.configure(patcher=patcher)
    logger.add(
        log_path,  # log file path
        level=LOG_LEVEL,  # logging level
        format=_format,
        enqueue=enqueue,  # set to true for async or multiprocessing logging
        backtrace=False,  # turn to false if in production to prevent data leaking
        rotation=rotator.should_rotate,  # file size or time to rotate
        retention=retention,  # how long a the logging data persists
        compression=compression,  # log rotation compression
        serialize=JSON_LOGS,  # if you want it JSON style, set to true. But also change the format
        context=spawn_context,
    )


if __name__ == "__main__":
    foo = "bar"
    logger.info(f"example {foo} test")
    logger.opt(exception=True).debug("something bad happened")