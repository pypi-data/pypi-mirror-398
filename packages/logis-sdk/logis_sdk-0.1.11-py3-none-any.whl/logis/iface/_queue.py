from typing import Protocol, TypeVar, runtime_checkable

from logis.data_type import T


@runtime_checkable
class IQueue(Protocol[T]):
    """
    队列接口
    """

    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize)

    def put(self, item: T, *args, **kwargs):
        pass

    def put_nowait(self, item: T):
        pass

    def get(self, *args, **kwargs) -> T:
        pass

    def get_nowait(self) -> T:
        pass

    def qsize(self) -> int:
        pass

    def empty(self) -> bool:
        pass

    def full(self) -> bool:
        pass


QueueType = TypeVar("QueueType", bound=IQueue[T])
