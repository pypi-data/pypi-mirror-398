from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from .shared_user import SharedUser
from .shared_group import SharedGroup


class ModelVisibility(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
    shared_users: Optional[List[SharedUser]] = None
    collaborators: Optional[List[SharedUser]] = None
    groups: Optional[List[SharedGroup]] = None
    collaborator_groups: Optional[List[SharedGroup]] = None


__all__ = ["ModelVisibility"]
