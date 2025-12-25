from pydantic import BaseModel


class AudioTranscriptionResponse(BaseModel):
    transcript: str
    data: dict
