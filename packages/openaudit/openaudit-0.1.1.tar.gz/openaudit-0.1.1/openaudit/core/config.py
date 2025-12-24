import os
import yaml
from pathlib import Path
from typing import Optional, Dict

class ConfigManager:
    """
    Manages persistent configuration for OpenAuditKit.
    """
    CONFIG_FILE_NAME = ".openaudit_config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to user home directory
            self.config_path = Path.home() / self.CONFIG_FILE_NAME

    def _load_config(self) -> Dict:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_config(self, config: Dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

    def get_api_key(self) -> Optional[str]:
        """
        Retrieves the OpenAI API key from environment variable or config file.
        Priority: Env Var > Config File
        """
        # 1. Check Environment Variable
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key:
            return env_key
            
        # 2. Check Config File
        config = self._load_config()
        return config.get("openai_api_key")

    def set_api_key(self, api_key: str):
        """
        Saves the OpenAI API key to the config file.
        """
        config = self._load_config()
        config["openai_api_key"] = api_key
        self._save_config(config)
