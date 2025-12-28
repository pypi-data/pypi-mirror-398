import logging
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import List, Optional, Type, Union
from uuid import uuid4

from platformdirs import user_data_dir

from .util import add_formatter_if_not, format_filename, format_level


class LoggerBuilder:
    """
    日志构建器接口
    """

    def __init__(self, **kwargs) -> None:
        self.dir(Path(user_data_dir()) / "logs").name("root").level(
            logging.WARNING
        ).encoding("utf-8").backup_count(5).rotation_when("h").max_bytes(
            200 * 1024 * 1024
        ).propagate(
            False
        )

        self._handlers = []

    def _resolve_file_path(self, filename: str) -> Optional[Path]:
        if not filename:
            return None
        return Path(format_filename(filename, self._log_dir))

    def name(self, name: str) -> "LoggerBuilder":
        """
        设置日志名称
        """
        self._name = name
        return self

    def propagate(self, propagate: bool) -> "LoggerBuilder":
        """
        设置是否 Propagate 日志到父 Logger
        """
        self._propagate = propagate
        return self

    def dir(self, path: Union[str, Path]) -> "LoggerBuilder":
        """
        设置日志目录
        """
        self._log_dir = path if isinstance(path, Path) else Path(path)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        logging.debug("Log directory set to: %s", str(self._log_dir))
        return self

    def level(self, level: int = logging.WARNING) -> "LoggerBuilder":
        """
        设置root日志级别
        """
        level = format_level(level)
        self._level = level
        return self

    def max_bytes(self, max_bytes: int) -> "LoggerBuilder":
        """
        设置日志文件最大字节数
        """
        self._max_bytes = max_bytes
        return self

    def encoding(self, encoding: str) -> "LoggerBuilder":
        """
        设置日志文件编码
        """
        self._encoding = encoding
        return self

    def backup_count(self, count: int) -> "LoggerBuilder":
        """
        设置日志文件最大备份数量
        """
        self._backup_count = count
        return self

    def rotation_when(self, when: str) -> "LoggerBuilder":
        """
        设置日志文件轮转时间间隔单位
        """
        self._rotation_when = when
        return self

    def add_handler(
        self,
        handler_type: Union[Type[logging.Handler], logging.Handler],
        level: Optional[int] = None,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        filters: Optional[List[logging.Filter]] = None,
        **kwargs,
    ) -> "LoggerBuilder":
        """
        添加日志处理器
        """
        filename = self._resolve_file_path(filename)
        if isinstance(handler_type, logging.FileHandler) or issubclass(
            handler_type, logging.FileHandler
        ):
            kwargs.setdefault("delay", True)
            kwargs.update(encoding=self._encoding, filename=filename)
        if handler_type is TimedRotatingFileHandler:
            handler = TimedRotatingFileHandler(
                when=self._rotation_when,
                backupCount=self._backup_count,
                **kwargs,
            )
        elif handler_type is RotatingFileHandler:
            handler = RotatingFileHandler(
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
                **kwargs,
            )
        elif handler_type is StreamHandler:
            handler = StreamHandler(stream=kwargs.get("stream", sys.stdout))
        elif isinstance(handler_type, logging.Handler):
            handler = handler_type
        elif issubclass(handler_type, logging.Handler):
            handler = handler_type(**kwargs)
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")

        add_formatter_if_not(handler)

        level = level if level is not None else self._level
        handler.setLevel(format_level(level))

        if name is not None:
            handler.name = name

        if handler.name is None:
            handler.name = str(uuid4())

        for f in filters or []:
            handler.addFilter(f)

        self._handlers.append(handler)
        return self

    def build(self) -> logging.Logger:
        assert self._name, "Logger name must be provided."
        name = self._name if self._name is not None else "root"
        logger = logging.getLogger(name)
        if self._level is not None:
            logger.setLevel(self._level)
        logger.propagate = self._propagate
        for handler in self._handlers or []:
            if handler is None:
                continue
            logger.addHandler(handler)
        return logger
