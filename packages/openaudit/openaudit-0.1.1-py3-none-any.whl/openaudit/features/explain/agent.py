from typing import List, Dict, Optional
from openaudit.ai.models import PromptContext, AIResult
from openaudit.ai.protocol import AgentProtocol
from openaudit.core.domain import Severity, Confidence
import random

class ExplainAgent(AgentProtocol):
    """
    AI Agent that explains code functionality and security implications.
    """
    name = "explain-agent"
    description = "Generates human-readable explanations and security insights for code."

    def run(self, context: PromptContext) -> AIResult:
        from openaudit.ai.engine import AIEngine
        engine = AIEngine()
        
        if not engine.is_available():
            return AIResult(
                analysis="AI not configured. Please set API key to use this feature.",
                risk_score=0.0,
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                is_advisory=True
            )

        system_prompt = "You are a technical expert. Explain the code and identify security risks."
        user_prompt = f"Code:\n{context.code_snippet}\n\nExplain and Analyze."

        try:
            response = engine.chat_completion(system_prompt, user_prompt)
            return AIResult(
                analysis=response,
                risk_score=0.1,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                is_advisory=True
            )
        except Exception as e:
            return AIResult(
                analysis=f"Error: {str(e)}",
                risk_score=0.1,
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                is_advisory=True
            )

    def stream(self, context: PromptContext):
        """
        Stream the explanation.
        Yields chunks of text.
        """
        from openaudit.ai.engine import AIEngine
        engine = AIEngine()
        
        if not engine.is_available():
            yield "AI not configured. Please set API key."
            return

        system_prompt = "You are a technical expert. Explain the code and identify security risks. Use Markdown."
        user_prompt = f"Code:\n{context.code_snippet}\n\nExplain and Analyze."

        try:
            for chunk in engine.chat_completion_stream(system_prompt, user_prompt):
                yield chunk
        except Exception as e:
            yield f"\n\nError during streaming: {str(e)}"
