from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from .image_aspect_ratio import ImageAspectRatio
from .image_quality import ImageQuality
from .image_background import ImageBackground


class ImageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str
    aspect_ratio: Optional[ImageAspectRatio] = ImageAspectRatio.SQUARE
    model: Optional[str] = None
    quality: Optional[ImageQuality] = ImageQuality.DEFAULT
    background: Optional[ImageBackground] = ImageBackground.OPAQUE
    nb_outputs: Optional[int] = 1
    user_id: Optional[UUID] = None


__all__ = ["ImageRequest"]
