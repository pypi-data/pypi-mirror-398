import json
import time
from typing import Any, Dict, Generic, Optional, TypeVar

import pytest
from pydantic import BaseModel

from logis.data_type import Number
from logis.data_type.unitable import (
    Capacity,
    Length,
    NumberUnit,
    QuantifiedValue,
    Speed,
    SpeedVector,
    merge_quantified_value,
)


def test_number():
    assert isinstance(10, Number)
    assert isinstance(1.1, Number)


def test_capacity():
    x = Capacity.parse_tuple([10, "箱"])
    assert isinstance(x, Capacity)
    x = Capacity.parse_tuple([10, "箱"])
    assert isinstance(x, Capacity)
    assert isinstance(x, NumberUnit)
    assert isinstance(x, QuantifiedValue)


def test_speed():
    x = Speed.parse_str("1|m/s")
    assert isinstance(x, Speed)
    assert x.quantity == 1
    assert x.unit == "m/s"

    y: SpeedVector = []

    assert type(y) is list
    # 这里没办法判断是SpeedVector类型
    assert type(y) is not SpeedVector


def test_length():
    x = Length(quantity=2, unit="cm")
    y = Length.parse_str("10|cm")

    z1 = x + y
    assert z1.quantity == 12
    z2 = x - y
    assert z2.quantity == -8
    print(z1, z2)


def test_merge_value():
    x = Length.parse_tuple([10, "m"])
    y = Length.parse_tuple([2.1, "cm"])
    z = Length.parse_tuple([20, "cm"])
    try:
        merge_quantified_value([x, y])
    except Exception as e:
        print(e)

    a = merge_quantified_value([x, y, z])
    assert a.quantity == 10.221
    assert a.unit == "m"

    a = merge_quantified_value([x, y, z], target_unit="cm")
    assert a.quantity == 1022.1
    assert a.unit == "cm"


def test_compare():

    a = QuantifiedValue(quantity=10)
    b = Capacity(quantity=11)
    assert a < b
    assert b > a


def test_parse():
    v = QuantifiedValue.model_validate({"quantity": 10, "unit": "m"})
    assert v.quantity == 10
    assert v.unit == "m"


def test_deserialize():
    T = TypeVar("T")
    from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG

    class MyEvent(BaseModel):
        event_type: str
        timestamp: Optional[float] = None

    class MyGenericEvent(MyEvent, Generic[T]):

        data: T

        model_config = DEFAULT_PYDANTIC_MODEL_CONFIG

    class InnerData(BaseModel):
        a: int
        b: int

    json_strings = [
        json.dumps({"event_type": "test", "timestamp": i, "data": {"a": i, "b": i**2}})
        for i in range(2, 100000)
    ]

    with pytest.raises(ValueError):
        MyGenericEvent[bytes].model_validate_json(json_strings[0])
        start = time.time()
        for json_string in json_strings:
            m = MyGenericEvent[bytes].model_validate_json(json_string)
            assert isinstance(m.data, bytes)
        dt = time.time() - start
        print(f"bytes deserialize time: {dt}")

    start = time.time()
    # for json_string in json_strings:
    #     m = MyGenericEvent[Dict[Any, Any]].model_validate_json(json_string)
    #     assert isinstance(m.data, dict)
    dt = time.time() - start
    print(f"dict deserialize time: {dt}")

    start = time.time()
    # for json_string in json_strings:
    #     m = MyGenericEvent[InnerData].model_validate_json(json_string)
    #     assert isinstance(m.data, InnerData)
    dt = time.time() - start
    print(f"inner data deserialize time: {dt}")

    start = time.time()
    for json_string in json_strings:
        m = MyEvent.model_validate_json(json_string)
        assert m
    dt = time.time() - start
    print(f"inner data deserialize time: {dt}")
