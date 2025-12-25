from abc import ABC, ABCMeta
from collections import defaultdict
from typing import Dict, Generic, Protocol, TypeVar, Union, runtime_checkable

from logis.data_type import NumberType, NumberUnit, SpatialProps, T
from logis.util.num_util import get_numeric_value


class Shape(metaclass=ABCMeta):
    """
    形状，例如路径、节点等
    """

    @property
    def rotation_value(self):
        v = get_numeric_value(self.props.rotation) if self.props else None
        return v or 0

    def __init__(self, **kwargs):
        self.props: Union[SpatialProps, None] = None


from ._event import *
from ._queue import *
from .container import *
