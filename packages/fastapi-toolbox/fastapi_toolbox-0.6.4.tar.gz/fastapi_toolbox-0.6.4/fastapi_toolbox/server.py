# encoding=utf-8
"""
FastAPI服务器启动工具
"""
import logging
from typing import Optional, List, Callable

from uvicorn import Server
from uvicorn.supervisors import Multiprocess

from .config import UvicornConfig
from .logging import logger, add_file_log


def run_server(
    app: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    workers: int = 1,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    filter_callbacks: Optional[List[Callable]] = None,
    rotation_size: int = 10 * 1024 * 1024,  # 默认10MB
    rotation_time: str = "00:00",  # 默认午夜轮转
    retention: str = "10 Days",  # 默认保留10天
    compression: str = "zip",  # 默认使用zip压缩
    **uvicorn_kwargs
):
    """
    启动FastAPI服务器，支持单进程和多进程模式

    Args:
        app: FastAPI应用的导入路径，如 "main:app"
        host: 监听地址，默认 "127.0.0.1"
        port: 监听端口，默认 8000
        workers: 工作进程数，大于1时使用多进程模式，默认 1
        log_file: 日志文件路径，如 "logs/app.log"，None表示不记录到文件
        log_format: 日志格式，默认 "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
        filter_callbacks: 日志过滤回调函数列表，每个回调接收record参数，返回True表示过滤掉该日志
        rotation_size: 文件大小限制（字节），默认10MB
        rotation_time: 每天轮转的时间点，格式"HH:MM"，默认"00:00"
        retention: 日志保留时间，默认"10 Days"
        compression: 日志压缩格式，默认"zip"
        **uvicorn_kwargs: 其他uvicorn配置参数

    Example:
        ```python
        from fastapi_toolbox import run_server
        import logging

        # SQLAlchemy日志过滤器示例
        def filter_sqlalchemy(record):
            if record.name.startswith("sqlalchemy"):
                if record.levelno < logging.ERROR:
                    return True

        # 启动服务器
        run_server(
            "main:app",
            host="0.0.0.0",
            port=8000,
            workers=4,
            log_file="logs/app.log",
            filter_callbacks=[filter_sqlalchemy]
        )
        ```
    """
    # 配置日志
    # 重置logger，去掉默认带的sink，否则默认它带的stderr sink无法通过spawn方式传递过去，无法序列化
    # 会报错 TypeError: cannot pickle '_io.TextIOWrapper' object
    logger.remove()

    # 添加文件日志（如果指定了日志文件路径）
    if log_file:
        if log_format is None:
            log_format = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
        add_file_log(
            log_file,
            _format=log_format,
            workers=workers,
            rotation_size=rotation_size,
            rotation_time=rotation_time,
            retention=retention,
            compression=compression
        )

    # 创建uvicorn配置
    config = UvicornConfig(
        app,
        host=host,
        port=port,
        workers=workers,
        filter_callbacks=filter_callbacks,
        **uvicorn_kwargs
    )

    # 创建服务器实例
    server = Server(config=config)

    try:
        # 根据workers数量选择启动模式
        if workers < 2:
            # 单进程模式
            server.run()
        else:
            # 多进程模式
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
    except KeyboardInterrupt:
        pass