import re
from typing import List
import os
from pathlib import Path

from openaudit.core.interfaces import ScannerProtocol
from openaudit.core.domain import Finding, ScanContext, Rule

class ConfigScanner(ScannerProtocol):
    def __init__(self, rules: List[Rule]):
        self.rules = rules
        self.config_rules = [r for r in rules if r.category in ["config", "infrastructure"]]
        self._compile_rules()

    def _compile_rules(self):
        self.compiled_rules = []
        for rule in self.config_rules:
            try:
                self.compiled_rules.append((rule, re.compile(rule.regex, re.MULTILINE)))
            except Exception:
                pass

    def scan(self, context: ScanContext) -> List[Finding]:
        findings = []
        target = Path(context.target_path)
        
        if not target.exists():
            return findings

        files_to_scan = []
        if target.is_file():
            if context.ignore_manager and context.ignore_manager.is_ignored(target):
                 pass
            else:
                 files_to_scan.append(target)
        else:
            for root, dirs, files in os.walk(target):
                # Filter dirs based on ignores?
                # pathspec match_file vs dirs?
                # We should probably filter dirs to avoid walking them.
                # But pathspec handles relative paths.
                
                # Filter dirs in-place
                if context.ignore_manager:
                     # Check which dirs to exclude
                     # dirs[:] = [d for d in dirs if not context.ignore_manager.is_ignored(Path(root) / d)]
                     # The above is tricky because pathspec usually matches files or globs.
                     # Let's iterate and check.
                     i = 0
                     while i < len(dirs):
                         d_path = Path(root) / dirs[i]
                         if context.ignore_manager.is_ignored(d_path):
                             del dirs[i]
                         else:
                             i += 1
                
                # Remove .git if not already handled by ignore manager
                if '.git' in dirs:
                    dirs.remove('.git')

                for file in files:
                    file_path = Path(root) / file
                    if context.ignore_manager and context.ignore_manager.is_ignored(file_path):
                        continue
                    files_to_scan.append(file_path)

        for file_path in files_to_scan:
            findings.extend(self._scan_file(file_path, context))
            
        return findings

    def _scan_file(self, file_path: Path, context: ScanContext = None) -> List[Finding]:
        findings = []
        filename = file_path.name.lower()
        
        # Determine file type
        is_env = filename == '.env' or filename.endswith('.env')
        is_dockerfile = 'dockerfile' in filename
        is_compose = filename in ['docker-compose.yml', 'docker-compose.yaml']

        if not (is_env or is_dockerfile or is_compose):
            return findings

        if is_env:
            # Special finding just for existence
            findings.append(Finding(
                rule_id="CONF_DOTENV_EXPOSED",
                description="Dotenv file found. Ensure this is not committed.",
                file_path=str(file_path),
                line_number=0,
                secret_hash="N/A",
                severity="medium",
                confidence="high",
                category="config",
                remediation="Add to .gitignore"
            ))

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Rule-based scanning
            for rule, regex in self.compiled_rules:
                # Filter rules based on file context to avoid noise (optional, but good practice)
                if is_env and rule.category == "infrastructure": continue
                if (is_dockerfile or is_compose) and rule.category == "config": continue

                for line_num, line in enumerate(content.splitlines(), 1):
                    match = regex.search(line)
                    if match:
                        masked_val = match.group(0).strip()
                        
                        # Custom masking for config values
                        if rule.category == "config":
                            if "=" in masked_val:
                                parts = masked_val.split("=", 1)
                                if len(parts) == 2:
                                    val = parts[1].strip()
                                    if len(val) > 4:
                                        val = val[:2] + "*" * (len(val)-4) + val[-2:]
                                    masked_val = f"{parts[0]}={val}"
                        elif rule.category == "infrastructure":
                             # usually don't need masking for docker instructions
                             pass

                        findings.append(Finding(
                            rule_id=rule.id,
                            description=rule.description,
                            file_path=str(file_path),
                            line_number=line_num,
                            secret_hash=masked_val,
                            severity=rule.severity,
                            confidence=rule.confidence,
                            category=rule.category,
                            remediation=rule.remediation
                        ))
        except Exception:
            pass

        return findings
