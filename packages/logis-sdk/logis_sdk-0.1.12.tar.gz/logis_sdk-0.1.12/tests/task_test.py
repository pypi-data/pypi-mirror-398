import pytest
from networkx import NetworkXError

from logis.task import Task, TaskGraph, TaskStatus


def test_task_graph():
    graph = TaskGraph()
    task1 = Task(id="task1")
    task2 = Task(id="task2")
    task3 = Task(id="task3")

    graph.add_task(task1)
    graph.add_task_if_absent(task1.model_copy(update=dict(name="task1 copy")))
    assert graph.get_task(task1.id).name is None

    # 测试父子关系
    graph.add_task(task2, parent=task1)
    graph.add_task(task3, parent=task2)
    assert list(graph.get_parents_id(task2.id)) == [task1.id]
    assert list(graph.get_children_id(task1.id)) == [task2.id]
    assert graph.has_parent_child_relationship(task1, task2)
    assert graph.has_parent_child_relationship(task1, task3, strict=True) is False
    assert graph.has_parent_child_relationship(task1, task3, strict=False) is True

    # 测试任务完成状态
    assert graph.is_task_finished(task1) is False
    graph.update_task_status(task3, TaskStatus.FINISHED)
    assert graph.is_task_finished(task1) is True

    # 测试删除
    with pytest.raises(NetworkXError):
        graph.remove_task("not exist")
    graph.remove_task_if_present(task2)
    assert task2 not in graph

    assert list(graph.get_children_id(task1)) == []
    assert task1.get_task_id() in graph

    task4 = Task(id="task4")
    task5 = Task(id="task5")
    graph.add_task(task4, parent=task3)
    graph.add_task(task5, parent=task4)
    graph.remove_task(task3, cascade=True)

    assert graph.task_size() == 1
    assert list(graph.tasks()) == [task1]
    assert list(graph.tasks(only_id=True)) == [task1.id]


def test_task_handler():
    from logis.task import ITaskHandler, IWorkingMode, WorkingMode

    class TestTaskHandler(ITaskHandler):
        def get_working_mode(self) -> IWorkingMode:
            return WorkingMode.SYNC

        def on_task_received(self, *tasks, **kwargs):
            pass

        def handle(self, *args, **kwargs):
            print(args, kwargs)

        def on_task_succeeded(self, *args, **kwargs):
            pass

    handler = TestTaskHandler()

    handler.handle(a=1, b=2, c=3)
