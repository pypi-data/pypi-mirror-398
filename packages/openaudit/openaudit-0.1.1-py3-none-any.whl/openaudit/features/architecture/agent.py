from openaudit.ai.models import PromptContext, AIResult
from openaudit.ai.protocol import AgentProtocol
from openaudit.core.domain import Severity, Confidence
from .models import ProjectStructure
import json

class ArchitectureAgent:
    """
    AI Agent that reviews the project structure.
    """
    name = "architecture-agent"
    description = "Analyzes module headers and dependencies to identify architectural issues."

    def run_on_structure(self, structure: ProjectStructure) -> AIResult:
        """
        Specialized run method that takes the structured object directly.
        """
        from openaudit.ai.engine import AIEngine
        engine = AIEngine()
        
        if not engine.is_available():
             return None

        # Prepare Prompt
        system_prompt = "You are a senior software architect. Analyze the project structure for modularity, circular dependencies, and architectural risks. Return a JSON response with analysis, risk_score (0-1), and suggestion."
        
        # Simplify structure for prompt to save tokens
        modules_summary = [f"{m.path} imports {m.imports}" for m in structure.modules]
        user_prompt = f"Project Structure:\n{json.dumps(modules_summary, indent=2)}\n\nAnalyze this structure."

        try:
            response = engine.chat_completion(system_prompt, user_prompt)
            # Parse response (assuming text for now, but ideal agents verify JSON)
            # For robustness, we'll wrap the text in AIResult
            return AIResult(
                analysis=response,
                risk_score=0.5, # Placeholder, ideally parsed from response
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                suggestion="Review AI detailed analysis.",
                is_advisory=True
            )
        except Exception as e:
             return AIResult(
                analysis=f"AI Analysis failed: {str(e)}",
                risk_score=0.0,
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                is_advisory=True
            )

    def run(self, context: PromptContext) -> AIResult:
        # Standard protocol entry point
        # We expect 'metadata' to contain the structure or we parse the code_snippet as JSON
        # This might need adapter logic.
        return AIResult(
            analysis="Architecture analysis not applicable on single file context via generic run.",
            risk_score=0.0,
            severity=Severity.LOW,
            confidence=Confidence.LOW
        )
