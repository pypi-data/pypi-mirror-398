from typing import List
from pydantic import BaseModel


class MigrationStep(BaseModel):
    step_id: int
    component: str
    depends_on: List[str]
    files: List[str]
    risk_level: str  # low | medium | high
    notes: List[str]


class MigrationPlan(BaseModel):
    source_stack: str
    target_stack: str
    steps: List[MigrationStep]
