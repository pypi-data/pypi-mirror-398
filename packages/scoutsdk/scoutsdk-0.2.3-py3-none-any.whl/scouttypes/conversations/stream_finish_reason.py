from enum import StrEnum


class StreamFinishReason(StrEnum):
    STOP = "stop"
    ERROR = "error"
    TOOL_CALL = "tool_call"
    REQUIRES_CONFIRMATION = "requires_confirmation"


__all__ = ["StreamFinishReason"]
