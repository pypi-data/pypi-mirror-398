from pydantic import BaseModel


class AssistantDataUpdateResponse(BaseModel):
    message: str
    assistant_id: str


__all__ = ["AssistantDataUpdateResponse"]
