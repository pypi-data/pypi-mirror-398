from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Iterable, Iterator, Optional

from networkx import DiGraph, has_path

from .model import ITask, TaskId, TaskLike, TaskStatus


class AbstractTaskManager(metaclass=ABCMeta):
    """
    任务管理器基础抽象类
    """

    @abstractmethod
    def is_task_finished(self, task: TaskLike, update: bool = True, infer=True) -> bool:
        """
        检查任务是否已完成
        Args:
            task (TaskLike): 任务对象
            update (bool, optional): 是否在检测到任务已完成时自动更新任务属性
            infer (bool, optional): 是否根据子任务的状态推测本任务的状态
        Returns:
            bool: 任务是否已完成
        """
        pass

    @abstractmethod
    def task_size(self) -> int:
        """
        获取任务数量
        """
        pass

    @abstractmethod
    def tasks(self, only_id: bool = False) -> Iterator[ITask]:
        """
        获取所有任务
        """
        pass

    @abstractmethod
    def add_task(self, task: TaskLike, parent: Optional[TaskLike] = None, **attr):
        """
        添加任务

        Args:
            task (TaskLike): 任务对象
            parent (TaskLike | None): 父任务对象. Defaults to None.
        """
        pass

    @abstractmethod
    def add_task_if_absent(
        self, task: TaskLike, parent: Optional[TaskLike] = None, **attr
    ) -> bool:
        """
        如果任务不存在则添加,否则不添加

        Args:
            task (TaskLike): 任务对象
            parent (TaskLike | None): 父任务对象. Defaults to None.

        Returns:
            bool: 是否添加成功
        """
        pass

    @abstractmethod
    def remove_task(self, task: TaskLike, cascade: bool = False):
        """
        删除任务

        Args:
            task (TaskLike): 任务对象
            cascade (bool, optional): 是否级联删除子任务. Defaults to False.
        """
        pass

    @abstractmethod
    def remove_task_if_present(self, task: TaskLike, cascade: bool = False):
        """
        如果任务存在则删除

        Args:
            task (TaskLike): 任务对象
            cascade (bool, optional): 是否级联删除子任务. Defaults to False.
        """
        pass

    @abstractmethod
    def get_task(self, task: TaskLike) -> Optional[ITask]:
        """
        根据任务ID获取任务本身
        """
        pass

    @abstractmethod
    def get_children_id(self, task: TaskLike, strict: bool = True) -> Iterable[TaskId]:
        """
        获取任务的所有子任务ID

        Args:
            task (TaskLike): 任务对象
            strict (bool, optional): 是否严格模式. Defaults to True.

        Returns:
            Iterable[TaskId]: 子任务ID列表
        """
        pass

    @abstractmethod
    def get_parents_id(self, task: TaskLike, strict: bool = True) -> Iterable[TaskId]:
        """
        获取任务的所有父任务ID

        Args:
            task (TaskLike): 任务对象
            strict (bool, optional): 是否严格模式. Defaults to True.

        Returns:
            Iterable[TaskId]: 父任务ID列表
        """
        pass

    @abstractmethod
    def has_parent_child_relationship(
        self, a: TaskLike, b: TaskLike, strict: bool = True
    ) -> bool:
        """
        判断任务a是否是任务b的父任务

        Args:
            a (TaskLike): 任务A
            b (TaskLike): 任务B
            strict (bool): 是否严格判断. 如果严格判断, 则判断是否存在一条有向边从a指向b. 否则判断是否存在一条从a到b的路径.

        Returns:
            bool: 是否是子任务
        """
        pass

    @abstractmethod
    def update_task_status(self, task: TaskId, status: TaskStatus):
        """
        更新任务状态
        Args:
            task (TaskId): 任务ID
            status (TaskStatus): 任务状态
        """
        pass


