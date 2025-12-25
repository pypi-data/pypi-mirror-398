from datetime import datetime
from typing import Any, Optional
from ....api import ScoutAPI, AssistantData, AssistantDataList
from ....api.project_helpers import scout


INDEXED_DATE_KEY = "indexed_date"


def create_embeddings(strings: list[str], batch_size: int = 25) -> list[list[float]]:
    embeddings = []
    scout_api = ScoutAPI()
    for i in range(0, len(strings), batch_size):
        batch = strings[i : i + batch_size]
        batch_embeddings = scout_api.utils.create_embeddings(batch)
        embeddings.extend(batch_embeddings)

    return embeddings


def get_url_indexed_date_entry(url: str) -> Optional[Any]:
    where = {"url": url, "type": INDEXED_DATE_KEY}

    datas = ScoutAPI().assistants.query_data(
        assistant_id=scout.context["SCOUT_ASSISTANT_ID"], where=where
    )
    return None if len(datas) == 0 else datas[0]


def need_to_index(url: str, last_udated_at: str) -> bool:
    entry = get_url_indexed_date_entry(url)
    indexed_date = entry.metadata.get(INDEXED_DATE_KEY) if entry else None
    return indexed_date is None or datetime.fromisoformat(
        indexed_date
    ) < datetime.fromisoformat(last_udated_at)


def delete_url_assistant_data_entries(url: str) -> None:
    ScoutAPI().assistants.delete_data(
        assistant_id=scout.context["SCOUT_ASSISTANT_ID"], where={"url": url}
    )


def update_url_indexed_date(url: str, last_udated_at: str) -> None:
    entry = get_url_indexed_date_entry(url)

    metadata = {"url": url, INDEXED_DATE_KEY: last_udated_at, "type": INDEXED_DATE_KEY}
    print("Updating", url, entry)
    if entry is None:
        ScoutAPI().assistants.create_data(
            assistant_id=scout.context["SCOUT_ASSISTANT_ID"],
            data=AssistantData(metadata=metadata, content="", embedding=None),
        )
    else:
        ScoutAPI().assistants.update_data(
            assistant_id=scout.context["SCOUT_ASSISTANT_ID"],
            data_id=entry["id"],
            content="",
            metadata=metadata,
        )


def add_data_to_assistant(data: list[AssistantData] | AssistantDataList) -> None:
    assistant_id = scout.context["SCOUT_ASSISTANT_ID"]
    ScoutAPI().assistants.create_data(
        assistant_id=assistant_id,
        data=AssistantDataList(list=data) if isinstance(data, list) else data,
    )
