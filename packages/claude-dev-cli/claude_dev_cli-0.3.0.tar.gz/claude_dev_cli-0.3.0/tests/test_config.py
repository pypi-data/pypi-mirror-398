"""Tests for config module."""

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest

from claude_dev_cli.config import Config, APIConfig, ProjectProfile


class TestAPIConfig:
    """Tests for APIConfig model."""
    
    def test_create_api_config(self) -> None:
        """Test creating an API configuration."""
        config = APIConfig(
            name="test",
            api_key="sk-ant-test",
            description="Test API",
            default=True
        )
        
        assert config.name == "test"
        assert config.api_key == "sk-ant-test"
        assert config.description == "Test API"
        assert config.default is True
    
    def test_api_config_defaults(self) -> None:
        """Test API config default values."""
        config = APIConfig(name="test", api_key="sk-ant-test")
        
        assert config.description is None
        assert config.default is False


class TestProjectProfile:
    """Tests for ProjectProfile model."""
    
    def test_create_project_profile(self) -> None:
        """Test creating a project profile."""
        profile = ProjectProfile(
            name="Test Project",
            api_config="client",
            system_prompt="You are a test assistant.",
            allowed_commands=["generate", "review"]
        )
        
        assert profile.name == "Test Project"
        assert profile.api_config == "client"
        assert profile.system_prompt == "You are a test assistant."
        assert profile.allowed_commands == ["generate", "review"]
    
    def test_project_profile_defaults(self) -> None:
        """Test project profile default values."""
        profile = ProjectProfile(name="Test", api_config="personal")
        
        assert profile.system_prompt is None
        assert profile.allowed_commands == ["all"]


class TestConfig:
    """Tests for Config class."""
    
    def test_init_creates_config_dir(self, temp_home: Path) -> None:
        """Test that Config.__init__ creates config directory."""
        config = Config()
        
        assert config.config_dir.exists()
        assert config.usage_log.exists()
    
    def test_init_creates_default_config(self, temp_home: Path) -> None:
        """Test that Config.__init__ creates default config file."""
        config = Config()
        
        assert config.config_file.exists()
        
        with open(config.config_file) as f:
            data = json.load(f)
        
        assert data["api_configs"] == []
        assert data["default_model"] == "claude-3-5-sonnet-20241022"
        assert data["max_tokens"] == 4096
    
    def test_load_existing_config(self, config_file: Path) -> None:
        """Test loading an existing config file."""
        config = Config()
        
        assert len(config.list_api_configs()) == 2
        assert config.get_model() == "claude-3-5-sonnet-20241022"
        assert config.get_max_tokens() == 4096
    
    def test_add_api_config(self, temp_home: Path) -> None:
        """Test adding a new API configuration."""
        config = Config()
        
        config.add_api_config(
            name="test",
            api_key="sk-ant-test-key",
            description="Test API",
            make_default=True
        )
        
        api_config = config.get_api_config("test")
        assert api_config is not None
        assert api_config.name == "test"
        assert api_config.api_key == "sk-ant-test-key"
        assert api_config.description == "Test API"
        assert api_config.default is True
    
    def test_add_api_config_from_env(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adding API config from environment variable."""
        monkeypatch.setenv("TEST_ANTHROPIC_API_KEY", "sk-ant-env-key")
        
        config = Config()
        config.add_api_config(name="test", description="From env")
        
        api_config = config.get_api_config("test")
        assert api_config is not None
        assert api_config.api_key == "sk-ant-env-key"
    
    def test_add_api_config_no_key_raises(self, temp_home: Path) -> None:
        """Test that adding API config without key raises error."""
        config = Config()
        
        with pytest.raises(ValueError, match="API key not provided"):
            config.add_api_config(name="test")
    
    def test_add_duplicate_name_raises(self, config_file: Path) -> None:
        """Test that adding duplicate API config name raises error."""
        config = Config()
        
        with pytest.raises(ValueError, match="already exists"):
            config.add_api_config(name="personal", api_key="sk-ant-duplicate")
    
    def test_first_config_is_default(self, temp_home: Path) -> None:
        """Test that first API config is set as default."""
        config = Config()
        
        config.add_api_config(name="first", api_key="sk-ant-first")
        
        api_config = config.get_api_config("first")
        assert api_config is not None
        assert api_config.default is True
    
    def test_make_default_unsets_others(self, config_file: Path) -> None:
        """Test that setting new default unsets other defaults."""
        config = Config()
        
        # Personal is default initially
        personal = config.get_api_config("personal")
        assert personal is not None
        assert personal.default is True
        
        # Add new default
        config.add_api_config(
            name="new_default", api_key="sk-ant-new", make_default=True
        )
        
        # Reload config
        config = Config()
        personal = config.get_api_config("personal")
        new_default = config.get_api_config("new_default")
        
        assert personal is not None
        assert personal.default is False
        assert new_default is not None
        assert new_default.default is True
    
    def test_get_api_config_by_name(self, config_file: Path) -> None:
        """Test getting API config by name."""
        config = Config()
        
        api_config = config.get_api_config("client")
        assert api_config is not None
        assert api_config.name == "client"
        assert api_config.api_key == "sk-ant-client-key"
    
    def test_get_api_config_default(self, config_file: Path) -> None:
        """Test getting default API config."""
        config = Config()
        
        api_config = config.get_api_config()
        assert api_config is not None
        assert api_config.name == "personal"
        assert api_config.default is True
    
    def test_get_api_config_nonexistent(self, config_file: Path) -> None:
        """Test getting nonexistent API config returns None."""
        config = Config()
        
        api_config = config.get_api_config("nonexistent")
        assert api_config is None
    
    def test_list_api_configs(self, config_file: Path) -> None:
        """Test listing all API configurations."""
        config = Config()
        
        configs = config.list_api_configs()
        assert len(configs) == 2
        assert configs[0].name == "personal"
        assert configs[1].name == "client"
    
    def test_get_project_profile_in_current_dir(
        self, project_dir: Path, config_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting project profile from current directory."""
        monkeypatch.chdir(project_dir)
        
        config = Config()
        profile = config.get_project_profile()
        
        assert profile is not None
        assert profile.name == "Test Project"
        assert profile.api_config == "client"
        assert profile.system_prompt == "You are a Python expert."
    
    def test_get_project_profile_in_parent_dir(
        self, project_dir: Path, config_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting project profile from parent directory."""
        subdir = project_dir / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        
        config = Config()
        profile = config.get_project_profile()
        
        assert profile is not None
        assert profile.name == "Test Project"
        assert profile.api_config == "client"
    
    def test_get_project_profile_not_found(
        self, temp_home: Path, config_file: Path
    ) -> None:
        """Test getting project profile when none exists."""
        config = Config()
        profile = config.get_project_profile()
        
        assert profile is None
    
    def test_get_model(self, config_file: Path) -> None:
        """Test getting default model."""
        config = Config()
        
        assert config.get_model() == "claude-3-5-sonnet-20241022"
    
    def test_get_max_tokens(self, config_file: Path) -> None:
        """Test getting default max tokens."""
        config = Config()
        
        assert config.get_max_tokens() == 4096
