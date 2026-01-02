"""Diff editor plugin registration."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from claude_dev_cli.plugins.base import Plugin
from .viewer import DiffViewer


class DiffEditorPlugin(Plugin):
    """Interactive diff editor plugin."""
    
    def __init__(self):
        super().__init__(
            name="diff-editor",
            version="0.1.0",
            description="Interactive diff viewer for reviewing code changes"
        )
        self.console = Console()
    
    def register_commands(self, cli: click.Group) -> None:
        """Register diff editor commands."""
        
        @cli.command("diff")
        @click.argument("original", type=click.Path(exists=True))
        @click.argument("proposed", type=click.Path(exists=True))
        @click.option(
            "--keybindings",
            "-k",
            type=click.Choice(["nvim", "fresh", "auto"]),
            default="auto",
            help="Keybinding mode (nvim, fresh, or auto-detect)"
        )
        @click.option(
            "--output",
            "-o",
            type=click.Path(),
            help="Output file path for accepted changes"
        )
        def diff_command(
            original: str,
            proposed: str,
            keybindings: str,
            output: Optional[str]
        ) -> None:
            """Interactively review differences between two files."""
            viewer = DiffViewer(
                original_path=Path(original),
                proposed_path=Path(proposed),
                keybinding_mode=keybindings,
                console=self.console
            )
            
            result = viewer.run()
            
            if result and output:
                with open(output, "w") as f:
                    f.write(result)
                self.console.print(f"\n[green]✓[/green] Changes saved to: {output}")
            elif result:
                self.console.print("\n[bold]Final result:[/bold]")
                self.console.print(result)
        
        @cli.command("apply-diff")
        @click.argument("file_path", type=click.Path(exists=True))
        @click.option(
            "--keybindings",
            "-k",
            type=click.Choice(["nvim", "fresh", "auto"]),
            default="auto",
            help="Keybinding mode"
        )
        @click.option(
            "--in-place",
            "-i",
            is_flag=True,
            help="Edit file in place"
        )
        def apply_diff_command(
            file_path: str,
            keybindings: str,
            in_place: bool
        ) -> None:
            """Apply AI-suggested changes to a file interactively."""
            self.console.print(
                f"[yellow]This would apply changes to {file_path} interactively[/yellow]"
            )
            self.console.print("Feature coming soon!")


def register_plugin() -> Plugin:
    """Register the diff editor plugin."""
    return DiffEditorPlugin()
