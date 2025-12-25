from typing import Optional
from pydantic import BaseModel, ConfigDict


class AssistantData(BaseModel):
    model_config = ConfigDict(extra="allow")
    metadata: dict
    content: str
    embedding: Optional[list] = None


__all__ = ["AssistantData"]
