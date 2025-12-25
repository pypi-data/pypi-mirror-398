from pydantic import BaseModel, ConfigDict


class DeleteConversationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str


__all__ = ["DeleteConversationResponse"]
