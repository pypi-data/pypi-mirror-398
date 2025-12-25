from typing import List, Optional
from pydantic import BaseModel


class TargetDependency(BaseModel):
    name: str
    import_path: str


class TargetState(BaseModel):
    name: str
    type: Optional[str]
    reactive: bool


class TargetAction(BaseModel):
    name: str
    async_action: bool


class TargetComponent(BaseModel):
    name: str
    role: str  # component | service
    file_name: str
    selector: Optional[str]
    state: List[TargetState]
    actions: List[TargetAction]
    dependencies: List[TargetDependency]


class TargetFrameworkIR(BaseModel):
    framework: str
    version: str
    components: List[TargetComponent]
