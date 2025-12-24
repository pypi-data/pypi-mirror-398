from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from openaudit.core.domain import Severity, Confidence

class PromptContext(BaseModel):
    """
    Context to be passed to an AI Agent.
    Contains the code to analyze, metadata, and potentially previous findings.
    """
    file_path: str
    code_snippet: str
    line_number: Optional[int] = None
    surrounding_lines: int = 5
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    # Optional: If analyzing an existing finding
    finding_id: Optional[str] = None

class AIResult(BaseModel):
    """
    Structured response from an AI Agent.
    """
    analysis: str = Field(..., description="Explanation of the analysis")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="0.0 to 1.0 risk score")
    severity: Severity
    confidence: Confidence
    suggestion: Optional[str] = None
    is_advisory: bool = True  # AI findings are advisory by default
