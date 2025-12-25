from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    FUNCTION = "function"
    MODEL = "model"


__all__ = ["MessageRole"]
