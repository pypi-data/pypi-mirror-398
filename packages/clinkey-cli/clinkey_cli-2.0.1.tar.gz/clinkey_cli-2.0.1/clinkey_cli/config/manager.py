"""Configuration manager for Clinkey settings.

Handles loading, merging, and accessing configuration from:
1. Default values (lowest priority)
2. Config file (~/.clinkey/config.toml)
3. Environment variables (CLINKEY_*)
4. Command-line flags (highest priority, handled by CLI)
"""

import os
import pathlib
from typing import Any

# Default configuration structure
DEFAULT_CONFIG = {
    "general": {
        "default_length": 16,
        "default_type": "normal",
        "interactive_mode": "rich",
        "auto_analyze": False,
        "clipboard_timeout": 30,
    },
    "security": {
        "min_password_length": 16,
        "max_password_length": 128,
        "min_strength_score": 0,
        "check_breaches": False,
        "offline_breach_db": "~/.clinkey/breaches.db",
    },
    "vault": {
        "database_path": "~/.clinkey/vault.db",
        "backup_path": "~/.clinkey/backups/",
        "auto_backup": True,
        "backup_interval": 7,
        "lock_timeout": 300,
        "clipboard_clear": True,
    },
    "generators": {
        "syllable": {
            "default_language": "english",
            "complexity": "mixed",
        },
        "passphrase": {
            "default_wordlist": "eff_large",
            "default_word_count": 4,
            "separator": "-",
            "capitalize": True,
        },
        "pattern": {
            "saved_templates": [],
        },
    },
    "compliance": {
        "enforce_nist": False,
        "enforce_owasp": False,
        "custom_policies": [],
    },
    "ui": {
        "tui": {
            "theme": "dark",
            "vim_mode": True,
            "show_help_bar": True,
        },
        "rich": {
            "color_scheme": "default",
        },
    },
}


class ConfigManager:
    """Manage Clinkey configuration.

    Loads configuration from file and provides access to settings with
    fallback to defaults. Supports nested key access via dot notation.

    Parameters
    ----------
    config_path : pathlib.Path | None
        Path to configuration file. If None, uses ~/.clinkey/config.toml.

    Attributes
    ----------
    config_path : pathlib.Path
        Path to configuration file.
    config : dict
        Loaded configuration merged with defaults.
    """

    def __init__(self, config_path: pathlib.Path | None = None):
        """Initialize configuration manager.

        Parameters
        ----------
        config_path : pathlib.Path | None, default None
            Path to config file. Defaults to ~/.clinkey/config.toml.
        """
        if config_path is None:
            config_path = pathlib.Path.home() / ".clinkey" / "config.toml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file or use defaults.

        Returns
        -------
        dict
            Configuration dictionary.
        """
        # For Phase 1, just return defaults
        # Phase 2+ will implement TOML parsing
        return DEFAULT_CONFIG.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Parameters
        ----------
        key : str
            Configuration key in dot notation (e.g., "general.default_length").
        default : Any, default None
            Default value if key not found.

        Returns
        -------
        Any
            Configuration value or default.

        Examples
        --------
        >>> manager = ConfigManager()
        >>> manager.get("general.default_length")
        16
        >>> manager.get("nonexistent.key", default=42)
        42
        """
        parts = key.split(".")
        value = self.config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Parameters
        ----------
        key : str
            Configuration key in dot notation.
        value : Any
            Value to set.

        Examples
        --------
        >>> manager = ConfigManager()
        >>> manager.set("general.default_length", 20)
        >>> manager.get("general.default_length")
        20
        """
        parts = key.split(".")
        config = self.config

        # Navigate to parent
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]

        # Set value
        config[parts[-1]] = value

    def save(self) -> None:
        """Save configuration to file.

        For Phase 1, this is a no-op. Phase 2+ will implement TOML writing.
        """
        # Phase 1: no-op
        # Phase 2+: write TOML file
        pass

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = DEFAULT_CONFIG.copy()
