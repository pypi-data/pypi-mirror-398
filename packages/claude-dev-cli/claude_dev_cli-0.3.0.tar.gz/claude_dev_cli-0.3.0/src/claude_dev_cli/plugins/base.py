"""Base plugin interface for Claude Dev CLI."""

from abc import ABC, abstractmethod
from typing import Optional
import click


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, name: str, version: str, description: str = ""):
        """Initialize plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
            description: Plugin description
        """
        self.name = name
        self.version = version
        self.description = description
    
    @abstractmethod
    def register_commands(self, cli: click.Group) -> None:
        """Register plugin commands with the CLI.
        
        Args:
            cli: Click group to register commands to
        """
        pass
    
    def before_apply(self, original: str, proposed: str) -> Optional[str]:
        """Hook called before applying changes.
        
        Args:
            original: Original content
            proposed: Proposed changes
            
        Returns:
            Modified proposed content or None to keep original
        """
        return None
    
    def after_apply(self, result: str) -> Optional[str]:
        """Hook called after applying changes.
        
        Args:
            result: Result after changes applied
            
        Returns:
            Modified result or None to keep original
        """
        return None
