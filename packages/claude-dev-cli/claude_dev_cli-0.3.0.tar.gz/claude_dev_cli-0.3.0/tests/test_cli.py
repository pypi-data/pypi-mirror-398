"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from claude_dev_cli.cli import main


class TestConfigCommands:
    """Tests for config commands."""
    
    def test_config_add_with_api_key(
        self, cli_runner: CliRunner, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adding API config with explicit key."""
        result = cli_runner.invoke(
            main,
            ["config", "add", "test", "--api-key", "sk-ant-test", "--default"]
        )
        
        assert result.exit_code == 0
        assert "Added API config: test" in result.output
    
    def test_config_add_from_env(
        self, cli_runner: CliRunner, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adding API config from environment variable."""
        monkeypatch.setenv("TEST_ANTHROPIC_API_KEY", "sk-ant-env")
        
        result = cli_runner.invoke(main, ["config", "add", "test"])
        
        assert result.exit_code == 0
        assert "Added API config: test" in result.output
    
    def test_config_list(
        self, cli_runner: CliRunner, config_file: Path
    ) -> None:
        """Test listing API configurations."""
        result = cli_runner.invoke(main, ["config", "list"])
        
        assert result.exit_code == 0
        assert "personal" in result.output
        assert "client" in result.output
    
    def test_config_list_empty(
        self, cli_runner: CliRunner, temp_home: Path
    ) -> None:
        """Test listing when no configs exist."""
        result = cli_runner.invoke(main, ["config", "list"])
        
        assert result.exit_code == 0
        assert "No API configurations found" in result.output


class TestAskCommand:
    """Tests for ask command."""
    
    def test_ask_with_prompt(
        self, cli_runner: CliRunner, config_file: Path
    ) -> None:
        """Test ask command with prompt."""
        with patch("claude_dev_cli.cli.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call_streaming.return_value = iter(["Test", " response"])
            mock_client_class.return_value = mock_client
            
            result = cli_runner.invoke(main, ["ask", "test prompt"])
            
            assert result.exit_code == 0
            mock_client.call_streaming.assert_called_once()
    
    def test_ask_with_file(
        self, cli_runner: CliRunner, config_file: Path, tmp_path: Path
    ) -> None:
        """Test ask command with file context."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")
        
        with patch("claude_dev_cli.cli.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call_streaming.return_value = iter(["Response"])
            mock_client_class.return_value = mock_client
            
            result = cli_runner.invoke(
                main, ["ask", "-f", str(test_file), "test prompt"]
            )
            
            assert result.exit_code == 0
            call_args = mock_client.call_streaming.call_args[0][0]
            assert "file content" in call_args
    
    def test_ask_with_api_flag(
        self, cli_runner: CliRunner, config_file: Path
    ) -> None:
        """Test ask command with --api flag."""
        with patch("claude_dev_cli.cli.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call_streaming.return_value = iter(["Response"])
            mock_client_class.return_value = mock_client
            
            result = cli_runner.invoke(main, ["ask", "-a", "client", "test"])
            
            assert result.exit_code == 0
            mock_client_class.assert_called_once_with(api_config_name="client")


class TestGenerateCommands:
    """Tests for generate commands."""
    
    def test_generate_tests(
        self, cli_runner: CliRunner, config_file: Path, tmp_path: Path
    ) -> None:
        """Test generate tests command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")
        
        with patch("claude_dev_cli.cli.generate_tests") as mock_gen:
            mock_gen.return_value = "Generated tests"
            
            result = cli_runner.invoke(main, ["generate", "tests", str(test_file)])
            
            assert result.exit_code == 0
            mock_gen.assert_called_once()
    
    def test_generate_tests_with_output(
        self, cli_runner: CliRunner, config_file: Path, tmp_path: Path
    ) -> None:
        """Test generate tests with output file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")
        output_file = tmp_path / "test_output.py"
        
        with patch("claude_dev_cli.cli.generate_tests") as mock_gen:
            mock_gen.return_value = "Generated tests"
            
            result = cli_runner.invoke(
                main, ["generate", "tests", str(test_file), "-o", str(output_file)]
            )
            
            assert result.exit_code == 0
            assert output_file.exists()
            assert output_file.read_text() == "Generated tests"


class TestReviewCommand:
    """Tests for review command."""
    
    def test_review(
        self, cli_runner: CliRunner, config_file: Path, tmp_path: Path
    ) -> None:
        """Test review command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")
        
        with patch("claude_dev_cli.cli.code_review") as mock_review:
            mock_review.return_value = "# Review\nLooks good"
            
            result = cli_runner.invoke(main, ["review", str(test_file)])
            
            assert result.exit_code == 0
            mock_review.assert_called_once()


class TestDebugCommand:
    """Tests for debug command."""
    
    def test_debug_with_file_and_error(
        self, cli_runner: CliRunner, config_file: Path, tmp_path: Path
    ) -> None:
        """Test debug command with file and error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")
        
        with patch("claude_dev_cli.cli.debug_code") as mock_debug:
            mock_debug.return_value = "Debug analysis"
            
            result = cli_runner.invoke(
                main, ["debug", "-f", str(test_file), "-e", "NameError"]
            )
            
            assert result.exit_code == 0
            mock_debug.assert_called_once()


class TestGitCommands:
    """Tests for git commands."""
    
    def test_git_commit(
        self, cli_runner: CliRunner, config_file: Path
    ) -> None:
        """Test git commit command."""
        with patch("claude_dev_cli.cli.git_commit_message") as mock_git:
            mock_git.return_value = "feat: add new feature"
            
            result = cli_runner.invoke(main, ["git", "commit"])
            
            assert result.exit_code == 0
            assert "feat: add new feature" in result.output
            mock_git.assert_called_once()


class TestUsageCommand:
    """Tests for usage command."""
    
    def test_usage(
        self, cli_runner: CliRunner, usage_log_file: Path
    ) -> None:
        """Test usage command."""
        with patch("claude_dev_cli.cli.UsageTracker") as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker
            
            result = cli_runner.invoke(main, ["usage"])
            
            assert result.exit_code == 0
            mock_tracker.display_usage.assert_called_once()
    
    def test_usage_with_filters(
        self, cli_runner: CliRunner, usage_log_file: Path
    ) -> None:
        """Test usage command with filters."""
        with patch("claude_dev_cli.cli.UsageTracker") as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker
            
            result = cli_runner.invoke(main, ["usage", "--days", "7", "--api", "personal"])
            
            assert result.exit_code == 0
            call_kwargs = mock_tracker.display_usage.call_args.kwargs
            assert call_kwargs["days"] == 7
            assert call_kwargs["api_config"] == "personal"


class TestToonCommands:
    """Tests for toon commands."""
    
    def test_toon_info_available(
        self, cli_runner: CliRunner
    ) -> None:
        """Test toon info when TOON is available."""
        with patch("claude_dev_cli.cli.toon_utils.is_toon_available") as mock_available:
            mock_available.return_value = True
            
            result = cli_runner.invoke(main, ["toon", "info"])
            
            assert result.exit_code == 0
            assert "TOON format support is installed" in result.output
    
    def test_toon_info_not_available(
        self, cli_runner: CliRunner
    ) -> None:
        """Test toon info when TOON is not available."""
        with patch("claude_dev_cli.cli.toon_utils.is_toon_available") as mock_available:
            mock_available.return_value = False
            
            result = cli_runner.invoke(main, ["toon", "info"])
            
            assert result.exit_code == 0
            assert "TOON format support not installed" in result.output
