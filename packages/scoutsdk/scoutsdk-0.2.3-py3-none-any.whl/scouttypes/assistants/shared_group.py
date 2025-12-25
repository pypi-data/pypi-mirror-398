from pydantic import BaseModel, ConfigDict


class SharedGroup(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str


__all__ = ["SharedGroup"]
