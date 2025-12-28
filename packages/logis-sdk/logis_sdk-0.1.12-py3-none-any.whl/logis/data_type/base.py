from decimal import Decimal
from fractions import Fraction
from numbers import Number
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import humps
from pydantic import BaseModel, ConfigDict, Field

StringNumber = str

BaseNumberType = Union[int, float]
NumberType = Union[Decimal, int, float, Fraction, Number]

ComponentIntId = int

ComponentStrId = str

ComponentId = Union[ComponentIntId, ComponentStrId]

TmpId = Union[int, str]


T = TypeVar("T")
Predicate = Callable[[T], bool]

Unit = NewType("Unit", str)

# 倍率计算器，输入源单位、目标单位，输出倍率
RatioComputer = Callable[[Unit, Unit], Decimal]

EventType = NewType("EventType", str)
TaskType = NewType("TaskType", str)

TuplePoint = Tuple[Optional[Number], Optional[Number], Optional[Number]]

# 这里不要随便改，如果不满足自己的需求，可以新建配置
DEFAULT_PYDANTIC_MODEL_CONFIG = ConfigDict(
    strict=False,
    arbitrary_types_allowed=True,
    extra="ignore",
    validate_by_alias=True,
    validate_by_name=True,
    coerce_numbers_to_str=True,
    alias_generator=humps.camelize,
    populate_by_name=True,
)
class CallableInput(BaseModel):
    args: Tuple = Field(default_factory=tuple)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def of(*args, **kwargs):
        return CallableInput(args=args, kwargs=kwargs)


class InvokeResult:
    def __init__(self):
        self.is_generator = False
        self.return_value: Any = None
        self.yield_values: Any = []

    @staticmethod
    def returns(value: Any):
        self = InvokeResult()
        self.return_value = value
        return self


class Data(BaseModel, Generic[T]):
    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG
    type: str
    value: T
    tags: Optional[List[str]] = None
    description: Optional[str] = None


from abc import ABCMeta
from enum import EnumMeta


class ABCEnumMeta(EnumMeta, ABCMeta):
    """
    适用于enum类继承但是提示metaclass冲突的情况
    1. 置顶metaclass为本类即可
    """

    pass
