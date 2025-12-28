import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from pathlib import Path
from typing import Union, Optional, List, Type

try:
    from colorama import Fore, Style, init  # type: ignore[import-untyped]

    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

    class _DummyStyle:
        RESET_ALL = ""
        BRIGHT = ""

    class _DummyFore:
        GREEN = ""
        WHITE = ""
        YELLOW = ""
        RED = ""
        MAGENTA = ""

    Style = _DummyStyle()
    Fore = _DummyFore()

DEFAULT_COLORS = {
    logging.DEBUG: Fore.GREEN,
    logging.INFO: Fore.WHITE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA + getattr(Style, "BRIGHT", ""),
}


__all__ = (
    "loggerConfig",
    "VXColoredFormatter",
)

__BASIC_FORMAT__ = (
    "%(asctime)s [%(process)s:%(threadName)s - %(funcName)s@%(filename)s:%(lineno)d]"
    " %(levelname)s: %(message)s"
)


class VXColoredFormatter(logging.Formatter):
    COLORS = DEFAULT_COLORS

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        reset_code: str = "",
    ):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.reset_code = reset_code

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{log_color}{message}{self.reset_code}"

    @classmethod
    def set_color(cls, level: int, color: str) -> Type["VXColoredFormatter"]:
        cls.COLORS[level] = color
        return cls


def loggerConfig(
    level: Union[str, int] = "INFO",
    format: Optional[str] = None,
    datefmt: str = "",
    *,
    force: bool = False,
    colored: bool = True,
    filename: Union[str, Path] = "",
    encoding: Optional[str] = None,
    logger: Optional[Union[str, logging.Logger]] = None,
    async_logger: bool = True,
    when: str = "D",
    interval: int = 7,
    backup_count: int = 7,
    stream: Optional[object] = None,
) -> logging.Logger:
    """为logging模块打补丁"""
    if logger is None:
        logger = logging.root

    elif isinstance(logger, str):
        logger = logging.getLogger(logger)

    if force:
        logger.handlers = []

    elif logger.handlers:
        return logger

    logger.setLevel(level)
    if format is None:
        format = __BASIC_FORMAT__
    if datefmt == "":
        datefmt = "%Y-%m-%d %H:%M:%S"

    console_handler = (
        logging.StreamHandler(stream=stream)
        if stream is not None
        else logging.StreamHandler()
    )
    console_handler.setLevel(level=level)
    if colored:
        reset_code = Style.RESET_ALL if COLORAMA_AVAILABLE else ""
        if COLORAMA_AVAILABLE:
            init(autoreset=True)
        console_handler.setFormatter(
            VXColoredFormatter(fmt=format, datefmt=datefmt, reset_code=reset_code)
        )
    else:
        console_handler.setFormatter(logging.Formatter(fmt=format, datefmt=datefmt))

    logger_handlers: List[logging.Handler] = [console_handler]

    if filename:
        log_file = Path(filename)
        log_dir = log_file.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        if encoding is None:
            encoding = "utf-8"

        file_handler = TimedRotatingFileHandler(
            log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=encoding,
        )

        file_handler.setFormatter(logging.Formatter(fmt=format, datefmt=datefmt))
        file_handler.setLevel(level)
        logger_handlers.append(file_handler)

    if async_logger:
        q: Queue[logging.LogRecord] = Queue(-1)
        q_handler = QueueHandler(q)
        q_handler.setLevel(logging.DEBUG)
        listener = QueueListener(q, *logger_handlers)
        listener.start()
        logger.addHandler(q_handler)
        setattr(logger, "_vx_listener", listener)
    else:
        for handler in logger_handlers:
            logger.addHandler(handler)
    logger.propagate = False
    return logger


def stop_logger(logger: Optional[Union[str, logging.Logger]] = None) -> None:
    if logger is None:
        logger = logging.root
    elif isinstance(logger, str):
        logger = logging.getLogger(logger)
    listener = getattr(logger, "_vx_listener", None)
    try:
        if listener and getattr(listener, "_thread", None) is not None:
            listener.stop()
    finally:
        if listener and hasattr(logger, "_vx_listener"):
            try:
                delattr(logger, "_vx_listener")
            except Exception:
                pass
    for h in list(logger.handlers):
        try:
            h.flush()
        except Exception:
            pass
        try:
            h.close()
        except Exception:
            pass
        logger.removeHandler(h)


if __name__ == "__main__":
    import time

    loggerConfig(
        level="DEBUG",
        force=False,
        colored=True,
        filename="log/message.log",
        datefmt="",
        async_logger=False,
        when="D",
        interval=7,
        backup_count=7,
    )

    print("+++++++++++++++++++")
    logging.debug("debug")
    logging.info("hello")
    logging.warning("warning")
    logging.error("error")
    logging.critical("critical")
    logging.info("info")
    logging.info("info2")
    logging.info("info3")
    print([h for h in logging.root.handlers])

    listener = getattr(logging.root, "_vx_listener", None)
    if listener:
        time.sleep(2)
        listener.stop()
