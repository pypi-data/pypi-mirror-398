import os
from typing import Any, Dict


class SayouConfig:
    """
    Central configuration manager for Sayou Fabric.
    Facilitates configuration injection from Dict or Environment Variables.
    """

    def __init__(self, config_dict: Dict[str, Any] = None):
        self._config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        Priority: Dict -> Environment Variable -> Default
        """
        # 1. Direct dictionary lookup
        if key in self._config:
            return self._config[key]

        # 2. Environment variable lookup (e.g., 'openai_api_key' -> 'OPENAI_API_KEY')
        env_key = key.upper()
        return os.environ.get(env_key, default)

    @property
    def connector(self) -> Dict[str, Any]:
        return self.get("connector", {})

    @property
    def document(self) -> Dict[str, Any]:
        return self.get("document", {})

    @property
    def refinery(self) -> Dict[str, Any]:
        return self.get("refinery", {})

    @property
    def chunking(self) -> Dict[str, Any]:
        return self.get("chunking", {})

    @property
    def wrapper(self) -> Dict[str, Any]:
        return self.get("wrapper", {})

    @property
    def assembler(self) -> Dict[str, Any]:
        return self.get("assembler", {})

    @property
    def loader(self) -> Dict[str, Any]:
        return self.get("loader", {})
