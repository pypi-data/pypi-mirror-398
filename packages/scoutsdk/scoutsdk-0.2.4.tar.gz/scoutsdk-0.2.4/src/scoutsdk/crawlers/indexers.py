from datetime import datetime, timezone
import fnmatch
from typing import Callable, Optional, Type

from pydantic import BaseModel

from ..api import ScoutAPI, AssistantDataList


from .indexers_impl.utils.assistant_data_utils import (
    add_data_to_assistant,
    delete_url_assistant_data_entries,
    update_url_indexed_date,
)


class Indexer:
    def __init__(self) -> None:
        self.api = ScoutAPI()

    def index_document(
        self, url: str, local_path: str, is_important: bool
    ) -> Optional[AssistantDataList]:
        pass


class RegisteredIndexer(BaseModel):
    class_type: Type[Indexer]
    masks: list[str]


class IndexerClassDecorator:
    _registered_indexers: list[RegisteredIndexer]

    def __init__(self) -> None:
        from .indexers_impl.spreadsheet_url_indexer import SpreadsheetUrlIndexer
        from .indexers_impl.summary_url_indexer import SummaryUrlIndexer
        from .indexers_impl.text_file_indexer import TextFileIndexer

        self._registered_indexers = [
            RegisteredIndexer(
                class_type=TextFileIndexer,
                masks=["*.docx", "*.txt", "*.pdf"],
            ),
            RegisteredIndexer(class_type=SummaryUrlIndexer, masks=["*.ppt", "*.pptx"]),
            RegisteredIndexer(
                class_type=SpreadsheetUrlIndexer,
                masks=["*.csv", "*.xlsx", "*.xls", "*.xlsm"],
            ),
        ]

    def register(self, masks: list[str]) -> Callable[[Type[Indexer]], Type[Indexer]]:
        def decorator(class_type: Type[Indexer]) -> Type[Indexer]:
            self._registered_indexers.insert(
                0, RegisteredIndexer(class_type=class_type, masks=masks)
            )
            return class_type

        return decorator

    def indexer_exists_for_file(self, url: str) -> bool:
        return self.indexer_for_file(url) is not None

    def indexer_for_file(self, local_path: str) -> Optional[Indexer]:
        for registered_indexer in self._registered_indexers:
            for pattern in registered_indexer.masks:
                if fnmatch.fnmatch(local_path, pattern):
                    return registered_indexer.class_type()
        return None

    def indexers(self) -> list[RegisteredIndexer]:
        return self._registered_indexers

    def index_document(self, url: str, local_path: str, is_important: bool) -> None:
        indexer = self.indexer_for_file(local_path)
        if indexer is None:
            print("No indexer found for", url)
        else:
            print(
                "Indexing",
                is_important,
                url,
                f"({local_path})",
                "(Summary)" if not is_important else "",
            )
            assistant_data_list = indexer.index_document(url, local_path, is_important)
            delete_url_assistant_data_entries(url)
            if assistant_data_list is not None:
                add_data_to_assistant(assistant_data_list)
                update_url_indexed_date(url, datetime.now(timezone.utc).isoformat())


indexers = IndexerClassDecorator()
