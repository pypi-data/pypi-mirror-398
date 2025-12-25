from enum import Enum


class FileType(str, Enum):
    """File types supported by Scout assistants."""

    KNOWLEDGE = "KNOWLEDGE"
    CUSTOM_FUNCTIONS = "CUSTOM_FUNCTIONS"
    ASSISTANT_TEMPLATES = "ASSISTANT_TEMPLATES"
    SHARED_CUSTOM_FUNCTIONS = "SHARED_CUSTOM_FUNCTIONS"


__all__ = ["FileType"]
