from abc import ABC, abstractmethod
from datetime import timedelta
from typing import List, Optional
from uuid import uuid4

import pandas
from pydantic import BaseModel

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG

from .order import *


class WaveGroupingConfig(BaseModel):
    """
    波次划分配置
    """

    # 批次大小
    batch_size: Optional[int] = None
    # 时间窗口
    time_interval: Optional[timedelta] = None
    # 指定各个时间段
    time_index: Optional[pandas.DatetimeIndex] = None

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG


class WaveGroupingStrategy(ABC):
    """
    波次划分策略
    """

    @abstractmethod
    def group(
        self, orders: List[IOrder], config: WaveGroupingConfig
    ) -> List[List[IOrder]]:
        """
        对订单列表进行波次划分
        Args:
            orders: 订单列表
            config: 波次拣选配置
        Returns:
            波次列表
        """
        pass

    def _generate_wave_id(self, waves: List[List[IOrder]]) -> Optional[Union[str, int]]:
        """
        生成波次ID,默认是uuid4
        """
        if not waves:
            return None
        for i, wave in enumerate(waves):
            wave_id = str(uuid4())
            for od in wave:
                od.set_wave_id(wave_id)


class TimeWindowWaveStrategy(WaveGroupingStrategy):
    """
    基于时间窗口的波次划分策略
    """

    def group(self, orders, config):
        if not orders:
            return []
        orders = sorted(orders, key=lambda od: od.get_order_time())

        min_time, left = orders[0].get_order_time(), orders[-1].get_order_time()
        time_index = config.time_index or pandas.date_range(
            min_time, left, freq=config.time_interval
        )
        waves: List[List[IOrder]] = []
        count = 0
        for i, left in enumerate(time_index):
            right = time_index[i + 1] if i + 1 < len(time_index) else None
            wave = []
            for od in orders[count:]:
                if od.get_order_time() >= left and (
                    right is None or od.get_order_time() < right
                ):
                    wave.append(od)
                else:
                    break
            if wave:
                waves.append(wave)
                count += len(wave)

        self._generate_wave_id(waves)
        return waves


class WaveSizeStrategy(WaveGroupingStrategy):
    """
    基于波次大小的波次划分策略
    """

    def group(self, orders, config):
        if not orders:
            return []
        orders = sorted(orders, key=lambda od: od.get_order_time())
        waves: List[List[IOrder]] = []
        wave = []
        for od in orders:
            if len(wave) >= config.batch_size:
                waves.append(wave)
                wave = []
            wave.append(od)
        if wave:
            waves.append(wave)
        self._generate_wave_id(waves)
        return waves
