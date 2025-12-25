from typing import Optional
from pydantic import BaseModel, ConfigDict
from .stream_tool_call_status import StreamToolCallStatus


class StreamToolCall(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: StreamToolCallStatus
    tool_name: str
    arguments: str
    call_id: str
    function_permission_data: Optional[dict]


__all__ = ["StreamToolCall"]
