from typing import Optional
from pydantic import BaseModel, ConfigDict

from .chunk import Chunk


class DocumentChunks(BaseModel):
    model_config = ConfigDict(extra="allow")
    chunks: Optional[list[Chunk]] = None
    sub_document_urls: list[str] = []


__all__ = ["DocumentChunks"]
