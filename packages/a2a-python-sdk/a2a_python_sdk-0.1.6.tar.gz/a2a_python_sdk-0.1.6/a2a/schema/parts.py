from __future__ import annotations
from typing import Literal, Union, Dict, Any
from pydantic import BaseModel


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class JsonPart(BaseModel):
    type: Literal["json"] = "json"
    data: Dict[str, Any]


class FilePart(BaseModel):
    type: Literal["file"] = "file"
    uri: str
    mime_type: str


MessagePart = Union[TextPart, JsonPart, FilePart]
