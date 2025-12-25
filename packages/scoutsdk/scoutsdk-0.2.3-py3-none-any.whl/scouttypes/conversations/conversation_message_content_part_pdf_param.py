from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class ConversationMessageContentPartPDFParam(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: str  # base64 encoded pdf data
    filename: Optional[str] = None
    type: Literal["pdf"] = "pdf"


__all__ = ["ConversationMessageContentPartPDFParam"]
