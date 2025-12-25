FORMAT_DEFAULT = (
    "%(asctime)s [%(levelname).1s] %(module)s:%(funcName)s:%(lineno)d - %(message)s"
)

FORMAT_COLORED_DEFAULT = "%(asctime)s [%(log_color)s%(levelname).1s%(reset)s] %(module)s:%(funcName)s:%(lineno)d - %(blue)s%(message)s"

FORMAT_NET_DEFAULT = (
    '%(asctime)s [%(levelname).1s] %(client_addr)s - "%(request_line)s" %(status_code)s'
)

from enum import Enum


class LoggerFormat(Enum):
    """
    日志格式
    """

    DEFAULT = FORMAT_DEFAULT
    NET_DEFAULT = FORMAT_NET_DEFAULT
    COLORED_DEFAULT = FORMAT_COLORED_DEFAULT

    def formatter_name(self) -> str:
        return self.name.lower()
