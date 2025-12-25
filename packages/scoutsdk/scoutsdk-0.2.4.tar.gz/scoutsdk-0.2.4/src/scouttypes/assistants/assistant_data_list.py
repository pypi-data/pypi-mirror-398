from pydantic import BaseModel, ConfigDict

from .assistant_data import AssistantData


class AssistantDataList(BaseModel):
    model_config = ConfigDict(extra="allow")
    list: list[AssistantData]


__all__ = ["AssistantDataList"]
