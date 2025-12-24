from typing import Protocol, runtime_checkable
from openaudit.ai.models import PromptContext, AIResult

@runtime_checkable
class AgentProtocol(Protocol):
    """
    Interface that all AI Agents must fulfill.
    """
    name: str
    description: str

    def run(self, context: PromptContext) -> AIResult:
        """
        Execute the agent on the given context.
        """
        ...
