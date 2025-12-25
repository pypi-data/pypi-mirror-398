from typing import Any, Optional


class ScoutMCPError(Exception):
    def __init__(
        self,
        message: str,
        assistant_id: Optional[str] = None,
        function_name: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.assistant_id = assistant_id
        self.function_name = function_name
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": str(self),
            "assistant_id": self.assistant_id,
            "function_name": self.function_name,
            "context": self.context,
        }
