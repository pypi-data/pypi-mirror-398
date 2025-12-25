import logging
import threading
from rich.logging import RichHandler
from typing import Type, List, Optional

from .handlers import MultiProcessSafeSizeRotatingHandler, MultiProcessSafeTimeRotatingHandler

class LogManager:
    """
    一个线程安全的日志管理器，用于获取和配置具有 Rich 控制台输出的 Logger。
    """
    _logger_cache: dict[str, logging.Logger] = {}
    _lock = threading.Lock()

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[str] = None,
        add_console: bool = True,
        level: int = logging.INFO,
        custom_handlers: Optional[logging.Handler] = None,
    ) -> logging.Logger:
        """
        获取或创建一个配置好的 logger。

        注意：Logger 实例按 name 缓存。重复调用会返回同一个实例，
        但会确保其配置（如 level 和 handlers）符合当前调用参数。

        :param name: logger 名称。
        :param log_file: 日志文件路径，如果为 None 则不写入文件。
        :param add_console: 是否添加带 Rich 格式的控制台 Handler。
        :param level: 日志级别。
        :param custom_handlers: 自定义 Handler 列表。
        """
        with cls._lock:
            # 1. 获取或创建 Logger 实例 (利用 logging 模块自身的缓存)
            logger = logging.getLogger(name)

            # 2. 确保基本配置
            logger.setLevel(level)
            logger.propagate = False

            # 3. 配置控制台 Handler
            if add_console and not any(isinstance(h, RichHandler) for h in logger.handlers):
                console_handler = RichHandler(rich_tracebacks=True, show_time=False, show_path=False)
                # 注意：RichHandler 默认有自己的时间格式，我们可以在 Formatter 中覆盖
                console_formatter = logging.Formatter(
                    "%(asctime)s | %(name)-8s | %(levelname)-4s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                console_handler.setFormatter(console_formatter)
                logger.addHandler(console_handler)

            # 4. 配置文件 Handler
            if log_file and not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_formatter = logging.Formatter(
                    "%(asctime)s | %(name)-8s | %(levelname)-4s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

            # 5. 配置自定义 Handlers (修正了原代码的 Bug)
            if custom_handlers:
                # 为所有自定义 handlers 设置一个统一的格式
                custom_formatter = logging.Formatter(
                    "%(asctime)s | %(name)-8s | %(levelname)-4s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                if custom_handlers not in logger.handlers:
                    custom_handlers.setFormatter(custom_formatter)
                    logger.addHandler(custom_handlers)

            return logger


# 全局可用的 get_logger 函数（无需引用 LogManager）
def get_logger(
    name: str=None,
    log_file: Optional[str] = None,
    add_console: bool = True,
    level: int = logging.INFO,
    custom_handlers: logging.Handler = None,
):
    """
    便捷函数：获取日志记录器，无需关心 LogManager 实例化。
    
    使用示例：
        from log_manager import get_logger
        logger = get_logger("my_module", log_file="app.log")
        logger.info("Hello world")
    """
    if name is None:
        name = "tmp_log"

    return LogManager.get_logger(
        name=name,
        log_file=log_file,
        add_console=add_console,
        level=level,
        custom_handlers=custom_handlers
    )

# logger = LogManager().get_logger("tmp_log")

