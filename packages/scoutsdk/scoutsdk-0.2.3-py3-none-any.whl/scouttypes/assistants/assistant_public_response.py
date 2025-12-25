from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AssistantPublicResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    description: str
    instructions: str
    visibility: str
    is_owner: bool
    is_collaborator: bool
    prompt_starters: List[str]
    owner_name: str
    avatar_url: Optional[str] = None
    ui_url: Optional[str] = None
    model: Optional[str] = None


__all__ = ["AssistantPublicResponse"]
