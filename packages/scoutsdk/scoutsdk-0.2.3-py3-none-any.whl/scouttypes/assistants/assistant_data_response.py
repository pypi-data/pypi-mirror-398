from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AssistantDataResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


__all__ = ["AssistantDataResponse"]
