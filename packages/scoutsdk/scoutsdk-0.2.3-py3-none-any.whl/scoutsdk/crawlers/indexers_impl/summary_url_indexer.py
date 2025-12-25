import os
from typing import Optional
from scoutsdk.api import AssistantDataList, AssistantData
from scoutsdk import ScoutAPI

from .utils.content_extractor import ContentExtractor
from ..indexers import Indexer
from .utils.assistant_data_utils import create_embeddings


class SummaryUrlIndexer(Indexer):
    def index_document(
        self, url: str, local_path: str, is_important: bool
    ) -> Optional[AssistantDataList]:
        filename = os.path.basename(local_path)
        data_to_add: list[AssistantData] = []
        data_to_embed: list[str] = []

        document_text = ScoutAPI().utils.get_document_text(local_path)
        file = document_text.get("file", None)
        file_content = file.get("content") if file is not None else None
        summary = (
            ContentExtractor().summarize_file(file_content, local_path)
            if file_content is not None
            else ""
        )
        data_to_add.append(
            AssistantData(
                content=summary,
                metadata={
                    "type": "powerpoint_summary",
                    "url": url,
                    "filename": filename,
                },
            )
        )
        data_to_embed.append(filename + " " + summary)

        embeddings = create_embeddings(data_to_embed)
        for i in range(len(data_to_add)):
            data_to_add[i].embedding = embeddings[i]

        return AssistantDataList(list=data_to_add)
