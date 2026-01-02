"""Tests for core module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from claude_dev_cli.core import ClaudeClient
from claude_dev_cli.config import Config


class TestClaudeClient:
    """Tests for ClaudeClient class."""
    
    def test_init_no_api_config_raises(self, temp_home: Path) -> None:
        """Test that initializing without API config raises error."""
        config = Config()
        
        with pytest.raises(ValueError, match="No API configuration found"):
            ClaudeClient(config=config)
    
    def test_init_with_explicit_api_config(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test initializing with explicit API config name."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient(api_config_name="client")
            
            assert client.api_config.name == "client"
            assert client.api_config.api_key == "sk-ant-client-key"
            mock_anthropic.assert_called_once_with(api_key="sk-ant-client-key")
    
    def test_init_uses_default_api_config(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test that default API config is used when none specified."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            
            assert client.api_config.name == "personal"
            assert client.api_config.default is True
    
    def test_init_uses_project_profile_api(
        self, project_dir: Path, config_file: Path, 
        mock_anthropic_client: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project profile API config overrides default."""
        monkeypatch.chdir(project_dir)
        
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            
            # Project profile specifies "client" API
            assert client.api_config.name == "client"
    
    def test_call_basic(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test basic non-streaming API call."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt")
            
            assert response == "Test response"
            mock_anthropic_client.messages.create.assert_called_once()
    
    def test_call_with_system_prompt(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test API call with system prompt."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt", system_prompt="You are a test assistant.")
            
            call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
            assert call_kwargs["system"] == "You are a test assistant."
    
    def test_call_with_custom_model(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test API call with custom model."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt", model="claude-3-haiku-20240307")
            
            call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-3-haiku-20240307"
    
    def test_call_with_project_profile_system_prompt(
        self, project_dir: Path, config_file: Path,
        mock_anthropic_client: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project profile system prompt is used."""
        monkeypatch.chdir(project_dir)
        
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt")
            
            call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
            assert call_kwargs["system"] == "You are a Python expert."
    
    def test_call_explicit_system_prompt_overrides_profile(
        self, project_dir: Path, config_file: Path,
        mock_anthropic_client: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that explicit system prompt overrides project profile."""
        monkeypatch.chdir(project_dir)
        
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt", system_prompt="Override prompt")
            
            call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
            assert call_kwargs["system"] == "Override prompt"
    
    def test_call_logs_usage(
        self, config_file: Path, mock_anthropic_client: Mock, temp_config_dir: Path
    ) -> None:
        """Test that API usage is logged."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            response = client.call("test prompt")
            
            # Check usage log was written
            usage_log = temp_config_dir / "usage.jsonl"
            assert usage_log.exists()
            
            with open(usage_log) as f:
                log_entry = json.loads(f.read())
            
            assert log_entry["api_config"] == "personal"
            assert log_entry["model"] == "claude-3-5-sonnet-20241022"
            assert log_entry["input_tokens"] == 100
            assert log_entry["output_tokens"] == 200
            assert "timestamp" in log_entry
            assert "duration_ms" in log_entry
    
    def test_call_streaming(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test streaming API call."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            chunks = list(client.call_streaming("test prompt"))
            
            assert chunks == ["Test ", "streaming ", "response"]
            mock_anthropic_client.messages.stream.assert_called_once()
    
    def test_call_streaming_with_system_prompt(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test streaming call with system prompt."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            chunks = list(client.call_streaming(
                "test prompt", 
                system_prompt="You are a test assistant."
            ))
            
            call_kwargs = mock_anthropic_client.messages.stream.call_args.kwargs
            assert call_kwargs["system"] == "You are a test assistant."
    
    def test_api_routing_hierarchy_explicit_flag(
        self, project_dir: Path, config_file: Path,
        mock_anthropic_client: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test API routing: explicit flag takes highest priority."""
        monkeypatch.chdir(project_dir)
        # Project specifies "client", but we explicitly pass "personal"
        
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient(api_config_name="personal")
            
            assert client.api_config.name == "personal"
    
    def test_api_routing_hierarchy_project_profile(
        self, project_dir: Path, config_file: Path,
        mock_anthropic_client: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test API routing: project profile overrides default."""
        monkeypatch.chdir(project_dir)
        
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            
            # Project profile specifies "client", not default "personal"
            assert client.api_config.name == "client"
    
    def test_api_routing_hierarchy_default(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test API routing: falls back to default when no override."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            
            assert client.api_config.name == "personal"
            assert client.api_config.default is True
    
    def test_default_model_and_tokens(
        self, config_file: Path, mock_anthropic_client: Mock
    ) -> None:
        """Test default model and max_tokens are used."""
        with patch("claude_dev_cli.core.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_anthropic_client
            
            client = ClaudeClient()
            
            assert client.model == "claude-3-5-sonnet-20241022"
            assert client.max_tokens == 4096
