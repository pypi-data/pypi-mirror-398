from abc import ABC, abstractmethod
import os
from typing import Optional

from .document_chunks import DocumentChunks


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


__all__ = ["AbstractDocumentChunker"]
