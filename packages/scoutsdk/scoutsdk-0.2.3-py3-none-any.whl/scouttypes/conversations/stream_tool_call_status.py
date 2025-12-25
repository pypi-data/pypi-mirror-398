from enum import StrEnum


class StreamToolCallStatus(StrEnum):
    PREPARING = "PREPARING"
    CALLING = "CALLING"


__all__ = ["StreamToolCallStatus"]
