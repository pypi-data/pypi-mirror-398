from pydantic import BaseModel, ConfigDict


class SignedUrlResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str


__all__ = ["SignedUrlResponse"]
