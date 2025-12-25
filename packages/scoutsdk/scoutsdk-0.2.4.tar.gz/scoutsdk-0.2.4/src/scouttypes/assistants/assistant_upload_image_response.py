from pydantic import BaseModel, ConfigDict


class AssistantUploadImageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    content_type: str
    protected_url: str


__all__ = ["AssistantUploadImageResponse"]
