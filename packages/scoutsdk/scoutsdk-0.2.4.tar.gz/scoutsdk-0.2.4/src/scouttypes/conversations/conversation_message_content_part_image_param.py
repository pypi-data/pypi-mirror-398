from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict

ImageContentTypes = Literal["image/png", "image/jpeg", "image/gif", "image/webp"]


class ConversationMessageContentPartImageParam(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: str  # base64 encoded image data
    content_type: ImageContentTypes
    filename: Optional[str] = None
    type: Literal["image"] = "image"


__all__ = ["ConversationMessageContentPartImageParam", "ImageContentTypes"]
