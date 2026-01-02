from _typeshed import Incomplete
from typing import Literal, TypedDict

Role: Incomplete

class ResponsesPart(TypedDict):
    type: Literal['input_text']
    text: str

class ResponsesMessage(TypedDict):
    role: Role
    content: list[ResponsesPart]

class ChatCompletionContentPart(TypedDict):
    type: Literal['text']
    text: str

class ChatCompletionMessage(TypedDict, total=False):
    role: str
    content: str | list[ChatCompletionContentPart]
    name: str
