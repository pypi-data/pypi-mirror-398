from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class LinkRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str
    id: Optional[UUID] = None


__all__ = ["LinkRequest"]
