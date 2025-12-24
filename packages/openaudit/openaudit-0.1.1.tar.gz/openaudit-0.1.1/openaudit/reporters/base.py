from abc import ABC, abstractmethod
from typing import List
from openaudit.core.domain import Finding

class Reporter(ABC):
    @abstractmethod
    def report(self, findings: List[Finding]):
        """Output the findings to the destination"""
        pass
