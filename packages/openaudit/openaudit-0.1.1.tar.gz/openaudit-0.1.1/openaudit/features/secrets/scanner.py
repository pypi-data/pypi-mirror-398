import re
import math
import os
from typing import List, Pattern
from pathlib import Path
from openaudit.core.interfaces import ScannerProtocol
from openaudit.core.domain import Finding, ScanContext, Rule, Severity

class SecretScanner(ScannerProtocol):
    def __init__(self, rules: List[Rule]):
        self.rules = [r for r in rules if r.category in ["secret", "general"]]
        self._compile_rules()

    def _compile_rules(self):
        self.compiled_rules = []
        for rule in self.rules:
            try:
                self.compiled_rules.append((rule, re.compile(rule.regex)))
            except re.error as e:
                print(f"Error compiling regex for rule {rule.id}: {e}")

    def scan(self, context: ScanContext) -> List[Finding]:
        findings = []
        target = Path(context.target_path)
        
        if not target.exists():
            return findings

        if target.is_file():
            findings.extend(self._scan_file(target))
        else:
            for root, dirs, files in os.walk(target):
                # Filter dirs in-place
                if context.ignore_manager:
                     i = 0
                     while i < len(dirs):
                         d_path = Path(root) / dirs[i]
                         if context.ignore_manager.is_ignored(d_path):
                             del dirs[i]
                         else:
                             i += 1

                # Basic ignore logic (manual fallback)
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = Path(root) / file
                    if context.ignore_manager and context.ignore_manager.is_ignored(file_path):
                        continue
                    findings.extend(self._scan_file(file_path))
        
        return findings

    def _scan_file(self, file_path: Path) -> List[Finding]:
        findings = []
        try:
            # Skip large files > 1MB for performance
            if file_path.stat().st_size > 1024 * 1024:
                return findings
                
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            for rule, regex in self.compiled_rules:
                for line_num, line in enumerate(content.splitlines(), start=1):
                    for match in regex.finditer(line):
                        if match.lastindex and match.lastindex >= 1:
                            secret_candidate = match.group(1)
                        else:
                            secret_candidate = match.group(0)
                        
                        if rule.entropy_check:
                            if self._calculate_entropy(secret_candidate) < 4.5: # Threshold
                                continue
                        
                        findings.append(Finding(
                            rule_id=rule.id,
                            description=rule.description,
                            file_path=str(file_path),
                            line_number=line_num,
                            secret_hash=self._mask_secret(secret_candidate),
                            severity=rule.severity,
                            confidence=rule.confidence,
                            category="secret"
                        ))
        except Exception as e:
            # log or ignore
            pass
            
        return findings

    def _calculate_entropy(self, data: str) -> float:
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def _mask_secret(self, secret: str) -> str:
        if len(secret) <= 4:
            return "*" * len(secret)
        return secret[:2] + "*" * (len(secret) - 4) + secret[-2:]
