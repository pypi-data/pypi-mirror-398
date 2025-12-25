from typing import Optional
from pydantic import BaseModel, ConfigDict


class MessageReasoning(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    text: Optional[str] = None
    data: Optional[dict] = None


__all__ = ["MessageReasoning"]
