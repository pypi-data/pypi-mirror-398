from openaudit.ai.models import PromptContext, AIResult
from openaudit.ai.protocol import AgentProtocol
from openaudit.core.domain import Severity, Confidence, Finding

class SecretConfidenceAgent:
    """
    AI Agent that reviews secret findings to adjust confidence.
    """
    name = "secret-confidence-agent"
    description = "Analyzes context to distinguish test secrets from real ones."

    def run(self, context: PromptContext) -> AIResult:
        from openaudit.ai.engine import AIEngine
        engine = AIEngine()
        if not engine.is_available():
            # No fallback, return None to indicate no analysis possible
            return None

        snippet = context.code_snippet
        system_prompt = "You are a secret scanning expert. Analyze the context of a potential secret. Determine if it is a TEST/MOCK secret or a REAL production secret. Respond ONLY with valid JSON in the format: {\"is_test\": boolean, \"reason\": \"string\"}"
        user_prompt = f"Code Context:\n{snippet}\n\nIs this a real secret?"
        
        try:
            import json
            response = engine.chat_completion(system_prompt, user_prompt)
            
            # Clean up potential markdown formatting in response (e.g. ```json ... ```)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.strip("`")
                if cleaned_response.startswith("json"):
                    cleaned_response = cleaned_response[4:]
            
            data = json.loads(cleaned_response)
            is_test = data.get("is_test", False)
            reason = data.get("reason", "No reason provided.")
            
            if is_test:
                 return AIResult(
                    analysis=f"AI identified this as a likely TEST/MOCK secret. Reason: {reason}",
                    risk_score=0.1,
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    suggestion="Mark as safe.",
                    is_advisory=True
                )
            else:
                 return AIResult(
                    analysis=f"AI identified this as a likely REAL secret. Reason: {reason}",
                    risk_score=0.9,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    suggestion="Rotate immediately.",
                    is_advisory=True
                )

        except Exception as e:
            return AIResult(
                analysis=f"Error: {str(e)}",
                risk_score=0.5,
                severity=Severity.MEDIUM,
                confidence=Confidence.LOW,
                is_advisory=True
            )
