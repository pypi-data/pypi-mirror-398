from typing import Optional, Any
from pydantic import BaseModel


class SkillResponse(BaseModel):
    """Response model for a skill."""

    id: str
    name: str
    description: Optional[str] = None
    type: str  # "FUNCTIONS" or "MCP"
    scope: str  # "ASSISTANT" or "GLOBAL"
    functions_file_remote_path: Optional[str] = None
    functions_status: Optional[str] = None  # "IN_QUEUE", "READY", "ERROR"
    functions_schema: Optional[dict[str, Any]] = None
    mcp_server: Optional[dict[str, Any]] = None
    visibility: Optional[dict[str, Any]] = None
    created_at: str
    updated_at: str


class AssistantSkillResponse(BaseModel):
    """Response model for assistant skill operations (add/remove)."""

    message: str
    assistant_id: str
    skill_id: str
