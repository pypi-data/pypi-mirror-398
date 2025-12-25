import os
from typing import Optional
from ...api import AssistantDataList, AssistantData

from .utils.content_extractor import ContentExtractor
from .utils.assistant_data_utils import create_embeddings
from ..indexers import Indexer


class SpreadsheetUrlIndexer(Indexer):
    def index_document(
        self, url: str, local_path: str, is_important: bool
    ) -> Optional[AssistantDataList]:
        filename = os.path.basename(local_path)

        data_to_add: list[AssistantData] = []
        data_to_embed: list[str] = []

        content_extractor = ContentExtractor()
        spreadsheet_result = content_extractor.extract_spreadsheet_document(local_path)
        for sheet in spreadsheet_result.get("sheets", []):
            if is_important:
                rows = sheet.get("rows")
                name = sheet.get("name")
                for row in rows:
                    if len(row.strip()) > 0:
                        data_to_add.append(
                            AssistantData(
                                content=row,
                                metadata={
                                    "type": "spreadsheet_sheet_row",
                                    "sheet_name": name,
                                    "url": url,
                                    "filename": filename,
                                },
                            )
                        )
                        data_to_embed.append(filename + " " + row)
            else:
                data_to_add.append(
                    AssistantData(
                        content=sheet.get("excerpt"),
                        metadata={
                            "type": "sheet_excerpt",
                            "url": url,
                            "filename": filename,
                        },
                    )
                )
                data_to_embed.append(filename + " " + sheet.get("excerpt"))

            sheet_summary = content_extractor.summarize_file(
                sheet.get("excerpt"), local_path
            )
            data_to_add.append(
                AssistantData(
                    content=sheet_summary,
                    metadata={
                        "type": "sheet_summary",
                        "url": url,
                        "filename": filename,
                    },
                )
            )
            data_to_embed.append(local_path + " " + sheet_summary)

        embeddings = create_embeddings(data_to_embed)
        for i in range(len(data_to_add)):
            data_to_add[i].embedding = embeddings[i]

        return AssistantDataList(list=data_to_add)
