from pydantic import BaseModel, ConfigDict
from typing import Any


class AssistantCustomFunction(BaseModel):
    model_config = ConfigDict(extra="allow")
    function_name: str
    description: str
    parameters: dict[str, Any]


__all__ = ["AssistantCustomFunction"]
