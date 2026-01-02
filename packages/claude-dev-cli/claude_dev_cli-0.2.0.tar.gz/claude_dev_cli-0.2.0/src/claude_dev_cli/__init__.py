"""
Claude Dev CLI - A powerful CLI tool for developers using Claude AI.

Features:
- Multi-API key management and routing
- Test generation for Python projects
- Code review and analysis
- Usage tracking and cost monitoring
- Interactive and single-shot modes
"""

__version__ = "0.2.0"
__author__ = "Julio"
__license__ = "MIT"

from claude_dev_cli.core import ClaudeClient
from claude_dev_cli.config import Config

__all__ = ["ClaudeClient", "Config", "__version__"]
