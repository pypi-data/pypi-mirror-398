from enum import StrEnum


class ImageQuality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DEFAULT = "default"


__all__ = ["ImageQuality"]
