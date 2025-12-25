from pydantic import BaseModel


class AsyncJobResponse(BaseModel):
    run_protected_url: str


__all__ = ["AsyncJobResponse"]
