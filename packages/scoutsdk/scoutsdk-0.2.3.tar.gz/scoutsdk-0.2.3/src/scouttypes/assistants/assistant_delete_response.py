from pydantic import BaseModel, ConfigDict


class AssistantDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    message: str


__all__ = ["AssistantDeleteResponse"]
