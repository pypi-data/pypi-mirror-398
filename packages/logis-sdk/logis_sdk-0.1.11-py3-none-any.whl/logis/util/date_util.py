from datetime import datetime
from enum import Enum
from typing import Union

import pandas as pd
from dateutil.parser import parse


class DateFormat(Enum):
    """
    日期格式枚举类
    """

    CHINESE_FULL = "%Y年%m月%d日%H点%M分%S秒"  # 2024年05月20日14点30分00秒
    CHINESE_SIMPLE = "%Y年%m月%d日"  # 2024年05月20日
    # 英文/国际标准格式
    ISO_DATETIME = "%Y-%m-%d %H:%M:%S"  # 2024-05-20 14:30:00（最常用）
    ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"
    ISO_DATE = "%Y-%m-%d"  # 2024-05-20
    ISO_TIME = "%H:%M:%S"  # 14:30:00
    # 简写格式
    SHORT_DATETIME = "%y-%m-%d %H:%M"  # 24-05-20 14:30
    # 美式格式
    US_DATETIME = "%m/%d/%Y %H:%M:%S"  # 05/20/2024 14:30:00


def parse_datetime(date_str: str):
    """
    主要增加了对中文日期的解析
    """
    if not date_str:  # 处理空值
        return None

    if isinstance(date_str, (pd.Timestamp)):
        return date_str.to_pydatetime()
    
    if isinstance(date_str, (datetime)):
        return date_str


    format = [
        "%Y年%m月%d日 %H:%M:%S",  # 年月日格式
        "%Y年%m月%d日",  # 年月日格式（仅日期）
    ]
    for f in format:
        try:
            return datetime.strptime(date_str, f)
        except ValueError:
            continue
    return parse(date_str)


def format_datetime(
    dt: datetime, fmt: Union[DateFormat, str] = DateFormat.ISO_DATETIME
):
    """
    将 datetime 对象转换为中文日期格式
    """
    dt = parse_datetime(dt)
    if isinstance(fmt, DateFormat):
        fmt = fmt.value
    return dt.strftime(fmt)
