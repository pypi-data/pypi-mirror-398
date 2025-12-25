import logging
from rich.logging import RichHandler


def get_logger(name=None, log_file=None, add_console=True, level=logging.INFO):
    logger = logging.getLogger(name=name)
    logger.setLevel(level)  # 日志级别

    logger.propagate = False  # 不向 root logger 冒泡

    has_console = any(isinstance(h, RichHandler) for h in logger.handlers)
    has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)


    if add_console and not has_console:
        # 控制台 Rich 日志
        console_handler = RichHandler(rich_tracebacks=True)
        console_formatter = logging.Formatter(
            "[%(name)s - %(asctime)s]   %(message)s ",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 文件日志
    if log_file and not has_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


logger = get_logger()