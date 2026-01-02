import pytest
from a2a.schema.task import Task, TaskStatus
from a2a.protocol.lifecycle import transition_task, InvalidTaskTransition


def test_valid_task_lifecycle():
    task = Task()
    transition_task(task, TaskStatus.WORKING)
    transition_task(task, TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED


def test_invalid_task_transition():
    task = Task()
    with pytest.raises(InvalidTaskTransition):
        transition_task(task, TaskStatus.COMPLETED)
