from typing import Optional
from scoutsdk.api import AssistantDataList, AssistantData
from scoutsdk import Chunk
import os

from ..indexers import Indexer
from .utils.content_extractor import ContentExtractor
from .utils.assistant_data_utils import create_embeddings


class TextFileIndexer(Indexer):
    def index_document(
        self, url: str, local_path: str, is_important: bool
    ) -> Optional[AssistantDataList]:
        filename = os.path.basename(local_path)

        data_to_add: list[AssistantData] = []
        data_to_embed: list[str] = []
        extracted_document = ContentExtractor().extract_text_document(local_path)
        table_of_content = extracted_document.get("table_of_content")

        # Split table_of_content into chunks of 1500 characters
        toc_chunks = (
            [
                table_of_content[i : i + 1500]
                for i in range(0, len(table_of_content), 1500)
            ]
            if table_of_content
            else []
        )
        for idx, toc_chunk in enumerate(toc_chunks):
            data_to_add.append(
                AssistantData(
                    content=toc_chunk,
                    metadata={
                        "type": "table_of_content",
                        "url": url,
                        "filename": filename,
                    },
                )
            )
            data_to_embed.append(f"{filename} {toc_chunk}")

        if is_important:
            print(f"Embedding content from {url}...")
            chunks: list[Chunk] = [
                Chunk(**a) for a in extracted_document.get("chunks", [])
            ]
            for chunk in chunks:
                metadata = chunk.metadata.model_dump() if chunk.metadata else {}
                metadata.pop("line_end", None)
                metadata.pop("line_start", None)
                metadata.pop("page_start", None)
                metadata.pop("page_end", None)
                metadata.pop("parent", None)
                metadata["url"] = url
                metadata["filename"] = filename
                data_to_add.append(
                    AssistantData(content=chunk.content_to_return, metadata=metadata)
                )
                data_to_embed.append(chunk.chunk_to_embed)

        embeddings = create_embeddings(data_to_embed)
        for i in range(len(data_to_add)):
            data_to_add[i].embedding = embeddings[i]

        return AssistantDataList(list=data_to_add)
