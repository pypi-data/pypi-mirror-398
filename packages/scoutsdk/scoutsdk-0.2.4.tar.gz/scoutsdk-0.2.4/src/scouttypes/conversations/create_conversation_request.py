from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .conversation_message import ConversationMessage


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    payload: List[ConversationMessage]
    time_zone_offset: Optional[str] = None
    assistant_id: Optional[str] = None
    title: Optional[str] = None
    model: Optional[str] = None
    user_data: Optional[dict] = None


__all__ = ["CreateConversationRequest"]
