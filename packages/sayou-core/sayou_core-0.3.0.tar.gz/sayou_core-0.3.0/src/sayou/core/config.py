import os
from typing import Any, Dict


class SayouConfig:
    """
    [Core] Universal Configuration Manager.
    Doesn't know about specific modules (Brain, Connector, etc.),
    just manages key-value pairs and env vars.
    """

    def __init__(self, config_dict: Dict[str, Any] = None):
        self._config = config_dict or {}

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Retrieves a config value.
        Usage:
            cfg.get("connector") -> Returns whole dict
            cfg.get("connector", "timeout") -> Returns value
        """
        # 1. Section lookup
        section_data = self._config.get(section, {})

        # If key is not provided, return the whole section
        if key is None:
            return section_data

        # 2. Key lookup in section
        if key in section_data:
            return section_data[key]

        # 3. Environment Variable Fallback
        # Pattern: SAYOU_{SECTION}_{KEY} (e.g., SAYOU_CONNECTOR_TIMEOUT)
        env_var = f"SAYOU_{section.upper()}_{key.upper()}"
        return os.environ.get(env_var, default)
