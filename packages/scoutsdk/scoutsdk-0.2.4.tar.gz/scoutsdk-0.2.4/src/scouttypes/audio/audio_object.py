from typing import Optional
from pydantic import BaseModel


class AudioObject(BaseModel):
    filename: str
    protected_url: Optional[str] = None
    base64: Optional[str] = None


__all__ = ["AudioObject"]
