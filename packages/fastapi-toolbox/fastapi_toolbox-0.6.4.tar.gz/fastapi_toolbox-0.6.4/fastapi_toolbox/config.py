import copy
import sys

from uvicorn import Config

from .logging import get_log_level, logger, setup_logging

LOG_LEVEL = get_log_level()

class UvicornConfig(Config):
    """
    自定义配置类,继承自uvicorn的Config类
    uvicorn 用的spawn，需要通过config把logger._core 传递到子进程里
    """

    def __init__(self, *args, **kwargs):
        """
        初始化方法
        保存logger的core对象,并调用父类初始化

        Args:
            filter_callbacks: 可选的过滤回调函数列表，用于过滤日志记录。
                            每个回调函数接收一个record参数，返回True表示过滤掉该日志。
                            常用于过滤特定模块的日志，如SQLAlchemy的低级别日志。
        """
        # 提取callbacks参数
        self.filter_callbacks = kwargs.pop('filter_callbacks', None)

        # 这里core.handlers 里只有文件的handler
        # 1. 字典的浅拷贝
        self._core = copy.copy(logger._core)
        super().__init__(*args, **kwargs)

    def configure_logging(self) -> None:
        """
        配置日志
        重写父类的configure_logging方法
        确保子进程logger使用父进程传递过来的core对象
        设置日志配置
        """

        super().configure_logging()
        if logger._core.handlers is not self._core.handlers:
            # 3. 父进程里 不会进入这里
            # 子进程里 会进入这里， 使用父进程传递进来的core对象
            logger._core= self._core

            logger.add(sys.stderr, level=LOG_LEVEL)

            setup_logging(filter_callbacks=self.filter_callbacks)
        else:
            # 2. 添加一个handler后
            # 这里loguru logger._core.handlers 会浅拷贝，生成一个新的对象
            # self._core.handlers 还是引用的原有的对像
            # 而原有的对象里只有文件的handler, 这样才能传递到子进程里 (可序列化)
            logger.add(sys.stderr, level=LOG_LEVEL)

            setup_logging(filter_callbacks=self.filter_callbacks)