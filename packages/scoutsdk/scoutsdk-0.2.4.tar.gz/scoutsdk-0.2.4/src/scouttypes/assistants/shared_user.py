from typing import Optional
from pydantic import BaseModel, ConfigDict


class SharedUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    first_name: str
    last_name: str
    email: str
    picture_url: Optional[str] = None


__all__ = ["SharedUser"]
