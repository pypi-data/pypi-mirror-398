from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def level(self) -> int:
        return {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }.get(self.value, 0)
    
    def __ge__(self, other):
        if isinstance(other, Severity):
            return self.level >= other.level
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Severity):
            return self.level > other.level
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Severity):
            return self.level <= other.level
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Severity):
            return self.level < other.level
        return NotImplemented

class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

from typing import Any

class ScanContext:
    def __init__(self, target_path: str, deep_scan: bool = False, ignore_manager: Any = None):
        self.target_path = target_path
        self.deep_scan = deep_scan
        self.ignore_manager = ignore_manager

class Rule(BaseModel):
    id: str
    description: str
    regex: str
    entropy_check: bool = False
    severity: Severity = Severity.HIGH
    confidence: Confidence = Confidence.MEDIUM
    category: str = "general"
    remediation: str = "No remediation provided."

class Finding(BaseModel):
    rule_id: str
    description: str
    file_path: str
    line_number: int
    secret_hash: str = Field(..., description="The masked secret content")
    severity: Severity = Severity.HIGH
    confidence: Confidence = Confidence.MEDIUM
    category: str = "secret"
    remediation: str = "No remediation provided."
    is_ai_generated: bool = Field(default=False, description="Whether this finding was generated/enriched by AI")

    def __str__(self):
        return f"[{self.severity.upper()}] {self.rule_id} in {self.file_path}:{self.line_number}"
