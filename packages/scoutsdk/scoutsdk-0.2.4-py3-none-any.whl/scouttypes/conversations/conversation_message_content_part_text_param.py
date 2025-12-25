from typing import Literal
from pydantic import BaseModel, ConfigDict


class ConversationMessageContentPartTextParam(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str
    type: Literal["text"] = "text"


__all__ = ["ConversationMessageContentPartTextParam"]
