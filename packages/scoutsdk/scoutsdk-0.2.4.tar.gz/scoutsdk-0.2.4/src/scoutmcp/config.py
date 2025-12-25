from pydantic import BaseModel
from typing import Optional


class MCPConfig(BaseModel):
    server_name: str  # Name for the MCP server
    scout_mcp_assistant_id: str  # Assistant UUID to use
    scout_api_token: str  # API authentication token
    scout_api_url: Optional[str] = None  # Scout API base URL
