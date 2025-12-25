from typing import Protocol, runtime_checkable


@runtime_checkable
class Producer(Protocol):
    """
    生产者
    """

    def produce(self, *args, **kwargs):
        pass


@runtime_checkable
class Consumer(Protocol):
    """
    消费者
    """

    def consume(self, *args, **kwargs):
        pass
