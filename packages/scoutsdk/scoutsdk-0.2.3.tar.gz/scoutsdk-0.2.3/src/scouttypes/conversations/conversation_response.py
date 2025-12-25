from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .conversation_message import ConversationMessage
from ..assistants import AssistantPublicResponse


class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    title: Optional[str]
    payload: List[ConversationMessage]
    updated_at: str
    assistant: Optional[AssistantPublicResponse] = None
    model: Optional[str] = None
    user_data: Optional[dict] = None


__all__ = ["ConversationResponse"]
