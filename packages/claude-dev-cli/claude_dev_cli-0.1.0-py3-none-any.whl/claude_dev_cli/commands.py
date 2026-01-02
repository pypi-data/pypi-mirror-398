"""Developer-specific commands for Claude Dev CLI."""

import subprocess
from pathlib import Path
from typing import Optional

from claude_dev_cli.core import ClaudeClient
from claude_dev_cli.templates import (
    TEST_GENERATION_PROMPT,
    CODE_REVIEW_PROMPT,
    DEBUG_PROMPT,
    DOCS_GENERATION_PROMPT,
    REFACTOR_PROMPT,
    GIT_COMMIT_PROMPT,
)


def generate_tests(file_path: str, api_config_name: Optional[str] = None) -> str:
    """Generate pytest tests for a Python file."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    prompt = TEST_GENERATION_PROMPT.format(
        filename=Path(file_path).name,
        code=code
    )
    
    client = ClaudeClient(api_config_name=api_config_name)
    return client.call(prompt, system_prompt="You are a Python testing expert.")


def code_review(file_path: str, api_config_name: Optional[str] = None) -> str:
    """Review code for bugs and improvements."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    prompt = CODE_REVIEW_PROMPT.format(
        filename=Path(file_path).name,
        code=code
    )
    
    client = ClaudeClient(api_config_name=api_config_name)
    return client.call(
        prompt,
        system_prompt="You are a senior code reviewer focused on security, performance, and best practices."
    )


def debug_code(
    file_path: Optional[str] = None,
    error_message: Optional[str] = None,
    api_config_name: Optional[str] = None
) -> str:
    """Debug code and analyze errors."""
    code = ""
    if file_path:
        with open(file_path, 'r') as f:
            code = f.read()
    
    prompt = DEBUG_PROMPT.format(
        filename=Path(file_path).name if file_path else "unknown",
        code=code,
        error=error_message or "No error message provided"
    )
    
    client = ClaudeClient(api_config_name=api_config_name)
    return client.call(
        prompt,
        system_prompt="You are a debugging expert. Analyze errors and provide fixes."
    )


def generate_docs(file_path: str, api_config_name: Optional[str] = None) -> str:
    """Generate documentation for a Python file."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    prompt = DOCS_GENERATION_PROMPT.format(
        filename=Path(file_path).name,
        code=code
    )
    
    client = ClaudeClient(api_config_name=api_config_name)
    return client.call(
        prompt,
        system_prompt="You are a technical documentation expert."
    )


def refactor_code(file_path: str, api_config_name: Optional[str] = None) -> str:
    """Suggest refactoring improvements."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    prompt = REFACTOR_PROMPT.format(
        filename=Path(file_path).name,
        code=code
    )
    
    client = ClaudeClient(api_config_name=api_config_name)
    return client.call(
        prompt,
        system_prompt="You are a refactoring expert focused on code maintainability and readability."
    )


def git_commit_message(api_config_name: Optional[str] = None) -> str:
    """Generate commit message from staged changes."""
    try:
        # Get staged changes
        result = subprocess.run(
            ['git', '--no-pager', 'diff', '--cached'],
            capture_output=True,
            text=True,
            check=True
        )
        diff = result.stdout
        
        if not diff:
            raise ValueError("No staged changes found. Run 'git add' first.")
        
        prompt = GIT_COMMIT_PROMPT.format(diff=diff)
        
        client = ClaudeClient(api_config_name=api_config_name)
        return client.call(
            prompt,
            system_prompt="You are a git commit message expert. Write clear, conventional commit messages."
        )
    
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git command failed: {e}")
    except FileNotFoundError:
        raise ValueError("Git is not installed or not in PATH")
