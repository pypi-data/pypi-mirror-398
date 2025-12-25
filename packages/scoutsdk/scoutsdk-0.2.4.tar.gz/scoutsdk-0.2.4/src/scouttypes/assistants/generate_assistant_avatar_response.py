from pydantic import BaseModel, ConfigDict


class GenerateAssistantAvatarResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    protected_url: str


__all__ = ["GenerateAssistantAvatarResponse"]
