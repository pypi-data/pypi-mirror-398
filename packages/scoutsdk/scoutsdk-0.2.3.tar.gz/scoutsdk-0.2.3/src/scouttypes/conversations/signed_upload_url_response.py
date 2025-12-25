from typing import Any
from pydantic import BaseModel, field_validator, ConfigDict
from .upload_mode import UploadMode


class SignedUploadUrlResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    url: str
    fields: dict[str, Any] = {}
    prefix: str = ""
    protected_url: str = ""
    upload_mode: UploadMode = UploadMode.POST
    content_type: str = ""

    @field_validator("protected_url")
    @classmethod
    def validate_protected_url(cls, protected_url: str) -> str:
        if not protected_url.startswith("/protected"):
            protected_url = f"/protected/{protected_url}"
        return protected_url


__all__ = ["SignedUploadUrlResponse"]
