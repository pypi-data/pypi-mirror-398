from pydantic import BaseModel
from .assistant_custom_function import AssistantCustomFunction


class AssistantCustomFunctionsResponse(BaseModel):
    functions: list[AssistantCustomFunction]


__all__ = ["AssistantCustomFunctionsResponse"]
