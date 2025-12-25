import logging
import logging.config
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from logis._log import LoggerBuilder, get_default_dict_config_builder
from logis._log.util import DictConfigBuilder


def do_log(log: logging.Logger):
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")
    try:
        1 / 0
    except Exception as e:
        log.exception("This is an exception message: %s", e)


LOGGER_NAME = "test_logger"

demo_logger = (
    LoggerBuilder()
    .dir("./logs")
    .name(LOGGER_NAME)
    .level(logging.INFO)
    .add_handler(
        StreamHandler,
        filters=[
            lambda record: record.levelno >= logging.WARNING,
        ],
    )
    .add_handler(RotatingFileHandler, filename="test")
    .build()
)


def test_logger_builder():
    do_log(demo_logger)


def test_dict_config_builder():
    dict_config = DictConfigBuilder().logger(demo_logger).build()
    print(dict_config)
    logging.config.dictConfig(dict_config)
    log = logging.getLogger(LOGGER_NAME)
    do_log(log)


def test_default_dict_config_builder():
    dict_config = get_default_dict_config_builder().build()
    print(dict_config)
    logging.config.dictConfig(dict_config)
    log = logging.getLogger("app")
    do_log(log)


if __name__ == "__main__":
    test_logger_builder()
