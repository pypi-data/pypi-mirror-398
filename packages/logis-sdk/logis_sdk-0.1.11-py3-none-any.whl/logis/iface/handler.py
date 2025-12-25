from abc import ABC, ABCMeta, abstractmethod


class IHandler(ABC):
    """
    处理接口
    """

    @abstractmethod
    def handle(self, *args, **kwargs):
        """
        处理数据
        """
