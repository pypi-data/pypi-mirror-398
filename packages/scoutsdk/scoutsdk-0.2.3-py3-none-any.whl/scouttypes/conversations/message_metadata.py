from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from .metadata_file import MetadataFile
from .metadata_tool_call import MetadataToolCall


class MessageMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    assistant_id: Optional[str] = None
    files: Optional[List[MetadataFile]] = None
    tool_calls: Optional[List[MetadataToolCall]] = None
    function_permissions: Optional[List[Any]] = None


__all__ = ["MessageMetadata"]
