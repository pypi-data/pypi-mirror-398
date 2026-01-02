from a2a.schema.message import A2AMessage

def crewai_to_a2a(task) -> A2AMessage:
    return A2AMessage(
        sender=task.sender,
        receiver=task.receiver,
        message_type="TASK_REQUEST",
        intent="delegate_task",
        payload={"task": task.description},
    )
