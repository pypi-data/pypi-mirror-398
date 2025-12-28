from typing import Protocol, runtime_checkable

from logis.data_type import Point
from logis.data_type.unitable import TIME_UNIT_CONFIG, UnitConfigBuilder


def test_point():
    p1 = Point(1, 2)
    p2 = Point(1, 2, 3)
    p3 = Point([1, 2, 3])
    p4 = Point([10, 1])
    for p in [p1, p2, p3, p4]:
        print(p)

    assert p1 - p2 == Point(0, 0, -3)
    assert p3 - p4 == Point(-9, 1, 3)
    assert Point() - Point() == Point()


def test_unit_config_builder():
    unit_config = UnitConfigBuilder.with_base("m").add("cm", 100).build()
    ratio = unit_config.get_ratio("m", "cm")
    assert ratio == 100
    ratio = unit_config.get_float_ratio("cm", "m")
    assert ratio == 0.01
    ratio = unit_config.get_ratio("m", "m")
    assert ratio == 1

    x = TIME_UNIT_CONFIG | unit_config

    ratio = x.get_ratio("秒", "毫秒")
    assert ratio == 1000


def test_protocal():
    @runtime_checkable
    class MyProtocal(Protocol):
        pass

    class SomeClass:
        pass

    assert isinstance(SomeClass(), MyProtocal)
