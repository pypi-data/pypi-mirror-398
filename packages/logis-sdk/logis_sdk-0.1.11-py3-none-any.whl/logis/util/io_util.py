import asyncio
import atexit
import inspect
import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Coroutine,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    Union,
)

from pydantic import BaseModel, ConfigDict

from logis.data_type import T
from logis.iface import QueueType
from logis.util.lambda_util import invoke


def get_or_new_event_loop(auto_set: bool = True) -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        if auto_set:
            asyncio.set_event_loop(loop)
    return loop


class WriteBufferConfig(BaseModel):
    # 每批最大事件数
    batch_size: int = 256

    # 缓存的最大条目数，默认无限制
    queue_size: int = 0

    # 缓存的最大时间间隔
    flush_interval: float = 10

    queue_type: Optional[QueueType] = None

    _queue: Optional[QueueType] = None

    handler: Union[Callable[[List[T]], None], None, Coroutine[Any, Any, None]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_queue(self, mode: Literal["sync", "async"]) -> QueueType:
        if self._queue is None:
            if self.queue_type is None:
                self.queue_type = queue.Queue if mode == "sync" else asyncio.Queue
            self._queue = self.queue_type(maxsize=self.queue_size)
        return self._queue


class WriteBuffer(ABC, Generic[T]):
    """
    写操作缓冲器
    """

    def __init__(self, config: WriteBufferConfig, **kwargs):
        self._config = config
        self._handler = self._config.handler

        self._is_running = False
        self._last_flush_time = time.time()
        self._lock: Union[threading.Lock, asyncio.Lock, None] = None
        self._flush_task: Optional[threading.Thread] = None

    def need_flush(self) -> bool:
        """判断是否需要刷新（根据时间间隔和条目数）"""
        current_time = time.time()
        meet_time_interval = (
            current_time - self._last_flush_time >= self._config.flush_interval
        )
        if meet_time_interval:
            logging.debug(f"meet time interval {self._config.flush_interval}")
        meet_batch_size = self._queue.qsize() >= self._config.batch_size
        if meet_batch_size:
            logging.debug(f"meet batch size {self._config.batch_size}")
        return meet_time_interval or meet_batch_size

    def put(self, item: Any) -> None:
        """添加单条数据到缓冲器"""
        with self._lock:
            # 若队列满了，先触发一次刷新（避免阻塞）
            if self._queue.full():
                self.flush()
            self._queue.put(item)

        # 检查是否达到批量阈值，达到则触发刷新
        if self.need_flush():
            self.flush()

    def start(self) -> None:
        """启动缓冲器（开启定时刷新线程）"""
        self._is_running = True
        self._last_flush_time = time.time()

    @abstractmethod
    def stop(self) -> None:
        """停止缓冲器（强制刷新剩余数据并关闭线程）"""
        self._is_running = False

    @abstractmethod
    def flush(self, flush_all: bool = False, **kwargs):
        pass

    def _flush_loop(self, **kwargs) -> None:
        """定时刷新循环（后台线程）"""
        pass


class SyncWriteBuffer(WriteBuffer[T]):
    """
    同步写操作缓冲器
    """

    def __init__(self, config: WriteBufferConfig, **kwargs):
        super().__init__(config, **kwargs)
        self._queue = self._config.get_queue(mode="sync")
        self._lock = threading.Lock()

        atexit.register(self.stop)

    def start(self):
        if self._is_running:
            return
        super().start()
        t = threading.Thread(target=self._flush_loop, daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        """停止缓冲器（强制刷新剩余数据并关闭线程）"""
        super().stop()
        if self._flush_task:
            self._flush_task.join()
        self.flush(flush_all=True)  # 退出前强制刷新剩余数据

    def flush(self, flush_all: bool = False, **kwargs) -> None:
        """强制刷新缓冲数据（批量处理）"""
        if self._queue.empty():
            return

        # TODO：是否可以不用加锁
        items: List[Any] = []
        with self._lock:
            while not self._queue.empty() and (
                flush_all or len(items) < self._config.batch_size
            ):
                try:
                    items.append(self._queue.get_nowait())
                except queue.Empty:
                    break

        # 调用用户自定义的批量处理函数
        if items:
            self._handler(items)
            # 更新刷新时间
            self._last_flush_time = time.time()

    def _flush_loop(self, check_interval=0.1, **kwargs):
        while self._is_running:
            if self.need_flush():
                self.flush()
            time.sleep(check_interval)


class AsyncWriteBuffer(WriteBuffer[T]):
    """
    异步写操作缓冲器
    """

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self._loop = get_or_new_event_loop()
        self._queue = self._config.get_queue(mode="async")
        self._lock = asyncio.Lock()
        atexit.register(self.__wait_stop)

    def __wait_stop(self):
        if self._loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            loop = self._loop

        loop.run_until_complete(self.stop())

    async def start(self):
        if self._is_running:
            return
        super().start()
        self._flush_task = self._loop.create_task(self._flush_loop())
        return self._flush_task

    async def stop(self):
        super().stop()
        if self._flush_task:
            await self._flush_task
        await self.flush(flush_all=True)

    async def put(self, item: Any):
        async with self._lock:
            if self._queue.full():
                await self.flush()
            await self._queue.put(item)

        if self.need_flush():
            await self.flush()

    async def flush(self, flush_all=False, **kwargs):
        if self._queue.empty():
            return

        items: List[Any] = []
        # TODO：是否可以不用加锁
        async with self._lock:
            while not self._queue.empty() and (
                flush_all or len(items) < self._config.batch_size
            ):
                items.append(await self._queue.get())

        if items:
            if inspect.iscoroutinefunction(self._handler):
                await self._handler(items)  # 调用异步批量处理函数
            else:
                self._handler(items)
            self._last_flush_time = time.time()

    async def _flush_loop(self, check_interval=0.1, **kwargs):
        while self._is_running:
            if self.need_flush():
                await self.flush()
            await asyncio.sleep(check_interval)
            # TODO: 这里会出现乱序问题
            # try:
            #     item = await asyncio.wait_for(self._queue.get(), timeout=check_interval)
            #     self._queue.put_nowait(item)
            # except asyncio.TimeoutError:
            #     pass
