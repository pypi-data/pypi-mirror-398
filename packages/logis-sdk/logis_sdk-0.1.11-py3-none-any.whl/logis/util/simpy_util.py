import logging
import time
from abc import ABC
from typing import Any, List, Optional, Union

import simpy
import simpy.resources
import simpy.resources.resource
from simpy.events import URGENT


def try_put(
    env: simpy.Environment,
    container: simpy.Container,
    amount: Union[int, float],
    timeout: Optional[int] = None,
):
    x = container.put(amount)
    if timeout:
        x = x | env.timeout(timeout)
    v = yield x
    return v


def get_free_capacity(container: simpy.Container):
    """
    获取容器的空闲容量
    Args:
        container (simpy.Container): 容器
    Returns:
        int | float: 空闲容量
    """
    # TODO：这里预先触发存取操作，可能会有性能影响，后续可考虑分离出去
    container._trigger_put(None)
    container._trigger_get(None)
    return container.capacity - container.level


def resize_container(
    container: simpy.Container, capacity: Union[int, float], is_delta=False
):
    """
    调整容器容量
    Args:
        container (simpy.Container): 容器
        capacity (int | float): 新容量
        is_delta (bool, optional): 是否是增量调整. 默认False
    """
    old_capacity = container.capacity
    capacity = capacity + old_capacity if is_delta else capacity
    dx = capacity - old_capacity
    if not dx:
        return
    # 如果是减容，先触发取操作
    if dx < 0:
        container._trigger_get(None)
        assert (
            container.level <= capacity
        ), f"容器当前等级{container.level}大于新容量{capacity}，无法完成减容"
    container._capacity = capacity
    if dx > 0:
        container._trigger_put(None)


def resource_to_dict(resource: Any):
    if isinstance(resource, simpy.Container):
        return dict(level=resource.level, capacity=resource.capacity)
    if isinstance(resource, simpy.Resource):
        return dict(level=resource.count, capacity=resource.capacity)
    if isinstance(resource, simpy.Store):
        return dict(level=len(resource.items), capacity=resource.capacity)
    print("unexpected type:" + resource)


def schedule_event_at(
    env: simpy.Environment, at: Union[float, int], ev: Optional[simpy.Event] = None
):
    """
    计划在指定时间触发事件
    Args:
        env (simpy.Environment): 仿真环境
        at (float | int): 触发时间
        ev (simpy.Event | None, optional): 事件. 默认None
    """
    if at < env.now:
        return
    if ev is None:
        ev = env.event()
        ev._ok = True
        ev._value = None
    env.schedule(ev, URGENT, at - env.now)
    return ev


def interrupt_on_event(env: simpy.Environment, ev: simpy.Event):
    """
    当事件触发时中断仿真
    Args:
        env (simpy.Environment): 仿真环境
        ev (simpy.Event): 事件
    """

    raise NotImplementedError("interrupt_on_event not implemented")


def interrupt_if_timeout(
    env: simpy.Environment,
    timeout: Optional[float] = None,
    check_interval: float = 10,
    exit_signal: Optional[simpy.Event] = None,
):
    """
    根据仿真真实运行时间是否超时来中断仿真

    Args:
        env (simpy.Environment): 仿真环境
        timeout (float | None, optional): 最大运行时间. 默认不限时
        check_interval (float, optional): 这个时间是仿真中的时间
        exit_signal (simpy.Event | None, optional): 外部信号，用于外部中断仿真. 默认不使用.
    """

    def inner():
        cpu_start_time = time.time()
        while True:
            dt = time.time() - cpu_start_time
            if timeout is not None and dt > timeout:
                raise simpy.Interrupt(
                    f"仿真运行时间{dt}超过最大运行时间{timeout}，强制退出"
                )
            if exit_signal and exit_signal.triggered:
                raise simpy.Interrupt(f"外部信号{exit_signal}触发，强制退出")
            yield env.timeout(check_interval)

    return env.process(inner())


def has_no_event_left(env: simpy.Environment):
    """
    判断指定环境中是否还有未处理的事件
    """
    return not env._queue and not env.active_process

def run_until(
    env: simpy.Environment,
    exit_signal: Optional[simpy.Event] = None,
    max_sim_time: Optional[float] = None,
    extra_events: Optional[List[simpy.Event]] = None,
):
    events = []
    if exit_signal:
        events.append(exit_signal)
    if max_sim_time is not None:
        dt = max(0, max_sim_time - env.now)
        events.append(env.timeout(dt))
    if extra_events:
        events.extend(extra_events)
    until = env.any_of(events) if events else None
    try:
        return env.run(until=until)
    except Exception as e:
        if has_no_event_left(env):
            logging.warning(
                "error happens but there is no event left, will ignore: %s", e
            )
            return
        raise e


def stop_simulation(env: simpy.Environment):
    """
    停止仿真
    1. 清空事件队列，诱发底层异常
    """

    def clear_queue():
        size = len(env._queue)
        logging.debug("will remove %s events in queue", size)
        env._queue.clear()
        yield env.timeout(0)
        return size

    env.process(clear_queue())


class ISimLock(ABC):

    def __init__(self, env: simpy.Environment):
        self._occupied_ = simpy.Resource(env, capacity=1)
        self._lock_ = False

    @property
    def is_occupied(self):
        """
        判断锁是否被占用
        """
        return self._occupied_.count > 0

    def lock(self):
        """
        请求锁
        """
        return self._occupied_.request()

    def unlock(self, req: simpy.resources.resource.Request):
        """
        请求解锁
        """
        return self._occupied_.release(req)
