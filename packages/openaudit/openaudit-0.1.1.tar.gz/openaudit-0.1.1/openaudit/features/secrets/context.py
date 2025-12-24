from pathlib import Path
from typing import Optional

class SecretContextExtractor:
    """
    Extracts code context surrounding a finding.
    """
    
    @staticmethod
    def get_context(file_path: str, line_number: int, window: int = 5) -> str:
        """
        Read the file and return lines around the finding.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return ""
            
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            start = max(0, line_number - 1 - window)
            end = min(len(lines), line_number + window)
            
            return "".join(lines[start:end])
        except Exception:
            return ""
