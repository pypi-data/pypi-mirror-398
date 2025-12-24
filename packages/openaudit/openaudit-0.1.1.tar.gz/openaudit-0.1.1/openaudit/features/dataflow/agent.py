from typing import List, Dict
from openaudit.ai.models import PromptContext, AIResult
from openaudit.core.domain import Severity, Confidence
from .models import DataFlowGraph, FlowNode, FlowEdge

class CrossFileAgent:
    """
    AI Agent that analyzes data flow graphs for cross-file vulnerabilities.
    """
    name = "cross-file-agent"
    description = "Analyzes data flow across modules to detect risky paths."

    def run_on_graph(self, graph: DataFlowGraph) -> List[AIResult]:
        results = []
        
        # 1. Algorithmic Path Finding (Source -> Sink)
        # Simple BFS for demonstration
        for source_id in graph.sources:
            paths = self._bfs_paths(graph, source_id, graph.sinks)
            for path in paths:
                # 2. Analyze Path
                result = self._analyze_path(graph, path)
                if result:
                    results.append(result)
        
        if not results:
             # Just a summary if no specific vulns found
             results.append(AIResult(
                 analysis=f"Scanned {len(graph.nodes)} functions and {len(graph.edges)} calls. No critical paths to sinks found.",
                 risk_score=0.0,
                 severity=Severity.LOW,
                 confidence=Confidence.LOW,
                 suggestion="Maintain loose coupling.",
                 is_advisory=True
             ))

        return results

    def _bfs_paths(self, graph: DataFlowGraph, start: str, goals: List[str]) -> List[List[str]]:
        queue = [(start, [start])]
        paths = []
        visited = set() # Avoid cycles
        
        while queue:
            (vertex, path) = queue.pop(0)
            if len(path) > 5: # Limit depth
                continue
                
            for edge in graph.edges:
                if edge.source_id == vertex:
                    next_node = edge.target_id
                    if next_node in goals:
                        paths.append(path + [next_node])
                    elif next_node not in path: # precise cycle check for current path
                        queue.append((next_node, path + [next_node]))
        return paths

    def _analyze_path(self, graph: DataFlowGraph, path: List[str]) -> AIResult:
        from openaudit.ai.engine import AIEngine
        engine = AIEngine()
        
        if not engine.is_available():
             return None

        path_names = [graph.nodes[nid].name for nid in path if nid in graph.nodes]
        path_str = " -> ".join(path_names)
        
        system_prompt = "You are a specific security analyzer for data flow. Analyze if the path allows tainted user input to reach sensitive sinks. Return analysis."
        user_prompt = f"Path: {path_str}\n\nAnalyze for taint flow."
        
        try:
            response = engine.chat_completion(system_prompt, user_prompt)
            if "taint" in response.lower() or "risk" in response.lower():
                return AIResult(
                    analysis=response,
                    risk_score=0.9,
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    suggestion="Validate input at source.",
                    is_advisory=True
                )
        except Exception:
            pass
        
        return None 
