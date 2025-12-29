from pathlib import Path
from typing import Any

import toml


class Config:
    """Configuration management for Git-Miner."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path and isinstance(config_path, (str, Path)) else None
        self._config: dict[str, Any] = {}

        if self.config_path and self.config_path.exists():
            self.load()

    def load(self):
        """Load configuration from file."""
        if not self.config_path:
            raise ValueError("No config path specified")

        with open(self.config_path) as f:
            self._config = toml.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """Save configuration to file."""
        if not self.config_path:
            raise ValueError("No config path specified")

        with open(self.config_path, "w") as f:
            toml.dump(self._config, f)

    @property
    def github_token(self) -> str | None:
        return self.get("github.token")

    @github_token.setter
    def github_token(self, value: str):
        self.set("github.token", value)

    @property
    def output_dir(self) -> str:
        return self.get("output.dir", ".")

    @output_dir.setter
    def output_dir(self, value: str):
        self.set("output.dir", value)

    @property
    def default_format(self) -> str:
        return self.get("output.format", "csv")

    @default_format.setter
    def default_format(self, value: str):
        self.set("output.format", value)

    @property
    def max_retries(self) -> int:
        return self.get("api.max_retries", 3)

    @max_retries.setter
    def max_retries(self, value: int):
        self.set("api.max_retries", value)

    @property
    def timeout(self) -> float:
        return self.get("api.timeout", 30.0)

    @timeout.setter
    def timeout(self, value: float):
        self.set("api.timeout", value)
