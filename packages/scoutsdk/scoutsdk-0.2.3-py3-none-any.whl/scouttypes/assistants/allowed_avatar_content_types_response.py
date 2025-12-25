from typing import List
from pydantic import BaseModel, ConfigDict


class AllowedAvatarContentTypesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    allowed_content_types: List[str]


__all__ = ["AllowedAvatarContentTypesResponse"]
