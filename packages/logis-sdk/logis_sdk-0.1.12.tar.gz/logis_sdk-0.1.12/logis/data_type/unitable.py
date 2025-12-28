from abc import ABCMeta, abstractmethod
from collections import defaultdict
from fractions import Fraction
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG as MODEL_CONFIG
from logis.data_type import NumberType, Unit

from .point import *


class NumberUnit(metaclass=ABCMeta):

    quantity: NumberType
    unit: Union[str, Unit, None] = None

    # 自定义倍率转换器
    _unit_config_: Optional["UnitConfig"] = None

    @property
    def kind(self):
        """
        默认情况下返回类名,实际使用时可以重写
        """
        return self.__class__.__name__

    @abstractmethod
    def model_dump(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def model_validate(cls, data: Dict[str, Any]) -> "NumberUnit":
        pass

    def __auto_validate__(self, other: "NumberUnit"):
        if self._unit_config_ is None:
            assert (
                self.unit == other.unit
            ), f"unit must be the same, but {self.unit} != {other.unit}"
        else:
            other = unify_quantified_value(
                other, self.unit, unit_config=self._unit_config_
            )
        return other

    def __sub__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        dc = self.model_dump()
        dc["quantity"] = self.quantity - other.quantity
        return type(self).model_validate(dc)

    def __add__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        dc = self.model_dump()
        dc["quantity"] += other.quantity
        return type(self)(**dc)

    def __truediv__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        # TODO: 处理精度问题
        return self.quantity / other.quantity

    def __mul__(self, times: Union[int, float]):
        data = self.model_dump()
        data["quantity"] *= times
        return type(self).model_validate(data)

    def __gt__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        return self.quantity > other.quantity

    def __lt__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        return self.quantity < other.quantity

    def __eq__(self, other: "NumberUnit"):
        if not other:
            return False
        other = self.__auto_validate__(other)
        return self.quantity == other.quantity

    def __ge__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        return self.quantity >= other.quantity

    def __le__(self, other: "NumberUnit"):
        other = self.__auto_validate__(other)
        return self.quantity <= other.quantity

    @property
    def value(self):
        return self.quantity

    @value.setter
    def value(self, new_value):
        self.quantity = new_value

    @classmethod
    def parse_tuple(cls, input: Tuple[NumberType, Unit]):
        """
        解析形如[1,"个"]的数据
        """
        return cls(quantity=input[0], unit=input[1])

    @classmethod
    def parse_str(cls, input: str, delimiter="|", number_type=float):
        """
        解析形如1|m/s的数据
        """
        if not input:
            return None
        tmps = input.strip().split(delimiter)
        assert len(tmps) == 2, "unexpected format: " + input
        return cls(quantity=number_type(tmps[0]), unit=tmps[1])

    @classmethod
    def of(cls, num: NumberType, unit: Optional[str] = None):
        return cls(quantity=num, unit=unit)

    def increase(self, num: NumberType) -> None:
        self.quantity += num

    def decrease(self, num: NumberType) -> None:
        self.quantity -= num


# 量化值
class QuantifiedValue(BaseModel, NumberUnit):
    model_config = MODEL_CONFIG

    name: Optional[str] = None


class Capacity(QuantifiedValue):
    pass


class Length(QuantifiedValue):
    pass


class Speed(QuantifiedValue):
    pass


SpeedVector = Tuple[Optional[Speed], Optional[Speed], Optional[Speed]]


class ThreeDimensionalVelocity(BaseModel):
    """
    使用x,y,z表示的三维速度
    """

    model_config = MODEL_CONFIG

    x: Optional[Speed] = None
    y: Optional[Speed] = None
    z: Optional[Speed] = None

    @classmethod
    def of(
        cls,
        x: Optional[NumberType] = None,
        y: Optional[NumberType] = None,
        z: Optional[NumberType] = None,
        unit: Optional[str] = None,
    ):
        return cls(
            x=None if x is None else Speed.of(x, unit),
            y=None if y is None else Speed.of(y, unit),
            z=None if z is None else Speed.of(z, unit),
        )


class Time(QuantifiedValue):
    """
    时间
    """

    pass


def get_time(l: Length, v: Speed):
    """
    距离/速度=时间
    TODO：处理单位
    """
    assert l.value is not None, "length is not specified"
    assert v.value is not None, "speed is not specified"
    assert v.value != 0, "speed cannot be zero"
    return abs(l.value / v.value)


def get_time_3d(delta_distance: Point, v: ThreeDimensionalVelocity):
    """
    分别计算各维度的时间，取最大值
    """
    lz, ly, lx, lunit = (
        delta_distance.z,
        delta_distance.y,
        delta_distance.x,
        delta_distance.unit,
    )
    return max(
        0 if not lx else get_time(Length(quantity=lx, unit=lunit), v.x),
        0 if not ly else get_time(Length(quantity=ly, unit=lunit), v.y),
        0 if not lz else get_time(Length(quantity=lz, unit=lunit), v.z),
    )


DEFAULT_UNIT_CONFIG = dict()

from pint import UnitRegistry, set_application_registry

# 1. 初始化单位注册表
ureg = UnitRegistry()
# 设置为全局注册表（避免重复注册）
set_application_registry(ureg)

Quantity = ureg.Quantity

# 2. 将中文与内置单位关联
# 长度单位
ureg.define("米 = meter")
ureg.define("分米 = decimeter")
ureg.define("厘米 = centimeter")
ureg.define("毫米 = millimeter")
ureg.define("纳米 = nanometer")
ureg.define("千米 = kilometer")
ureg.define("公里 = kilometer")

# 重量单位
ureg.define("千克 = kilogram")
ureg.define("克 = gram")
ureg.define("吨 = tonne")

# 时间单位
ureg.define("年 = year")
ureg.define("月 = month")
ureg.define("周 = week")
ureg.define("星期 = week")
ureg.define("天 = day")
ureg.define("小时 = hour")
ureg.define("分钟 = minute")
ureg.define("秒 = second")

# 温度单位
ureg.define("摄氏度 = degree_Celsius")
ureg.define("华氏度 = degree_Fahrenheit")


def get_unit_ratio(src: Unit, dst: Unit, src_quantity: NumberType = 1) -> float:
    """
    获取 src 到 dst 的倍率
    """
    src, dst = src.replace("每", "/"), dst.replace("每", "/")
    return ureg.Quantity(src_quantity, src).to(dst).magnitude


class UnitConfig(dict):
    """
    有关单位的配置项
    """

    def get_ratio(self, src: Unit, dst: Unit, src_quantity: NumberType = 1) -> Fraction:
        """
        获取 src 到 dst 的倍率
        """
        if src == dst:
            return Fraction(src_quantity, 1)
        if src in self and dst in self:
            return Fraction(self[dst] * src_quantity, self[src])
        try:
            return Fraction(get_unit_ratio(src, dst, src_quantity=src_quantity))
        except:
            pass
        raise ValueError(f"unknown unit: {src} or {dst}")

    def get_float_ratio(self, src: Unit, dst: Unit, *args, **kwargs) -> float:
        """
        获取 src 到 dst 的倍率
        """
        return float(self.get_ratio(src, dst, *args, **kwargs))

    def get_int_ratio(self, src: Unit, dst: Unit, *args, **kwargs) -> int:
        """
        获取 src 到 dst 的倍率
        """
        return int(self.get_ratio(src, dst, *args, **kwargs))

    def alias(self, unit: Unit, *aliases: Unit):
        """
        为单位添加别名
        """
        for alias in aliases:
            self[alias] = self.get(unit)
        return self

    def __or__(self, value: Dict):

        obj = dict(value)
        obj.update(self)

        return UnitConfig(obj)


class UnitConfigBuilder:
    """
    单位配置构建器
    """

    def __init__(self, base_unit: Unit):
        self.__unit_config__ = UnitConfig([[base_unit, 1]])

    @staticmethod
    def with_base(unit: Unit):
        return UnitConfigBuilder(unit)

    def add(self, unit: Unit, multiplier_to_base: NumberType):
        """
        Args:
            unit: 单位
            multiplier_to_base: 转换到1base单位所需要的倍率，例如：base为1m时，cm到1m需要100倍
        """
        self.__unit_config__[unit] = multiplier_to_base
        return self

    def alias(self, unit: Unit, *aliases: Unit):
        """
        为单位添加别名
        """
        self.__unit_config__.alias(unit=unit, *aliases)
        return self

    def build(self) -> UnitConfig:
        return self.__unit_config__


TIME_UNIT_CONFIG = UnitConfig(
    天=1, 小时=24, 分钟=24 * 60, 秒=24 * 60 * 60, 毫秒=24 * 60 * 60 * 10**3
)
VOLUME_UNIT_CONFIG = UnitConfig(kl=Fraction(1, 10**3), l=1, dl=10, cl=100, ml=10**3)
LENGTH_UNIT_CONFIG = UnitConfig(
    km=Fraction(1, 10**3), m=1, dm=10, cm=100, mm=10**3, nm=10**9
)

DEFAULT_UNIT_CONFIG = TIME_UNIT_CONFIG | VOLUME_UNIT_CONFIG | LENGTH_UNIT_CONFIG


def unify_quantified_value(
    self: QuantifiedValue,
    target_unit: Optional[Unit] = None,
    unit_config: UnitConfig = DEFAULT_UNIT_CONFIG,
    modify_ref: bool = False,
):
    """
    单位转换
    """
    same_unit = self.unit == target_unit
    if unit_config is None:
        assert same_unit, "unit must be the same if no radio_computer given"
    else:
        ratio = 1 if same_unit else unit_config.get_ratio(self.unit, target_unit)
        if modify_ref:
            self.quantity = self.quantity * ratio
            self.unit = target_unit
            return self
        # 上面这种方式能尽可能避免属性丢失，但修改的是原始对象
        dc = {
            **self.model_dump(),
            **dict(quantity=self.quantity * ratio, unit=target_unit),
        }
        return type(self)(**dc)


def merge_quantified_value(
    items: List[QuantifiedValue],
    unit_config: Optional[UnitConfig] = DEFAULT_UNIT_CONFIG,
    target_unit: Optional[Unit] = None,
):
    """
    将所有的物理量合并，这里是假定所有的物理量都是同类，例如：全是长度，而不是既有长度又有速度

    Args:
        items: 待合并项
        ratio_computer: 倍率计算器
        target_unit: 目标单位，如果未指定，默认使用数组的第一个条目的单位
    """
    assert items, "item length need to be at least 1"
    target_unit = target_unit or items[0].unit
    if len(items) != 2:
        return reduce(
            lambda a, b: merge_quantified_value(
                [a, b], target_unit=target_unit, unit_config=unit_config
            ),
            items,
        )
    self, other = unify_quantified_value(
        items[0], target_unit=target_unit, unit_config=unit_config
    ), unify_quantified_value(
        items[1], target_unit=target_unit, unit_config=unit_config
    )
    dc = {
        **self.model_dump(),
        **dict(quantity=self.quantity + other.quantity, unit=target_unit),
    }
    return type(self)(**dc)


def group_merge_quantified_value(items: List[QuantifiedValue]) -> List[QuantifiedValue]:
    """
    按照单位分组，并合并同类单位物理量
    """
    result = []
    unit_items_map = defaultdict(list)
    for item in items:
        unit_items_map[item.unit].append(item)
    for _, tmps in unit_items_map.items():
        result.append(merge_quantified_value(tmps))
    return result
