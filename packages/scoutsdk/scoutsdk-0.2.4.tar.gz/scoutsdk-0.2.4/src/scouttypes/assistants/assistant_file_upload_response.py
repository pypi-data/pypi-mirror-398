from pydantic import BaseModel, ConfigDict


class AssistantFileUploadResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    message: str
    file_id: str
    assistant_id: str


__all__ = ["AssistantFileUploadResponse"]
