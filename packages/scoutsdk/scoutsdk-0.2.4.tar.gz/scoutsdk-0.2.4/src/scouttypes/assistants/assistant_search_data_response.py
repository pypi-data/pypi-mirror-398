from typing import Optional
from pydantic import BaseModel, ConfigDict

from ..document_chunker import ChunkMetadata


class AssistantSearchDataResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    distance: float
    content: str
    file_name: Optional[str] = None
    link_url: Optional[str] = None
    metadata: Optional[ChunkMetadata] = None


__all__ = ["AssistantSearchDataResponse"]
