from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Iterable, Optional, Union

from pydantic import BaseModel, Field

TaskId = Union[str, int]
TaskPriority = Union[str, int]


class TaskStatus(Enum):
    """
    任务状态
    """

    NOT_STARTED = "not_started"
    STARTED = "started"
    PAUSED = "paused"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ITask(metaclass=ABCMeta):
    """
    任务基础抽象类
    """

    @abstractmethod
    def get_task_id(self) -> TaskId:
        pass

    @abstractmethod
    def get_priority(self) -> TaskPriority:
        """
        任务优先级
        """
        pass

    @abstractmethod
    def update_status(self, status: TaskStatus):
        """
        更新任务状态
        """
        pass

    @abstractmethod
    def is_status_at(self, status: TaskStatus) -> bool:
        """
        检查任务状态是否为指定值
        """
        pass

    @property
    def finished(self) -> bool:
        return self.is_status_at(TaskStatus.FINISHED)


TaskLike = Union[ITask, TaskId]


class Task(BaseModel, ITask):
    """
    任务基础结构
    """

    id: Optional[TaskId] = None
    parent_id: Optional[TaskId] = None
    children_ids: Iterable[TaskId] = Field(default_factory=list)

    name: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[TaskPriority] = None

    repeat: int = 1
    progress: Union[float, int] = 0
    tags: Iterable[str] = Field(default_factory=set)

    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    started_at: Optional[int] = None
    finished_at: Optional[int] = None
    cancelled_at: Optional[int] = None

    status: Optional[TaskStatus] = None
    stage: Optional[str] = None

    remark: Optional[str] = None

    def get_task_id(self) -> TaskId:
        return self.id

    def get_priority(self) -> TaskPriority:
        return self.priority

    def update_status(self, status: TaskStatus):
        self.status = status

    def is_status_at(self, status: TaskStatus) -> bool:
        return self.status == status
