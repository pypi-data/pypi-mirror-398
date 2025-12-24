import json
from typing import List, Optional
from openaudit.core.domain import Finding, Severity
from .base import Reporter

class JSONReporter(Reporter):
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path

    def report(self, findings: List[Finding]):
        summary = {
            "total": len(findings),
            "critical": len([f for f in findings if f.severity == Severity.CRITICAL]),
            "high": len([f for f in findings if f.severity == Severity.HIGH]),
            "medium": len([f for f in findings if f.severity == Severity.MEDIUM]),
            "low": len([f for f in findings if f.severity == Severity.LOW]),
        }

        # Pydantic v2 serialization 
        findings_data = [f.model_dump(mode='json') for f in findings]
        
        data = {
            "summary": summary,
            "findings": findings_data
        }
        
        json_content = json.dumps(data, indent=2, default=str)
        
        if self.output_path:
            try:
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                print(f"Report saved to {self.output_path}")
            except IOError as e:
                print(f"Error saving report to {self.output_path}: {e}")
        else:
            print(json_content)
