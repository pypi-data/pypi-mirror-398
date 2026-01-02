from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel


WebhookEvent = Literal[
    "task_update",
    "artifact",
    "error",
    "completion",
]


class WebhookConfig(BaseModel):
    """
    Declares push notification support for an agent.
    """

    url: str
    events: List[WebhookEvent]
