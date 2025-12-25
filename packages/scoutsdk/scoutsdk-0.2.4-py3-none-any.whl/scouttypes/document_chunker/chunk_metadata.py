from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    hierarchy: Optional[list[str] | str] = None
    parent: Optional["ChunkMetadata"] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


__all__ = ["ChunkMetadata"]
