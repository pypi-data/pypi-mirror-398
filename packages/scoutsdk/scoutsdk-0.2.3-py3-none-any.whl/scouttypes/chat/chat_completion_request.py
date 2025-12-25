from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from ..conversations import ConversationMessage


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: List[ConversationMessage]
    assistant_id: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False
    response_interface: Optional[str] = None
    llm_args: Optional[dict] = None
    allowed_tools: Optional[List[str]] = None
    response_format: Optional[dict] = None


__all__ = ["ChatCompletionRequest"]
