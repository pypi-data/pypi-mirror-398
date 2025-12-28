import sys
from abc import ABCMeta
from pathlib import Path
from typing import Optional, Union

import pytest
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

MODEL_CONFIG = ConfigDict(
    arbitrary_types_allowed=True, validate_by_alias=True, validate_by_name=True
)


class NumberUnit(metaclass=ABCMeta):
    unit: Optional[str] = None
    quantity: Union[int, float] = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class QuantifiedValue(NumberUnit, BaseModel):

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)

    model_config = MODEL_CONFIG
    name: Optional[str] = None


class OverideQuantifiedValue(QuantifiedValue):

    unit: str = Field(validation_alias=AliasChoices("xxx", "unit"))

    model_config = MODEL_CONFIG


class Xxx(OverideQuantifiedValue):
    pass


Yyy = OverideQuantifiedValue


def test_override_quantified_value():
    x = OverideQuantifiedValue.model_validate(dict(quantity=10, xxx="m"))
    assert x.quantity == 10
    assert x.unit == "m"

    with pytest.raises(AssertionError):

        x = Xxx.model_validate(dict(quantity=10, xxx="m"))
        assert x.quantity == 10
        assert x.unit == "m"

    y = Yyy.model_validate(dict(quantity=10, xxx="m"))
    assert y.quantity == 10
    assert y.unit == "m"


class ComplexClass:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name: str = "hello"


def test_mro():
    class Combined2(QuantifiedValue, ComplexClass):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class Combined(ComplexClass, QuantifiedValue):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # QuantifiedValue.__init__(self, **kwargs)
            # ComplexClass.__init__(self, **kwargs)

    from logis.util.visual_util import draw_mro_tree

    draw_mro_tree(Combined, Combined2)

    c = Combined()
    assert c.name == "hello"

    with pytest.raises(AssertionError):
        c2 = Combined2()
        assert c2.name == "hello"


def test_path():
    class MyModel(BaseModel):
        path: Optional[Path] = None

    m = MyModel.model_validate(dict(path="."))
    assert m.path.exists()

class TestModel(BaseModel):
    name: Optional[str] = Field(None, validation_alias=AliasChoices("名称"))
    age: Optional[int] = Field(None, validation_alias=AliasChoices("年龄", "age"))

    model_config = ConfigDict(extra="ignore")


def test_validation_alias_choices():
    form = dict(名称="张三", age="18", not_exist=True)
    m = TestModel.model_validate(form)
    assert m.name == "张三"
    assert m.age == 18

    form = dict(name="张三", 年龄="18")
    if sys.version_info >= (3, 9):
        m = TestModel.model_validate(form, by_alias=True, by_name=True)
        assert m.name == "张三"
    else:
        m = TestModel.model_validate(form)
        assert m.name is None

    assert m.age == 18

    # with pytest.raises(ValidationError):
    #     form = dict(name="张三", 年龄="18")
    #     m = TestModel.model_validate(form)
    #     if sys.version_info>=(3,9):
    #         assert m.name == "张三"
    #     else:
    #         assert m.name is None
    #     assert m.age == 18


def test_implict_type_cast():
    class MyModel(BaseModel):
        name: str
        model_config = ConfigDict(strict=False, coerce_numbers_to_str=True)

        age: Union[int, float, None] = None

    v = MyModel(name=1000, age=100.0)
    assert v.name == "1000"
    assert type(v.age) is float and v.age == 100
