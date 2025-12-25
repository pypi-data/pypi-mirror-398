from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict

from .model_visibility import ModelVisibility
from .content_retrieving_strategy import ContentRetrievingStrategy


class AssistantInfoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str
    description: str
    instructions: str
    visibility: ModelVisibility
    use_system_prompt: bool
    prompt_starters: List[str]
    avatar_url: Optional[str] = None
    allowed_functions: Optional[List[str]] = None
    is_owner: bool
    allowed_external_services: Optional[List[str]] = None
    content_retrieving_strategy: ContentRetrievingStrategy
    variables: Dict[str, str]
    secrets: List[str]
    ui_url: Optional[str] = None
    model: Optional[str] = None


__all__ = ["AssistantInfoResponse"]
