from abc import ABC, abstractmethod
import os
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class ChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    hierarchy: Optional[list[str] | str] = None
    parent: Optional["ChunkMetadata"] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    def model_dump_clean(self, **kwargs: Any) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, exclude_defaults=True, **kwargs)


class Chunk(BaseModel):
    chunk_to_embed: str
    content_to_return: str
    metadata: Optional[ChunkMetadata] = None


class DocumentChunks(BaseModel):
    chunks: Optional[list[Chunk]] = None
    sub_document_urls: list[str] = []


class AbstractDocumentChunker(ABC):
    @property
    def priority(self) -> int:
        return 100

    def is_file_url(self, url: str) -> bool:
        return url.startswith("file://")

    def file_extension(self, url: str) -> Optional[str]:
        filename, file_extension = os.path.splitext(url.lower())
        return file_extension

    def url_to_file_path(self, url: str) -> str:
        return url.removeprefix("file://")

    @abstractmethod
    def supports_document(self, url: str) -> bool:
        pass

    @abstractmethod
    def process_document(self, url: str) -> DocumentChunks:
        pass
