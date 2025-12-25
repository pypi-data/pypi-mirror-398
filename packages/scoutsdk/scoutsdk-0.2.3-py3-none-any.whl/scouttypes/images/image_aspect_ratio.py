from enum import StrEnum


class ImageAspectRatio(StrEnum):
    SQUARE = "square"
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


__all__ = ["ImageAspectRatio"]
