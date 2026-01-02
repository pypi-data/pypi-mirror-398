from a2a.schema.task import Task, TaskStatus


VALID_TRANSITIONS = {
    TaskStatus.SUBMITTED: {
        TaskStatus.WORKING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.WORKING: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


class InvalidTaskTransition(Exception):
    pass


def transition_task(task: Task, new_status: TaskStatus) -> Task:
    """
    Enforce valid A2A task lifecycle transitions.
    """
    allowed = VALID_TRANSITIONS.get(task.status, set())

    if new_status not in allowed:
        raise InvalidTaskTransition(
            f"Invalid transition: {task.status} → {new_status}"
        )

    task.update_status(new_status)
    return task
