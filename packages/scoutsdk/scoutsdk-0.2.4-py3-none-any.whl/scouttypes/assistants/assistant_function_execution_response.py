from typing import Any
from pydantic import BaseModel, ConfigDict


class AssistantFunctionExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    result: Any


__all__ = ["AssistantFunctionExecutionResponse"]
