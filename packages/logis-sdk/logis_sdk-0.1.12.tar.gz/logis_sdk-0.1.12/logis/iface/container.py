from abc import ABCMeta
from collections import defaultdict
from typing import Dict, Protocol, runtime_checkable

from logis.data_type import NumberType, NumberUnit


class StoreResult(metaclass=ABCMeta):
    """
    存储结果
    """

    pass


class RetrieveResult(metaclass=ABCMeta):
    """
    检索结果
    """

    pass


class StoreStrategy(metaclass=ABCMeta):
    """
    存储策略
    """


@runtime_checkable
class Storable(Protocol):
    # class Storable(metaclass=ABCMeta):
    """
    可存储的

    使用鸭子类型实现，相比ABC更灵活
    """

    def pre_store(self, *args, **kwargs):
        pass

    def pre_retrieve(self, *args, **kwargs):
        pass

    def store(self, *args, **kwargs) -> StoreResult:
        pass

    def retrieve(self, *args, **kwargs) -> RetrieveResult:
        pass


class QuantifiedValueContainer(Storable):

    def __init__(self):
        self.__container__: Dict[str, Dict[str, NumberType]] = defaultdict(
            defaultdict(0)
        )

    def store(self, v: "NumberUnit"):
        self.__container__[v.kind][v.unit] += v.quantity

    def retrieve(self, v: "NumberUnit"):
        self.__container__[v.kind][v.unit] -= v.quantity
