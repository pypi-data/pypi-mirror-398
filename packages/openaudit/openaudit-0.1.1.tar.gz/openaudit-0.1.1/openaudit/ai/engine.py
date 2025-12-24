from typing import Optional, List
import openai
from openaudit.core.config import ConfigManager
from openaudit.core.domain import Severity, Confidence
from openaudit.ai.models import AIResult
from openai import OpenAI, OpenAIError

class AIEngine:
    """
    Centralized engine for AI model interactions.
    """
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client: Optional[OpenAI] = None
        self._initialize_client()

    def _initialize_client(self):
        api_key = self.config_manager.get_api_key()
        if api_key:
            self.client = OpenAI(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def chat_completion(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> Optional[str]:
        """
        Executes a chat completion request.
        """
        if not self.client:
            # Try re-initializing in case config changed
            self._initialize_client()
            if not self.client:
                raise RuntimeError("OpenAI API key not configured. Run 'openaudit config set-key <KEY>' or set OPENAI_API_KEY env var.")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            # creating a dummy result on error or re-raising?
            # For now, let's log and re-raise to be handled by caller or CLI
            raise RuntimeError(f"OpenAI API Error: {str(e)}")

    def chat_completion_stream(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o"):
        """
        Executes a chat completion request with streaming.
        Yields chunks of the response content.
        """
        if not self.client:
            self._initialize_client()
            if not self.client:
                raise RuntimeError("OpenAI API key not configured. Run 'openaudit config set-key <KEY>' or set OPENAI_API_KEY env var.")

        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API Error: {str(e)}")

