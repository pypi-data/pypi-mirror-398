from typing import Optional, Dict, Any
from pydantic import BaseModel


class AssistantDataResponseItem(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


__all__ = ["AssistantDataResponseItem"]
