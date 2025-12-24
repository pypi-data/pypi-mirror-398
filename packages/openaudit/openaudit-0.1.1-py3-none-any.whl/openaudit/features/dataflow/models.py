from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set

class FlowNode(BaseModel):
    """
    Represents a function, method, or file in the data flow graph.
    """
    id: str  # unique identifier, e.g., "module.function"
    name: str # display name, e.g., "get_user_data"
    file_path: str
    type: str = "function" # function, class, file, entrypoint
    line_number: int = 0

class FlowEdge(BaseModel):
    """
    Represents a call or data dependency between two nodes.
    """
    source_id: str
    target_id: str
    relation: str = "calls" # calls, imports, inherits
    description: Optional[str] = None

class DataFlowGraph(BaseModel):
    """
    The graph representing the data flow across the project.
    """
    nodes: Dict[str, FlowNode] = Field(default_factory=dict)
    edges: List[FlowEdge] = Field(default_factory=list)
    sinks: List[str] = Field(default_factory=list, description="IDs of sensitive sinks (e.g. db execution)")
    sources: List[str] = Field(default_factory=list, description="IDs of entry points (e.g. api handlers)")
