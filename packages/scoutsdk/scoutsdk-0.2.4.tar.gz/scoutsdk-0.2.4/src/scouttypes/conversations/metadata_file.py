from pydantic import BaseModel, ConfigDict


class MetadataFile(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    content_type: str


__all__ = ["MetadataFile"]
