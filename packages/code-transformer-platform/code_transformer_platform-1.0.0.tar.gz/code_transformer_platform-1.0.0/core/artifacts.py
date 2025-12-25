from pydantic import BaseModel
from typing import List, Dict, Optional,Any

class ScanIndex(BaseModel):
    component_to_files: Dict[str, List[str]]

class FileInventory(BaseModel):
    files: List[str]


class FileMetadata(BaseModel):
    path: str
    extension: str
    language: Optional[str]
    role: Optional[str]


class DependencyGraph(BaseModel):
    graph: Dict[str, List[str]]


class LanguageSummary(BaseModel):
    languages: Dict[str, int]


class ResolvedDependencyGraph(BaseModel):
    internal_graph: Dict[str, List[str]]


class ExternalDependencies(BaseModel):
    dependencies: List[str]


class DependencyReport(BaseModel):
    cyclic_dependencies: List[List[str]]
    entry_points: List[str]


class SourceAST(BaseModel):
    file_path: str
    language: str
    ast: Any   # language-specific tree


class ASTIndex(BaseModel):
    asts: Dict[str, SourceAST]


class ParseReport(BaseModel):
    parsed_files: List[str]
    failed_files: Dict[str, str]



class IRState(BaseModel):
    name: str
    type: Optional[str]
    source: str  # local | remote | derived


class IRAction(BaseModel):
    name: str
    kind: str  # sync | async
    effects: List[str]


class IRDependency(BaseModel):
    name: str
    type: str  # service | component | external


class IRView(BaseModel):
    kind: str  # table | form | list | custom
    fields: List[str]


class IRComponent(BaseModel):
    name: str
    component_type: str  # ui | service | model
    state: List[IRState]
    actions: List[IRAction]
    view: Optional[IRView]
    dependencies: List[IRDependency]


class CanonicalIR(BaseModel):
    components: List[IRComponent]

class TargetMapping(BaseModel):
    component: str
    target_framework: str
    ui_pattern: str
    state_management: str
    strategy: str