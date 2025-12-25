from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class AssistantFile(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = ""
    filename: str = ""
    description: str = ""
    status: str = ""
    content_type: str = ""
    type: str = ""
    functions_schema: Optional[Dict[str, Any]] = None


__all__ = ["AssistantFile"]
