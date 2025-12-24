import ast
import os
from pathlib import Path
from typing import List, Dict, Set, Optional
from openaudit.core.domain import ScanContext
from openaudit.features.architecture.models import ProjectStructure
from .models import DataFlowGraph, FlowNode, FlowEdge

class DataFlowScanner:
    """
    Builds a simplified data flow graph by analyzing python files.
    """

    def scan(self, context: ScanContext, structure: ProjectStructure) -> DataFlowGraph:
        graph = DataFlowGraph()
        # We need to process files to find definitions first, then usages.
        # Ideally, we leverage the structure from architecture scanner, but we need ASTs again.
        
        # 1. First Pass: Collect all function/class definitions
        definitions: Dict[str, FlowNode] = {} # id -> node

        # Map file paths to module names for resolution
        file_map: Dict[str, str] = {} # absolute_path -> module.name

        target_path = Path(context.target_path)

        for module in structure.modules:
            # Re-parse (or caching ASTs in structure would be better optimization later)
            file_path = Path(context.target_path) / module.path
            if not file_path.exists(): 
                 # Handle case where file_path might be absolute or relative differently
                 # Depending on how architecture scanner stores it.
                 # Assuming module.path is relative to root.
                 pass

            # Construct logical module name
            module_name = module.path.replace(os.sep, ".").replace(".py", "")
            file_map[str(file_path.absolute())] = module_name

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                # Walk for definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_id = f"{module_name}.{node.name}"
                        flow_node = FlowNode(
                            id=func_id,
                            name=node.name,
                            file_path=str(file_path),
                            type="function",
                            line_number=node.lineno
                        )
                        definitions[func_id] = flow_node
                        graph.nodes[func_id] = flow_node
                        
                        # Heuristic: Identify potential sources/sinks
                        if "handler" in node.name or "route" in node.name:
                            graph.sources.append(func_id)
                        
                        if "execute" in node.name and ("sql" in node.name or "db" in node.name or "query" in node.name):
                            graph.sinks.append(func_id)

            except Exception:
                pass


        # 2. Second Pass: Find calls (Edges)
        # This is complex because of aliasing. 
        # For MVP, we'll try to resolve direct calls and simple imports.
        
        for module in structure.modules:
            file_path = Path(context.target_path) / module.path
            module_name = module.path.replace(os.sep, ".").replace(".py", "")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                # Track local imports: alias -> full_name
                imports: Dict[str, str] = {}
                
                # Visitor to find imports and calls
                class CallVisitor(ast.NodeVisitor):
                    def __init__(self, current_function: Optional[str] = None):
                        self.current_function = current_function

                    def visit_Import(self, node):
                        for alias in node.names:
                            name = alias.name
                            asname = alias.asname or name
                            imports[asname] = name
                        self.generic_visit(node)

                    def visit_ImportFrom(self, node):
                        module = node.module or ""
                        # relative import handling simplified
                        if node.level > 0:
                             # very rough approximation for MVP
                             count = node.level
                             parts = module_name.split(".")
                             if len(parts) >= count:
                                 module = ".".join(parts[:-count]) + ("." + module if module else "")
                        
                        for alias in node.names:
                            name = alias.name
                            asname = alias.asname or name
                            full_name = f"{module}.{name}" if module else name
                            imports[asname] = full_name
                        self.generic_visit(node)

                    def visit_FunctionDef(self, node):
                        # Enter function context
                        previous = self.current_function
                        self.current_function = f"{module_name}.{node.name}"
                        self.generic_visit(node)
                        self.current_function = previous

                    def visit_Call(self, node):
                        if not self.current_function:
                            return
                        
                        # Try to resolve call
                        called_name = ""
                        if isinstance(node.func, ast.Name):
                            # Direct call: func()
                            called_name = node.func.id
                        elif isinstance(node.func, ast.Attribute):
                            # Attribute call: module.func() or obj.method()
                            # simplified: only handling module.func where module is imported
                            if isinstance(node.func.value, ast.Name):
                                base = node.func.value.id
                                if base in imports:
                                    # It's an imported module
                                    called_name = f"{imports[base]}.{node.func.attr}"
                        
                        # Resolution
                        target_id = None
                        
                        # 1. Check if it's imported as full name
                        if called_name in imports:
                            target_id = imports[called_name]
                        # 2. Check if it is the called_name logic above
                        elif called_name:
                             # Check if this matches a known definition
                             if called_name in definitions:
                                 target_id = called_name
                             
                             # Try resolving aliases in called_name
                             # e.g. defined func=sql.execute, imports sql=db.sql
                             # called_name=sql.execute -> db.sql.execute
                             parts = called_name.split(".")
                             if parts[0] in imports:
                                 resolved_base = imports[parts[0]]
                                 potential_id = f"{resolved_base}.{'.'.join(parts[1:])}"
                                 if potential_id in definitions:
                                     target_id = potential_id
                        
                        if target_id and target_id in definitions:
                             graph.edges.append(FlowEdge(
                                 source_id=self.current_function,
                                 target_id=target_id,
                                 relation="calls"
                             ))
                        
                        self.generic_visit(node)

                CallVisitor().visit(tree)
            except Exception:
                pass

        return graph
