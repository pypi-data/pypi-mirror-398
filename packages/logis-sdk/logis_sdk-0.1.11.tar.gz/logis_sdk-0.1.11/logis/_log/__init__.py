from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .builder import *
from .fmt import *
from .handler import *
from .util import *


def get_default_dict_config_builder():
    """
    默认内置
    1. 名为console的控制台Logger，日志级别INFO，彩色输出
    2. 名为app的Logger，日志级别INFO，输出到控制台和文件
    """
    return (
        DictConfigBuilder()
        .handler(get_default_console_handler(), name="console")
        .handler_dict(
            HandlerDictConfig(
                name="error_file_handler",
                clazz=RotatingFileHandler,
                level=logging.ERROR,
                filename="error.log",
                formatter=LoggerFormat.DEFAULT.formatter_name(),
            )
        )
        .handler_dict(
            HandlerDictConfig(
                name="info_file_handler",
                clazz=TimedRotatingFileHandler,
                level=logging.INFO,
                filename="info.log",
                formatter=LoggerFormat.DEFAULT.formatter_name(),
            )
        )
        .logger_dict(
            LoggerDictConfig(
                name="root",
                level=logging.WARNING,
                handlers=["console", "error_file_handler"],
            )
        )
        .logger_dict(
            LoggerDictConfig(
                name="app",
                level=logging.INFO,
                handlers=["console", "info_file_handler", "error_file_handler"],
            )
        )
    )
