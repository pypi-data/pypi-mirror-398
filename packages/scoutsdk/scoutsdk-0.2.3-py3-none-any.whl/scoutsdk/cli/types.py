from pydantic import BaseModel


class EmptyRequest(BaseModel):
    pass


class GenericResponse(BaseModel):
    model_config = {
        "extra": "allow",  # Allow extra fields
    }
