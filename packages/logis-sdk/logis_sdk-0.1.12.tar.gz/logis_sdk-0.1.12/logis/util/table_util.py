import pandas as pd
import tabulate


def to_pretty_string(df: pd.DataFrame) -> str:
    """
    将DataFrame转换为易读的字符串格式
    Args:
        df: 输入的DataFrame
    Returns:
        易读的字符串格式
    """
    return tabulate.tabulate(df, headers="keys", tablefmt="fancy_grid")
