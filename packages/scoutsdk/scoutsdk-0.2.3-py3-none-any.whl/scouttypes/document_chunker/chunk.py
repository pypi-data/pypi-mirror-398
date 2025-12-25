from typing import Optional
from pydantic import BaseModel, ConfigDict

from .chunk_metadata import ChunkMetadata


class Chunk(BaseModel):
    model_config = ConfigDict(extra="allow")
    chunk_to_embed: str
    content_to_return: str
    metadata: Optional[ChunkMetadata] = None


__all__ = ["Chunk"]
