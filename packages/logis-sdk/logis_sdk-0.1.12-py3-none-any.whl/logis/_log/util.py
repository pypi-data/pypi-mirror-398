import logging
import logging.handlers
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from colorlog import ColoredFormatter

from logis.util.pkg_util import get_class_full_path

from .fmt import LoggerFormat
from .model import HandlerDictConfig, LoggerDictConfig


def format_level(level: Union[int, str]) -> int:
    """
    将日志级别统一调整为logging内置常量
    """
    if isinstance(level, str):
        level = level.upper()
        level = getattr(logging, level)
    return level


def format_filename(
    filename: str,
    log_dir: Optional[Path] = None,
    ensure_suffix: Optional[str] = ".log",
) -> str:
    """
    格式化日志文件名，确保文件名以指定后缀结尾。
    如果未指定后缀，则默认使用 ".log"。
    如果未指定日志根目录，则直接返回文件名。
    如果指定了日志根目录，则确保目录存在，并返回绝对路径。
    """
    if ensure_suffix and not filename.endswith(ensure_suffix):
        filename += ensure_suffix
    if log_dir is None:
        return filename
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / filename)


def format_filename_if_necessary(
    handler: logging.Handler,
    log_dir: Optional[Path] = None,
    ensure_suffix: Optional[str] = ".log",
) -> None:
    """
    如果给定的handler是文件处理器类型，则格式化其文件名。
    """
    if not handler:
        return
    if isinstance(handler, logging.FileHandler):
        handler.baseFilename = format_filename(
            handler.baseFilename, log_dir, ensure_suffix
        )


def add_formatter_if_not(handler: logging.Handler) -> None:
    """
    如果给定的handler上尚未配置formatter， 则为其设置默认的formatter。
    """
    if not handler:
        return
    if handler.formatter is not None:
        return
    if isinstance(handler, logging.FileHandler):
        handler.setFormatter(logging.Formatter(LoggerFormat.DEFAULT.value))
    else:
        handler.setFormatter(ColoredFormatter(LoggerFormat.COLORED_DEFAULT.value))


