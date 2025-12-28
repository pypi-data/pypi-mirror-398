import logging
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from colorlog import ColoredFormatter

from .fmt import LoggerFormat


def get_default_console_handler(level=logging.INFO) -> StreamHandler:
    handler = StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(fmt=LoggerFormat.COLORED_DEFAULT.value))
    handler.setLevel(level)
    return handler
