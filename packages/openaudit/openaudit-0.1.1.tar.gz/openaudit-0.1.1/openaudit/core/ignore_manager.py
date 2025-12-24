from pathlib import Path
from typing import List
import pathspec

class IgnoreManager:
    DEFAULT_IGNORES = [
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        "__pycache__",
        "node_modules",
        "venv",
        ".env", # Often we want to scan .env, but maybe ignore by default in some contexts? 
                # Actually ConfigScanner specifically looks for .env. 
                # SecretScanner might wanna scan it. 
                # Let's keep .env OUT of default ignores for now, user can add it if they want.
        "dist",
        "build",
        "coverage",
        ".tox",
        "*.egg-info"
    ]

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.spec = self._load_spec()

    def _load_spec(self) -> pathspec.PathSpec:
        patterns = self.DEFAULT_IGNORES.copy()
        
        # Load .oaignore or .openauditignore
        ignore_files = [".oaignore", ".openauditignore"]
        for f in ignore_files:
            ignore_path = self.root_path / f
            if ignore_path.exists():
                try:
                    with open(ignore_path, "r", encoding="utf-8") as pf:
                        patterns.extend(pf.read().splitlines())
                except Exception:
                    pass
        
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def is_ignored(self, file_path: Path) -> bool:
        try:
            # pathspec expects relative paths usually, or strictly strings
            rel_path = file_path.relative_to(self.root_path)
            return self.spec.match_file(str(rel_path))
        except ValueError:
            # If path is not relative to root (e.g. absolute path elsewhere), 
            # fall back to name checking or don't ignore
            return self.spec.match_file(file_path.name)
