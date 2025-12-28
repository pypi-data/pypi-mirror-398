import math
from typing import Optional

from scipy.spatial.distance import cityblock

from logis.data_type.point import Point


def manhattan_distance(start_point: Point, end_point: Point) -> float:
    """
    计算曼哈顿距离，又称为街道距离
    """
    return float(cityblock(start_point.to_tuple(), end_point.to_tuple()))
    distance = abs(start_point.x - end_point.x) + abs(start_point.y - end_point.y)
    return distance


def euclid_distance(pos1: Point, pos2: Point, precision: Optional[int] = None) -> float:
    """计算欧几里得距离"""
    v = math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)
    return round(v, precision) if precision is not None else v
