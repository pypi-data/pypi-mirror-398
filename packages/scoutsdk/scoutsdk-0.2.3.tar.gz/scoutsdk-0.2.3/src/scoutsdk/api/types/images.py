from typing import Optional
from uuid import UUID
from enum import StrEnum
from pydantic import BaseModel
from collections import namedtuple

ImageFileObject = namedtuple("ImageFileObject", ["filename", "content", "content_type"])


class ImageAspectRatio(StrEnum):
    SQUARE = "square"
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class ImageQuality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DEFAULT = "default"


class ImageBackground(StrEnum):
    OPAQUE = "opaque"
    TRANSPARENT = "transparent"


class ImageRequest(BaseModel):
    prompt: str
    aspect_ratio: Optional[ImageAspectRatio] = ImageAspectRatio.SQUARE
    model: Optional[str] = None
    quality: Optional[ImageQuality] = ImageQuality.DEFAULT
    background: Optional[ImageBackground] = ImageBackground.OPAQUE
    user_id: Optional[UUID] = None


class ImageResponse(BaseModel):
    content: bytes
    content_type: str
