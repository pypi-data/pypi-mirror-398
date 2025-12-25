from pydantic import BaseModel, field_validator
from typing import Any
from enum import StrEnum


class UploadMode(StrEnum):
    AZURE = "azure"
    POST = "post"


class SignedUploadUrlResponse(BaseModel):
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
