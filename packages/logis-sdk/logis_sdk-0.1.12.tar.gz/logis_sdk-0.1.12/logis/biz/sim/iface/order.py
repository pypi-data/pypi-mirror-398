from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union


class IOrder(ABC):

    @abstractmethod
    def get_priority(self) -> int:
        """
        订单优先级,数字越小优先级越高
        """
        pass

    def get_wave_id(self) -> Union[str, int, None]:
        """
        波次ID
        """
        return None

    @abstractmethod
    def set_wave_id(self, wave_id: Union[str, int, None]):
        """
        设置波次ID
        """
        pass

    @abstractmethod
    def get_order_time(self) -> datetime:
        """
        订单时间
        """
        pass
