from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class IRState(BaseModel):
    name: str
    type: Optional[str] = None
    source: str  # local | remote | derived
    default_value: Optional[Any] = None
    required: bool = False

class IRAction(BaseModel):
    name: str
    kind: str  # sync | async
    effects: List[str]
    params: List[str] = []
    implementation: Optional[str] = None  # Actual code implementation
    has_api_call: bool = False

class IRDependency(BaseModel):
    name: str
    type: str  # service | component | external

class IRView(BaseModel):
    kind: str  # table | form | list | custom
    fields: List[str]

class IRValidator(BaseModel):
    field: str
    type: str  # function | rule
    implementation: Optional[str] = None

class IRMethod(BaseModel):
    name: str
    params: List[str]
    implementation: str
    is_async: bool = False
    has_api_call: bool = False

class IRApiConfig(BaseModel):
    url: Optional[str] = None
    methods: Dict[str, Any] = {}

class IRAnnotation(BaseModel):
    key: str
    value: str


# Extend IRComponent
class IRComponent(BaseModel):
    name: str
    component_type: str
    state: List[IRState]
    actions: List[IRAction]
    view: Optional[IRView]
    dependencies: List[IRDependency]
    annotations: List[IRAnnotation] = []
    validators: List[IRValidator] = []
    api_config: Optional[IRApiConfig] = None
    raw_source: Optional[str] = None  # Keep original source for reference

class CanonicalIR(BaseModel):
    components: List[IRComponent]
