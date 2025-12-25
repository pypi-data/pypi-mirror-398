from typing import Literal
from pydantic import BaseModel, ConfigDict


class ConversationMessageContentPartInputAudioParam(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: str
    format: str
    type: Literal["audio"] = "audio"


__all__ = ["ConversationMessageContentPartInputAudioParam"]
