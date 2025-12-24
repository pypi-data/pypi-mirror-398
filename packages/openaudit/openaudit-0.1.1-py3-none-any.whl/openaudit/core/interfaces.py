from typing import Protocol, List
from .domain import Finding, ScanContext

class ScannerProtocol(Protocol):
    def scan(self, context: ScanContext) -> List[Finding]:
        """
        Scans using the provided context and returns a list of findings.
        """
        ...
