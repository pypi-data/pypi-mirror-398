from typing import List
from pydantic import RootModel
from .assistant_data_response_item import AssistantDataResponseItem


class QueryAssistantDataResponse(RootModel[List[AssistantDataResponseItem]]):
    pass


__all__ = ["QueryAssistantDataResponse"]
