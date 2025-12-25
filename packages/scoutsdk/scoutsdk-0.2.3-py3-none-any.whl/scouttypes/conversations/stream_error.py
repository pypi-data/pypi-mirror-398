from pydantic import BaseModel, ConfigDict


class StreamError(BaseModel):
    model_config = ConfigDict(extra="allow")
    error_code: str
    reference_id: str
    message: str


__all__ = ["StreamError"]
