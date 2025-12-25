from pydantic import BaseModel, ConfigDict
from .tool_call_function import ToolCallFunction


class MessageToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    type: str
    function: ToolCallFunction


__all__ = ["MessageToolCall"]
