from pydantic import BaseModel, ConfigDict


class AudioTranscriptionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    transcript: str
    data: dict


__all__ = ["AudioTranscriptionResponse"]
