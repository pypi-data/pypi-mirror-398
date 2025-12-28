from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG

from .order import IOrder


class OrderPickingConfig(BaseModel):
    """
    订单拣选配置项
    """

    # 拣选工人能同时处理的订单数量
    picker_parallel_orders: Optional[int] = None

    # # 分波次的方式
    # wave_method: Optional[Literal["订单数量", "时间段"]] = None
    # # 所选合并订单方式的值
    # value_of_wave_method: Optional[Union[UTime, int]] = None

    # 按照订单优先级排序
    sort_by_priority: bool = False

    # 智能体专用
    merge_by_sku_when_fetching: bool = True

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG


class OrderPickingStrategy(ABC):
    """
    订单拣选策略
    1. 合并size均为1时，退化为按单拣选
    2. 合并size均>1时，即是合并拣选
    3. 合并size>=1时，即是混合拣选
    """

    @abstractmethod
    def on_merge(self, *orders: Tuple[IOrder], **kwargs):
        """
        当订单发生合并时的钩子方法
        """
        pass

    @abstractmethod
    def merge(
        self, orders: List[IOrder], config: Union[OrderPickingConfig, None] = None
    ) -> List[IOrder]:
        """
        订单合并逻辑
        Args:
            orders: 待合并的订单列表
            config: 订单拣选配置
        Returns:
            合并后的订单列表
        """
        if not orders:
            return []
        if config and config.sort_by_priority:
            orders = sorted(orders, key=lambda od: od.get_priority())
        return orders
