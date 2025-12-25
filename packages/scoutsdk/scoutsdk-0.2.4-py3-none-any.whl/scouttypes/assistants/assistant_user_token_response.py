from typing import Dict, Any
from pydantic import BaseModel, ConfigDict


class AssistantUserTokenResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    access_token: str
    expiry: int
    user: Dict[str, Any]  # UserResponse structure can be defined if needed
    assistant_id: str


__all__ = ["AssistantUserTokenResponse"]