class TaskGraph(AbstractTaskManager):
    """
    以任务id作为节点id组成的任务树,内部数据结构是一个有向无环图
    """

    __KEY_TASK__ = "task"

    def __init__(self, **attr):
        self.__graph__ = DiGraph()
        self.__id_task_map__ = defaultdict()

    def parse_task_id(self, task: TaskLike) -> TaskId:
        if isinstance(task, (str, int)):
            return task
        if isinstance(task, ITask):
            return task.get_task_id()
        raise ValueError(f"Unknown task type {type(task)}")
    def task_size(self) -> int:
        """
        获取任务数量
        """
        return self.__graph__.number_of_nodes()

    def tasks(self, only_id: bool = False) -> Iterator[ITask]:
        for node_id in self.__graph__.nodes:
            yield node_id if only_id else self.get_task(node_id)

    def get_task(self, task_id: TaskId) -> Optional[ITask]:
        task = self.__id_task_map__.get(task_id)
        if task:
            return task
        node = self.__graph__.nodes.get(task_id)
        return node.get(self.__KEY_TASK__) if node else None

    def find_by(self):
        raise NotImplementedError("TaskGraph.find_by not implemented")

    def add_task(self, task: TaskLike, parent: Optional[TaskLike] = None, **attr):
        task_id = self.parse_task_id(task)
        self.__id_task_map__[task_id] = task
        self.__graph__.add_node(task_id, **attr)
        if parent:
            parent_id = self.parse_task_id(parent)
            self.add_task_if_absent(parent)
            assert (
                parent_id != task_id
            ), f"parent task {parent_id} and task itself {task_id} should be different"
            self.__graph__.add_edge(parent_id, task_id)

    def add_task_if_absent(
        self, task: TaskLike, parent: Optional[TaskLike] = None, **attr
    ) -> bool:
        task_id = self.parse_task_id(task)
        has = self.__graph__.has_node(task_id)
        if not has:
            self.add_task(task, parent=parent, **attr)
        return has

    def remove_task(self, task: TaskLike, cascade: bool = False, **kwargs):
        task_id = self.parse_task_id(task)
        if cascade:
            for child_id in list(self.get_children_id(task, strict=True)):
                self.remove_task(child_id, cascade=cascade, **kwargs)
        self.__graph__.remove_node(task_id)

    def remove_task_if_present(
        self, task: TaskLike, cascade: bool = False, **kwargs
    ) -> bool:
        task_id = self.parse_task_id(task)
        has = self.__graph__.has_node(task_id)
        if has:
            self.remove_task(task, cascade=cascade, **kwargs)
        return has

    def get_children_id(self, task: TaskLike, strict: bool = True) -> Iterator[TaskId]:
        if strict:
            return self.__graph__.successors(self.parse_task_id(task))
        raise NotImplementedError()

    def get_parents_id(self, task: TaskLike, strict: bool = True) -> Iterable[TaskId]:
        if strict:
            return self.__graph__.predecessors(self.parse_task_id(task))
        raise NotImplementedError()

    def has_parent_child_relationship(
        self, a: TaskLike, b: TaskLike, strict: bool = True
    ) -> bool:
        a_id = self.parse_task_id(a)
        b_id = self.parse_task_id(b)
        return (
            self.__graph__.has_edge(a_id, b_id)
            if strict
            else has_path(self.__graph__, a_id, b_id)
        )

    def __contains__(self, task: TaskLike) -> bool:
        """
        检查任务是否存在
        """
        return self.__graph__.has_node(self.parse_task_id(task))

    def update_task_status(self, task: TaskId, status: TaskStatus):
        """
        将任务状态设置为指定值
        """
        task_id = self.parse_task_id(task)
        task: ITask = self.get_task(task_id)
        assert task, f"任务 {task_id} 不存在"
        task.update_status(status)

    def is_task_finished(self, task: TaskLike, update: bool = True, infer=True):
        task_id = self.parse_task_id(task)
        task: ITask = self.get_task(task_id)

        finished = task.finished
        if finished is True:
            return finished
        if not infer:
            return finished

        children_ids = list(self.get_children_id(task_id, strict=True))
        all_children_finished = (
            False
            if not children_ids
            else all(self.is_task_finished(child_id) for child_id in children_ids)
        )
        if all_children_finished and update:
            self.update_task_status(task_id, TaskStatus.FINISHED)
        return all_children_finished
