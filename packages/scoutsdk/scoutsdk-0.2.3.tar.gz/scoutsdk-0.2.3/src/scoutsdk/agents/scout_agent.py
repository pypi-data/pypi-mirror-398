from typing import Callable, Optional
from pydantic import BaseModel


class ScoutAgent(BaseModel):
    id: str
    # Added first to the system instructions
    instructions: Optional[str] = None
    # Method called and added to the instructions when set
    # Usefull when instructions could take time to build
    # Ex: Fetching a schema from a DB
    build_instructions: Optional[Callable[[], str]] = None
    temperature: float = 0.1
    handoff_description: Optional[str] = None
    model_id: Optional[str] = None
    tools: Optional[list[Callable]] = None
    allowed_tools: list[str] = []
    handoff_ids: Optional[list[str]] = None  # Handoff ids

    @property
    def resolved_instructions(self) -> str:
        all_instructions = []
        if self.instructions:
            all_instructions.append(self.instructions)
        if self.build_instructions:
            all_instructions.append(self.build_instructions())
        return ("\n").join(all_instructions)
