from typing import Optional
from pydantic import BaseModel, ConfigDict


class MetadataToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")
    tool_name: str
    arguments: str
    output_metadata: Optional[dict] = None


__all__ = ["MetadataToolCall"]
