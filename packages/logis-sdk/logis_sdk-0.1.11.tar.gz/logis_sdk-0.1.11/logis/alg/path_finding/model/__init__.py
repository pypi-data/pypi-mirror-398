from typing import Any, Callable, Dict, List, NewType, Optional, Union

from networkx import DiGraph, Graph
from pydantic import BaseModel, Field

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG, Point

PathFindingAlgorithmType = NewType("PathFindingAlgorithmType", str)

AlgorithmTypeResolver = Callable[[Any], PathFindingAlgorithmType]

# TODO: 完善名字、补充类型
A_STAR_ALGORITHM = PathFindingAlgorithmType("a_star")
DIJKSTRA_ALGORITHM = PathFindingAlgorithmType("dijkstra")


class PathFindingInput(BaseModel):
    # 算法名称，分流用
    alg: Union[PathFindingAlgorithmType, str, None] = None

    # 图对象，可以是无向图或有向图
    graph: Union[Graph, DiGraph, None] = None

    # 起点
    start: Point
    # 终点
    end: Point

    # 排除的点或障碍点
    excluded_vertices: List[Point] = []

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG


class PathFindingOutput(BaseModel):
    """
    寻路输出结果
    可以输出具体路径，也可以只输出下一点
    """

    # 是否成功
    success: bool

    # 具体路径
    path: Optional[List[Point]] = None

    next_point: Optional[Point] = None

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG
