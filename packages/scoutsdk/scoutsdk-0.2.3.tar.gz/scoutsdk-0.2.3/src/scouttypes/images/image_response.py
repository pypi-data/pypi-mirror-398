from pydantic import BaseModel, ConfigDict


class ImageWithMetadata(BaseModel):
    base64: str
    mime_type: str


class ImageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    images: list[ImageWithMetadata]


__all__ = ["ImageResponse", "ImageWithMetadata"]
