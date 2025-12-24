import ast
import os
from pathlib import Path
from typing import List, Dict, Set
from .models import ModuleNode, ProjectStructure
from openaudit.core.domain import ScanContext

class ArchitectureScanner:
    """
    Statically analyzes the codebase to build a module tree and import graph.
    """
    
    def scan(self, context: ScanContext) -> ProjectStructure:
        root_path = Path(context.target_path)
        modules = []
        dependency_graph = {}
        
        # Walk the directory
        for root, dirs, files in os.walk(root_path):
            # Apply ignore rules (rudimentary check here, ideally use IgnoreManager)
            # Modifying dirs in-place to prune traversal
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            if context.ignore_manager:
                dirs[:] = [d for d in dirs if not context.ignore_manager.is_ignored(Path(root) / d)]
                
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                full_path = Path(root) / file
                rel_path = full_path.relative_to(root_path)
                
                if context.ignore_manager and context.ignore_manager.is_ignored(full_path):
                    continue

                imports = self._extract_imports(full_path)
                
                # Add to graph
                module_name = str(rel_path).replace(os.sep, ".").replace(".py", "")
                dependency_graph[module_name] = imports
                
                node = ModuleNode(
                    name=file,
                    path=str(rel_path),
                    type="file",
                    imports=imports
                )
                modules.append(node)
                
        # TODO: Ideally maintain tree structure in 'modules', currently a flat list for simplicity
        # but the Model supports nesting. For the AI summary, a flat list with paths is often enough.

        return ProjectStructure(
            root_path=str(root_path),
            modules=modules,
            dependency_graph=dependency_graph
        )

    def _extract_imports(self, file_path: Path) -> List[str]:
        """
        Parse file with AST and extract imported names.
        """
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    # Handle relative imports (e.g., from . import utils)
                    if node.level > 0:
                        module = "." * node.level + module
                    imports.append(module)
        except Exception:
            # If parsing fails, just ignore (could be syntax error or non-utf8)
            pass
            
        return imports
