from typing import List
from pydantic import BaseModel


class CreateAssistantDataResponse(BaseModel):
    message: str
    assistant_id: str
    created_item_ids: List[str]


__all__ = ["CreateAssistantDataResponse"]
