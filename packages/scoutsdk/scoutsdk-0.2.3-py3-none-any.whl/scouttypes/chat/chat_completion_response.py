from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from ..conversations import ConversationMessage, StreamError


class ChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: List[ConversationMessage]
    error: Optional[StreamError] = None


__all__ = ["ChatCompletionResponse"]
