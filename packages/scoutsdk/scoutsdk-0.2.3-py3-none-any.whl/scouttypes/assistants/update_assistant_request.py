from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

from .link_request import LinkRequest


class UpdateAssistantRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    use_system_prompt: Optional[bool] = None
    prompt_starters: Optional[List[str]] = None
    visibility: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    ui_url: Optional[str] = None
    links: Optional[List[LinkRequest]] = None
    allowed_functions: Optional[List[str]] = None
    variables: Optional[Dict[str, str]] = None
    secrets: Optional[Dict[str, Optional[str]]] = None
    allowed_external_services: Optional[List[str]] = None
    content_retrieving_strategy: Optional[Dict[str, Any]] = None


__all__ = ["UpdateAssistantRequest"]
