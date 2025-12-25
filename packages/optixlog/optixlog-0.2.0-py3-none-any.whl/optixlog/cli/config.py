"""
Configuration Management for OptixLog CLI

Handles reading/writing config from ~/.config/optixlog/config.toml
with environment variable overrides.

Priority: CLI args > env vars > config file > defaults
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# TOML parsing - use tomllib (Python 3.11+) or tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


# Default values
DEFAULT_API_URL = "https://optixlog.com"
DEFAULT_PROJECT = "dev"

# Config file location
CONFIG_DIR = Path.home() / ".config" / "optixlog"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Environment variable names
ENV_API_KEY = "OPTIX_API_KEY"
ENV_API_URL = "OPTIX_API_URL"
ENV_PROJECT = "OPTIX_PROJECT"


class OptixConfig:
    """Configuration manager for OptixLog CLI."""
    
    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            self._config = {"default": {}}
            return
        
        if tomllib is None:
            # Fallback: try to parse simple TOML manually
            self._config = self._parse_simple_toml(CONFIG_FILE)
            return
        
        try:
            with open(CONFIG_FILE, "rb") as f:
                self._config = tomllib.load(f)
        except Exception:
            self._config = {"default": {}}
    
    def _parse_simple_toml(self, path: Path) -> Dict[str, Any]:
        """Simple TOML parser for basic key-value configs."""
        config: Dict[str, Any] = {"default": {}}
        current_section = "default"
        
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line[1:-1]
                        if current_section not in config:
                            config[current_section] = {}
                    elif "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if current_section not in config:
                            config[current_section] = {}
                        config[current_section][key] = value
        except Exception:
            pass
        
        return config
    
    def _save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        lines = []
        for section, values in self._config.items():
            lines.append(f"[{section}]")
            for key, value in values.items():
                if isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    lines.append(f'{key} = {str(value).lower()}')
                else:
                    lines.append(f'{key} = {value}')
            lines.append("")
        
        with open(CONFIG_FILE, "w") as f:
            f.write("\n".join(lines))
    
    def get(self, key: str, default: Optional[str] = None, section: str = "default") -> Optional[str]:
        """
        Get a config value with environment variable override.
        
        Priority: env var > config file > default
        """
        # Check environment variable first
        env_map = {
            "api_key": ENV_API_KEY,
            "api_url": ENV_API_URL,
            "project": ENV_PROJECT,
        }
        
        if key in env_map:
            env_value = os.environ.get(env_map[key])
            if env_value:
                return env_value
        
        # Check config file
        if section in self._config and key in self._config[section]:
            return self._config[section][key]
        
        return default
    
    def set(self, key: str, value: str, section: str = "default") -> None:
        """Set a config value and save to file."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self._save()
    
    def delete(self, key: str, section: str = "default") -> bool:
        """Delete a config value and save to file."""
        if section in self._config and key in self._config[section]:
            del self._config[section][key]
            self._save()
            return True
        return False
    
    def list_all(self, section: str = "default") -> Dict[str, Any]:
        """List all config values in a section."""
        return self._config.get(section, {}).copy()
    
    def get_all_sections(self) -> Dict[str, Dict[str, Any]]:
        """Get all config sections."""
        return self._config.copy()
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key (env var takes precedence)."""
        return self.get("api_key")
    
    @property
    def api_url(self) -> str:
        """Get API URL (env var takes precedence)."""
        return self.get("api_url", DEFAULT_API_URL) or DEFAULT_API_URL
    
    @property
    def project(self) -> str:
        """Get default project (env var takes precedence)."""
        return self.get("project", DEFAULT_PROJECT) or DEFAULT_PROJECT
    
    @property
    def config_path(self) -> Path:
        """Get config file path."""
        return CONFIG_FILE
    
    def exists(self) -> bool:
        """Check if config file exists."""
        return CONFIG_FILE.exists()


# Global config instance
_config: Optional[OptixConfig] = None


def get_config() -> OptixConfig:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = OptixConfig()
    return _config


def reload_config() -> OptixConfig:
    """Reload config from disk."""
    global _config
    _config = OptixConfig()
    return _config

