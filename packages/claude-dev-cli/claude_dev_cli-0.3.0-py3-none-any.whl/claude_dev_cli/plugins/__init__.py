"""Plugin system for Claude Dev CLI."""

from typing import List
from pathlib import Path
import importlib
import importlib.util

from .base import Plugin


def discover_plugins() -> List[Plugin]:
    """Discover and load all plugins from the plugins directory.
    
    Returns:
        List of loaded plugin instances
    """
    plugins = []
    plugin_dir = Path(__file__).parent
    
    # Look for plugin directories (those with plugin.py)
    for item in plugin_dir.iterdir():
        if item.is_dir() and (item / "plugin.py").exists() and item.name != "__pycache__":
            try:
                # Use proper import instead of spec loading to handle relative imports
                plugin_module_name = f"claude_dev_cli.plugins.{item.name}.plugin"
                module = importlib.import_module(plugin_module_name)
                
                # Look for plugin registration function
                if hasattr(module, "register_plugin"):
                    plugin = module.register_plugin()
                    plugins.append(plugin)
            except Exception as e:
                # Silently skip plugins that fail to load
                pass
    
    return plugins


# Alias for backwards compatibility and clearer intent
load_plugins = discover_plugins

__all__ = ["Plugin", "discover_plugins", "load_plugins"]
