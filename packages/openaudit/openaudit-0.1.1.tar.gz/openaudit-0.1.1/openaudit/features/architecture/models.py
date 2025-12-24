from pydantic import BaseModel, Field
from typing import List, Dict, Set, Optional

class ModuleNode(BaseModel):
    """
    Represents a file or directory in the codebase.
    """
    name: str
    path: str
    type: str = Field(..., description="file or directory")
    imports: List[str] = Field(default_factory=list)
    children: List['ModuleNode'] = Field(default_factory=list)
    
    class Config:
        # Needed for recursive models
        arbitrary_types_allowed = True

class ProjectStructure(BaseModel):
    """
    Represents the entire project structure and dependency graph.
    """
    root_path: str
    modules: List[ModuleNode]
    # Simple adjacency list: "module_a" -> ["module_b", "module_c"]
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
