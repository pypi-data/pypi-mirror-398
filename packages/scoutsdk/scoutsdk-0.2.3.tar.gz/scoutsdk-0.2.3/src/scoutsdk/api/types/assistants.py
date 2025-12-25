from pydantic import BaseModel

# This types file is deprecated
# The types are now in scouttypes and one file per type.

# Import the moved types from their new location


class AssistantResponse(BaseModel):
    message: str
    assistant_id: str
