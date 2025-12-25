import math

from logis.data_type.unitable import DEFAULT_UNIT_CONFIG
from logis.data_type.unitable import Quantity as Q_
from logis.data_type.unitable import get_unit_ratio


def test_unit_config():
    unit_config = DEFAULT_UNIT_CONFIG
    assert unit_config.get_ratio("m", "cm", 10) == 1000
    assert unit_config.get_ratio("km", "cm") == 1000 * 100


def test_unit():
    speed = Q_(60, "千米") / Q_(1, "小时")
    assert math.floor(speed.to("米/秒").magnitude) == 16

    assert Q_(36000, "千米/小时").to("千米/秒").magnitude == 10
    assert Q_(36000, "km/h").to("km/s").magnitude == 10

    assert get_unit_ratio("千米每小时", "千米/秒", 36000) == 10

    assert int(get_unit_ratio("年", "天")) == 365
    assert int(get_unit_ratio("年", "月")) == 12
    assert int(get_unit_ratio("月", "天")) == 30
    assert get_unit_ratio("天", "小时") == 24
    assert get_unit_ratio("星期", "天") == 7
    assert get_unit_ratio("周", "天") == 7

    assert get_unit_ratio("吨", "千克") == 1000

    assert get_unit_ratio("千米", "米") == 1000

    assert round(get_unit_ratio("摄氏度", "华氏度"), 1) == 1.8
