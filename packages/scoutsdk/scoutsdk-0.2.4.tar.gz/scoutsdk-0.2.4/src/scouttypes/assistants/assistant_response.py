from pydantic import BaseModel, ConfigDict


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    message: str
    assistant_id: str


__all__ = ["AssistantResponse"]
