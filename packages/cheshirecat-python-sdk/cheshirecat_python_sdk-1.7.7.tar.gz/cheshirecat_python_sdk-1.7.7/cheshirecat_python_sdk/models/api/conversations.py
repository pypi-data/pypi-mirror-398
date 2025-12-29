from typing import List
from pydantic import BaseModel

from cheshirecat_python_sdk.models.api.nested.memories import ConversationMessage


class ConversationDeleteOutput(BaseModel):
    deleted: bool


class ConversationHistoryOutput(BaseModel):
    history: List[ConversationMessage]


class ConversationsResponse(BaseModel):
    chat_id: str
    name: str
    num_messages: int
    created_at: float | None
    updated_at: float | None


class ConversationNameChangeOutput(BaseModel):
    changed: bool