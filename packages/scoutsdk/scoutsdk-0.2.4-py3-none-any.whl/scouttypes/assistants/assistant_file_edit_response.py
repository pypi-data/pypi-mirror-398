from pydantic import BaseModel, ConfigDict


class AssistantFileEditResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    message: str


__all__ = ["AssistantFileEditResponse"]
