from a2a.schema.artifact import Artifact
from a2a.schema.parts import TextPart
from uuid import uuid4


def test_artifact_creation():
    task_id = uuid4()

    artifact = Artifact(
        task_id=task_id,
        parts=[TextPart(text="result")],
        is_final=True,
    )

    assert artifact.task_id == task_id
    assert artifact.is_final is True
