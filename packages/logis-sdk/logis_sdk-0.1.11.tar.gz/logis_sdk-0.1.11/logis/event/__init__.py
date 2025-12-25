from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel
from pyee import EventEmitter
from pyee.base import Handler

from logis.ctx import Context
from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG

T = TypeVar("T")


class EventContext(BaseModel, Generic[T]):
    # 事件所携带的数据
    payload: Optional[T] = None
    # 事件源ID
    source_id: Optional[str] = None
    # 事件目标ID
    target_id: Optional[Any] = None
    # 事件名称
    name: str
    # 附加数据
    extra: Any = None

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG


class EventBus(Context):
    """
    事件总线，支持监听、发出事件
    """

    emitter = EventEmitter()

    @classmethod
    def get_event_emitter(cls) -> EventEmitter:
        return cls.emitter

    @classmethod
    def emit(cls, event_name: str, *args, **kwargs):
        cls.get_event_emitter().emit(event_name, *args, **kwargs)

    @classmethod
    def on(cls, event_name: str, func: Handler):
        cls.get_event_emitter().on(event_name, func)

    @classmethod
    def add_listener(cls, event_name: str, listener: Handler):
        cls.get_event_emitter().add_listener(event_name, listener)


class EventBaseModel(BaseModel, Generic[T]):
    """
    事件基础结构
    """

    # 设计为x.y.z的形式
    event_type: str

    value: Optional[T] = None

    source_id: Optional[str] = None

    # 事件发生的时间
    event_time: float

    created_at: Optional[datetime] = None
