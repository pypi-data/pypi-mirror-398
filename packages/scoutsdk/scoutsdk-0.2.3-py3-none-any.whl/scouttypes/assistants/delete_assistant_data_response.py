from pydantic import BaseModel


class DeleteAssistantDataResponse(BaseModel):
    message: str
    assistant_id: str


__all__ = ["DeleteAssistantDataResponse"]