def get_dict_config_tmpl():
    """
    获取默认的 logging.config.dictConfig 字典配置模板
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": defaultdict(dict),
        "filters": defaultdict(dict),
        "handlers": defaultdict(dict),
        "loggers": defaultdict(dict),
    }


def formatter_to_dict(formatter: logging.Formatter) -> Dict[str, Any]:
    """
    将 logging.Formatter 实例转换为 logging.config.dictConfig 兼容的字典配置
    """
    return {
        "class": get_class_full_path(formatter.__class__),
        "format": formatter._fmt,
        "datefmt": formatter.datefmt,
    }


def get_name_attr(obj: Any) -> str:
    """
    获取对象的名称， 如果对象没有名称，则返回其类型名。
    """
    return getattr(obj, "name", None)


def handler_to_dict(handler: logging.Handler) -> Dict[str, Any]:
    """
    将 logging.Handler 实例转换为 logging.config.dictConfig 兼容的字典配置
    """
    formatter = getattr(handler, "formatter", None)
    formatter_name = getattr(formatter, "name", None)
    handler_args: Dict[str, Any] = {
        "class": get_class_full_path(handler.__class__),
        "level": handler.level,
        "formatter": formatter_name,
        "filters": [
            get_name_attr(f)
            for f in handler.filters
            if isinstance(f, logging.Filter) and get_name_attr(f) is not None
        ],
    }
    if isinstance(handler, logging.FileHandler):
        handler_args["filename"] = handler.baseFilename
        handler_args["mode"] = handler.mode
        handler_args["encoding"] = handler.encoding
        handler_args["delay"] = handler.delay
    elif isinstance(handler, logging.StreamHandler):
        try:
            fileno = handler.stream.fileno()
            handler_args["stream"] = (
                "ext://sys.stdout" if fileno == 1 else "ext://sys.stderr"
            )
        except (AttributeError, OSError):
            handler_args["stream"] = "ext://sys.stdout"
    else:
        raise ValueError(f"Unsupported handler type: {handler}")

    if isinstance(handler, logging.handlers.RotatingFileHandler):
        handler_args["maxBytes"] = handler.maxBytes
        handler_args["backupCount"] = handler.backupCount
    elif isinstance(handler, logging.handlers.TimedRotatingFileHandler):
        handler_args["when"] = handler.when
        handler_args["interval"] = handler.interval
        handler_args["backupCount"] = handler.backupCount

    return handler_args


class DictConfigBuilder:
    """
    支持从对象实例中提取配置，
    并将其转换为 logging.config.dictConfig 兼容的字典配置
    1. 内置LoggerFormat枚举的所有格式
    """

    def dir(self, log_dir: str):
        self._log_dir = Path(log_dir)
        return self

    def __init__(self):
        self._log_dir: Optional[Path] = None
        self.__dict_config__ = get_dict_config_tmpl()
        self.__loggers__: Dict[str, Dict[str, Any]] = self.__dict_config__["loggers"]
        self.__handlers__: Dict[str, Dict[str, Any]] = self.__dict_config__["handlers"]
        self.__filters__: Dict[str, Dict[str, Any]] = self.__dict_config__["filters"]
        self.__formatters__: Dict[str, Dict[str, Any]] = self.__dict_config__[
            "formatters"
        ]

        for e in LoggerFormat:
            if "color" in e.name.lower():
                formatter = ColoredFormatter(fmt=e.value)
            else:
                formatter = logging.Formatter(fmt=e.value)
            self.formatter(formatter, name=e.formatter_name())

    def build(self):
        return self.__dict_config__

    def filter(self, f: logging.Filter, name: Optional[str] = None):
        """
        将 logging.Filter 实例转换为 logging.config.dictConfig 兼容的字典配置

        返回格式符合 Python logging 官方 dict 配置规范，支持直接用于 dictConfig()
        """
        if not isinstance(f, logging.Filter):
            logging.warning("only logging.Filter instance supported now: %s", f)
            return self
        name = name if name is not None else get_name_attr(f)
        setattr(f, "name", name)
        filter_dict: dict = self.__filters__[name]
        filter_dict.update({"()": get_class_full_path(f.__class__)})
        return self

    def handler(self, handler: logging.Handler, name: Optional[str] = None):
        """
        将 logging.Handler 实例转换为 logging.config.dictConfig 兼容的字典配置

        返回格式符合 Python logging 官方 dict 配置规范，支持直接用于 dictConfig()
        """
        name = name if name is not None else handler.name
        if name is None:
            name = str(uuid4())
        handler.name = name

        format_filename_if_necessary(
            handler, log_dir=self._log_dir, ensure_suffix=".log"
        )

        for f in handler.filters:
            if get_name_attr(f) is None:
                setattr(f, "name", str(uuid4()))

        if formatter := getattr(handler, "formatter", None):
            formatter_name = getattr(formatter, "name", None)
            if formatter_name is None:
                formatter_name = str(uuid4())
            setattr(formatter, "name", formatter_name)

        handler_dict = handler_to_dict(handler)
        formatter = getattr(handler, "formatter", None)
        if formatter is not None:
            self.formatter(formatter)
        for f in handler.filters:
            self.filter(f)
        self.__handlers__[name].update(handler_dict)
        return self

    def formatter(self, formatter: logging.Formatter, name: Optional[str] = None):
        """
        将 logging.Formatter 实例转换为 logging.config.dictConfig 兼容的字典配置

        返回格式符合 Python logging 官方 dict 配置规范，支持直接用于 dictConfig()
        """
        if formatter is None:
            return self
        name = name or getattr(formatter, "name", None)
        setattr(formatter, "name", name)
        formatter_dict = formatter_to_dict(formatter)
        self.__formatters__[name].update(formatter_dict)
        return self

    def logger(self, logger: logging.Logger):
        """
        将 logging.Logger 实例转换为 logging.config.dictConfig 兼容的字典配置

        返回格式符合 Python logging 官方 dict 配置规范，支持直接用于 dictConfig()
        """
        if logger is None:
            return self
        logger_dict: dict = self.__loggers__[logger.name]
        handler_ids = []
        for handler in logger.handlers:
            self.handler(handler)
            handler_ids.append(handler.name)

        logger_dict.update(
            {
                "level": logger.getEffectiveLevel(),
                "propagate": "yes" if logger.propagate else "no",
                "handlers": handler_ids,
            }
        )

        return self

    def logger_dict(self, config: LoggerDictConfig):
        self.__loggers__[config.name].update(config.model_dump(exclude={"name"}))
        return self

    def handler_dict(self, config: HandlerDictConfig):
        config.filename = format_filename(
            config.filename, log_dir=self._log_dir, ensure_suffix=".log"
        )
        self.__handlers__[config.name].update(config.model_dump(exclude={"name"}))
        return self
