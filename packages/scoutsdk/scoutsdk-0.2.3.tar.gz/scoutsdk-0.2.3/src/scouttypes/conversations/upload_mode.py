from enum import StrEnum


class UploadMode(StrEnum):
    AZURE = "azure"
    POST = "post"


__all__ = ["UploadMode"]
