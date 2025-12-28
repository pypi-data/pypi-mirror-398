from abc import ABC, abstractmethod
from ast import Not
from enum import Enum

from logis.data_type import ABCEnumMeta
from logis.iface.handler import IHandler
from logis.task.model import ITask


class IWorkingMode(ABC):
    """
    工作模式
    """

    pass


class WorkingMode(IWorkingMode, Enum, metaclass=ABCEnumMeta):
    """
    工作模式
    """

    SYNC = "synchronous"
    ASYNC = "asynchronous"


class ITaskHandler(IHandler):
    """
    任务处理接口
    """

    def get_working_mode(self):
        """
        获取处理模式
        """
        raise NotImplementedError("get_working_mode")

    def get_task_manifest(self):
        """
        获取任务清单
        """
        raise NotImplementedError("get_task_manifest")

    def is_task_all_done(self, **kwargs):
        """
        任务是否全部完成
        """
        raise NotImplementedError("is_task_all_done")

    @abstractmethod
    def on_task_received(self, *tasks: ITask, **kwargs):
        """
        接收任务
        """

    @abstractmethod
    def on_task_succeeded(self, *args, **kwargs):
        """
        任务完成
        """

    def on_task_failed(self, *args, **kwargs):
        """
        任务失败
        """
        raise NotImplementedError("on_task_failed")
