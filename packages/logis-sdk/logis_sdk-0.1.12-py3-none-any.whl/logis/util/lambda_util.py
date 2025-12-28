import asyncio
import inspect
from types import GeneratorType
from typing import Any, Coroutine

from logis.data_type import InvokeResult


def generate_all(v: GeneratorType):
    """
    执行生成器函数，返回所有yield值
    :param v: 生成器函数
    :return: 生成器函数返回值,包括yield出的值和函数的返回值
    """
    assert isinstance(v, GeneratorType)

    result = InvokeResult()
    result.is_generator = True
    try:
        while True:
            result.yield_values.append(next(v))
    except StopIteration as e:
        result.return_value = e.value
    return result


def invoke_async_func(coroutine: Coroutine[Any, Any, Any]):
    from logis.util.io_util import get_or_new_event_loop

    loop = get_or_new_event_loop(auto_set=True)
    return loop.run_until_complete(coroutine)


def invoke(func, *args, **kwargs):
    """
    调用函数，返回结果,支持普通函数、生成器函数

    :param func: 函数
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 函数返回值
    """
    result = func(*args, **kwargs)
    if inspect.iscoroutinefunction(func):
        result = invoke_async_func(result)
    elif isinstance(result, GeneratorType):
        return generate_all(result)
    return InvokeResult.returns(result)
