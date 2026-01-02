"""Configuration management for Claude Dev CLI."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """Configuration for a Claude API key."""
    
    name: str
    api_key: str
    description: Optional[str] = None
    default: bool = False


class ProjectProfile(BaseModel):
    """Project-specific configuration."""
    
    name: str
    api_config: str  # Name of the API config to use
    system_prompt: Optional[str] = None
    allowed_commands: List[str] = Field(default_factory=lambda: ["all"])


class Config:
    """Manages configuration for Claude Dev CLI."""
    
    CONFIG_DIR = Path.home() / ".claude-dev-cli"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    USAGE_LOG = CONFIG_DIR / "usage.jsonl"
    
    def __init__(self) -> None:
        """Initialize configuration."""
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.usage_log = self.USAGE_LOG
        self._ensure_config_dir()
        self._data: Dict = self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.usage_log.touch(exist_ok=True)
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            default_config = {
                "api_configs": [],
                "project_profiles": [],
                "default_model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
            }
            self._save_config(default_config)
            return default_config
        
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def _save_config(self, data: Optional[Dict] = None) -> None:
        """Save configuration to file."""
        if data is None:
            data = self._data
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_api_config(
        self,
        name: str,
        api_key: Optional[str] = None,
        description: Optional[str] = None,
        make_default: bool = False
    ) -> None:
        """Add a new API configuration."""
        # Get API key from env if not provided
        if api_key is None:
            env_var = f"{name.upper()}_ANTHROPIC_API_KEY"
            api_key = os.environ.get(env_var)
            if not api_key:
                raise ValueError(
                    f"API key not provided and {env_var} environment variable not set"
                )
        
        # Check if name already exists
        api_configs = self._data.get("api_configs", [])
        for config in api_configs:
            if config["name"] == name:
                raise ValueError(f"API config with name '{name}' already exists")
        
        # If this is the first config or make_default is True, set as default
        if make_default or not api_configs:
            for config in api_configs:
                config["default"] = False
        
        api_config = APIConfig(
            name=name,
            api_key=api_key,
            description=description,
            default=make_default or not api_configs
        )
        
        api_configs.append(api_config.model_dump())
        self._data["api_configs"] = api_configs
        self._save_config()
    
    def get_api_config(self, name: Optional[str] = None) -> Optional[APIConfig]:
        """Get API configuration by name or default."""
        api_configs = self._data.get("api_configs", [])
        
        if name:
            for config in api_configs:
                if config["name"] == name:
                    return APIConfig(**config)
        else:
            # Return default
            for config in api_configs:
                if config.get("default", False):
                    return APIConfig(**config)
        
        return None
    
    def list_api_configs(self) -> List[APIConfig]:
        """List all API configurations."""
        return [APIConfig(**c) for c in self._data.get("api_configs", [])]
    
    def add_project_profile(
        self,
        name: str,
        api_config: str,
        system_prompt: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None
    ) -> None:
        """Add a project profile."""
        profiles = self._data.get("project_profiles", [])
        
        profile = ProjectProfile(
            name=name,
            api_config=api_config,
            system_prompt=system_prompt,
            allowed_commands=allowed_commands or ["all"]
        )
        
        profiles.append(profile.model_dump())
        self._data["project_profiles"] = profiles
        self._save_config()
    
    def get_project_profile(self, cwd: Optional[Path] = None) -> Optional[ProjectProfile]:
        """Get project profile for current directory."""
        if cwd is None:
            cwd = Path.cwd()
        
        # Check for .claude-dev-cli file in current or parent directories
        current = cwd
        while current != current.parent:
            config_file = current / ".claude-dev-cli"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return ProjectProfile(**data)
            current = current.parent
        
        return None
    
    def get_model(self) -> str:
        """Get default model."""
        return self._data.get("default_model", "claude-3-5-sonnet-20241022")
    
    def get_max_tokens(self) -> int:
        """Get default max tokens."""
        return self._data.get("max_tokens", 4096)
