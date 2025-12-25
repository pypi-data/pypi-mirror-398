from typing import Optional
from pydantic import BaseModel
from .audio_object import AudioObject


class AudioTranscriptionRequest(BaseModel):
    conversation_id: Optional[str] = None
    audio: AudioObject
    model: Optional[str] = None
    execute_async: bool = True
    model_args: Optional[dict] = None


__all__ = ["AudioTranscriptionRequest"]
