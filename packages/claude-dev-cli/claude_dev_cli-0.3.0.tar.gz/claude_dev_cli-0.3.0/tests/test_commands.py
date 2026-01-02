"""Tests for commands module."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from claude_dev_cli.commands import (
    generate_tests,
    code_review,
    debug_code,
    generate_docs,
    refactor_code,
    git_commit_message,
)


class TestGenerateTests:
    """Tests for generate_tests command."""
    
    def test_generate_tests_reads_file(
        self, tmp_path: Path, sample_python_code: str, config_file: Path,
        mock_anthropic_client: Mock
    ) -> None:
        """Test that generate_tests reads the file."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Generated tests"
            mock_client_class.return_value = mock_client
            
            result = generate_tests(str(test_file))
            
            assert result == "Generated tests"
            mock_client.call.assert_called_once()
            
            # Check that file content was included in prompt
            call_args = mock_client.call.call_args
            assert sample_python_code in call_args[0][0]
    
    def test_generate_tests_uses_correct_system_prompt(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that generate_tests uses testing expert system prompt."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Generated tests"
            mock_client_class.return_value = mock_client
            
            generate_tests(str(test_file))
            
            call_kwargs = mock_client.call.call_args.kwargs
            assert call_kwargs["system_prompt"] == "You are a Python testing expert."
    
    def test_generate_tests_with_api_config(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that generate_tests respects api_config_name."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Generated tests"
            mock_client_class.return_value = mock_client
            
            generate_tests(str(test_file), api_config_name="client")
            
            mock_client_class.assert_called_once_with(api_config_name="client")


class TestCodeReview:
    """Tests for code_review command."""
    
    def test_code_review_reads_file(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that code_review reads the file."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Review results"
            mock_client_class.return_value = mock_client
            
            result = code_review(str(test_file))
            
            assert result == "Review results"
            assert sample_python_code in mock_client.call.call_args[0][0]
    
    def test_code_review_uses_correct_system_prompt(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that code_review uses senior reviewer system prompt."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Review results"
            mock_client_class.return_value = mock_client
            
            code_review(str(test_file))
            
            call_kwargs = mock_client.call.call_args.kwargs
            assert "senior code reviewer" in call_kwargs["system_prompt"]


class TestDebugCode:
    """Tests for debug_code command."""
    
    def test_debug_code_with_file_and_error(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test debug_code with both file and error message."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Debug analysis"
            mock_client_class.return_value = mock_client
            
            result = debug_code(
                file_path=str(test_file),
                error_message="NameError: name 'x' is not defined"
            )
            
            assert result == "Debug analysis"
            call_args = mock_client.call.call_args[0][0]
            assert sample_python_code in call_args
            assert "NameError" in call_args
    
    def test_debug_code_without_file(self, config_file: Path) -> None:
        """Test debug_code with only error message."""
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Debug analysis"
            mock_client_class.return_value = mock_client
            
            result = debug_code(error_message="Some error occurred")
            
            assert result == "Debug analysis"
            call_args = mock_client.call.call_args[0][0]
            assert "Some error occurred" in call_args
    
    def test_debug_code_uses_correct_system_prompt(
        self, config_file: Path
    ) -> None:
        """Test that debug_code uses debugging expert system prompt."""
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Debug analysis"
            mock_client_class.return_value = mock_client
            
            debug_code(error_message="Error")
            
            call_kwargs = mock_client.call.call_args.kwargs
            assert "debugging expert" in call_kwargs["system_prompt"]


class TestGenerateDocs:
    """Tests for generate_docs command."""
    
    def test_generate_docs_reads_file(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that generate_docs reads the file."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Generated docs"
            mock_client_class.return_value = mock_client
            
            result = generate_docs(str(test_file))
            
            assert result == "Generated docs"
            assert sample_python_code in mock_client.call.call_args[0][0]


class TestRefactorCode:
    """Tests for refactor_code command."""
    
    def test_refactor_code_reads_file(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that refactor_code reads the file."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Refactored code"
            mock_client_class.return_value = mock_client
            
            result = refactor_code(str(test_file))
            
            assert result == "Refactored code"
            assert sample_python_code in mock_client.call.call_args[0][0]
    
    def test_refactor_code_uses_correct_system_prompt(
        self, tmp_path: Path, sample_python_code: str, config_file: Path
    ) -> None:
        """Test that refactor_code uses refactoring expert system prompt."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_python_code)
        
        with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
            mock_client = Mock()
            mock_client.call.return_value = "Refactored code"
            mock_client_class.return_value = mock_client
            
            refactor_code(str(test_file))
            
            call_kwargs = mock_client.call.call_args.kwargs
            assert "refactoring expert" in call_kwargs["system_prompt"]


class TestGitCommitMessage:
    """Tests for git_commit_message command."""
    
    def test_git_commit_message_calls_git_diff(
        self, sample_git_diff: str, config_file: Path
    ) -> None:
        """Test that git_commit_message calls git diff --cached."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=sample_git_diff)
            
            with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
                mock_client = Mock()
                mock_client.call.return_value = "feat: add new feature"
                mock_client_class.return_value = mock_client
                
                result = git_commit_message()
                
                assert result == "feat: add new feature"
                mock_run.assert_called_once()
                
                # Verify git command
                call_args = mock_run.call_args[0][0]
                assert call_args == ["git", "--no-pager", "diff", "--cached"]
    
    def test_git_commit_message_includes_diff_in_prompt(
        self, sample_git_diff: str, config_file: Path
    ) -> None:
        """Test that git diff is included in the prompt."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=sample_git_diff)
            
            with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
                mock_client = Mock()
                mock_client.call.return_value = "feat: add new feature"
                mock_client_class.return_value = mock_client
                
                git_commit_message()
                
                call_args = mock_client.call.call_args[0][0]
                assert sample_git_diff in call_args
    
    def test_git_commit_message_no_staged_changes(
        self, config_file: Path
    ) -> None:
        """Test that error is raised when no staged changes."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="")
            
            with pytest.raises(ValueError, match="No staged changes"):
                git_commit_message()
    
    def test_git_commit_message_git_not_found(
        self, config_file: Path
    ) -> None:
        """Test that error is raised when git is not found."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            with pytest.raises(ValueError, match="Git is not installed"):
                git_commit_message()
    
    def test_git_commit_message_git_error(
        self, config_file: Path
    ) -> None:
        """Test that error is raised when git command fails."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            with pytest.raises(ValueError, match="Git command failed"):
                git_commit_message()
    
    def test_git_commit_message_uses_correct_system_prompt(
        self, sample_git_diff: str, config_file: Path
    ) -> None:
        """Test that git_commit_message uses git expert system prompt."""
        with patch("claude_dev_cli.commands.subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=sample_git_diff)
            
            with patch("claude_dev_cli.commands.ClaudeClient") as mock_client_class:
                mock_client = Mock()
                mock_client.call.return_value = "feat: add new feature"
                mock_client_class.return_value = mock_client
                
                git_commit_message()
                
                call_kwargs = mock_client.call.call_args.kwargs
                assert "git commit message expert" in call_kwargs["system_prompt"]
