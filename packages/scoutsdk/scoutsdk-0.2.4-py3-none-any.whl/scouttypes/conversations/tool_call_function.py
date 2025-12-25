from pydantic import BaseModel, ConfigDict


class ToolCallFunction(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    arguments: str


__all__ = ["ToolCallFunction"]
