import re
from typing import List
from pathlib import Path

# Placeholder for consent storage file
CONSENT_FILE = Path(".openaudit_consent")

class Redactor:
    """
    Utility to redaction secrets from text before sending to an LLM.
    Uses basic patterns to identify potential secrets.
    """
    
    # Simple regex for common secrets (placeholder, ideally reuse SecretScanner patterns)
    # This is a safety net; specific scanners should also redact.
    SENSITIVE_PATTERNS = [
        r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{8,})['\"]?",
        r"(?i)private[_-]?key",
    ]

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Replace sensitive patterns with [REDACTED].
        """
        redacted_text = text
        for pattern in cls.SENSITIVE_PATTERNS:
            redacted_text = re.sub(pattern, lambda m: m.group(0).replace(m.group(2), "[REDACTED]"), redacted_text)
        return redacted_text

class ConsentManager:
    """
    Manages user consent for AI features.
    """
    
    @staticmethod
    def has_consented() -> bool:
        """
        Check if the user has explicitly consented to AI usage.
        For now, we check for a specific marker file or env var.
        """
        # In a real impl, this might check a global config file in user home
        return CONSENT_FILE.exists()

    @staticmethod
    def grant_consent():
        """
        Grant consent creates the marker.
        """
        CONSENT_FILE.touch()

    @staticmethod
    def revoke_consent():
        """
        Revoke consent removes the marker.
        """
        if CONSENT_FILE.exists():
            CONSENT_FILE.unlink()
