from typing import List
from fastapi import Response


def add_activation_header(
    response: Response,
    activated: List[str]
):
    """
    Add A2A-Extensions header on the agent response.
    """
    if activated:
        response.headers["A2A-Extensions"] = ",".join(activated)
