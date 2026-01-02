"""Interactive diff viewer with multiple keybinding modes."""

import difflib
from pathlib import Path
from typing import List, Optional, Tuple
import os

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


class Hunk:
    """Represents a single diff hunk."""
    
    def __init__(
        self,
        original_lines: List[str],
        proposed_lines: List[str],
        original_start: int,
        proposed_start: int
    ):
        self.original_lines = original_lines
        self.proposed_lines = proposed_lines
        self.original_start = original_start
        self.proposed_start = proposed_start
        self.accepted = None  # None = undecided, True = accepted, False = rejected
    
    def get_context(self) -> str:
        """Get a brief context description of this hunk."""
        if self.proposed_lines:
            first_line = self.proposed_lines[0].strip()
            return first_line[:50] if len(first_line) > 50 else first_line
        return "deletion"


class DiffViewer:
    """Interactive diff viewer with multiple keybinding modes."""
    
    def __init__(
        self,
        original_path: Path,
        proposed_path: Path,
        keybinding_mode: str = "auto",
        console: Optional[Console] = None
    ):
        self.original_path = original_path
        self.proposed_path = proposed_path
        self.console = console or Console()
        
        # Detect keybinding mode
        if keybinding_mode == "auto":
            self.keybinding_mode = self._detect_keybinding_mode()
        else:
            self.keybinding_mode = keybinding_mode
        
        # Load files
        with open(original_path) as f:
            self.original_content = f.read()
            self.original_lines = self.original_content.splitlines(keepends=True)
        
        with open(proposed_path) as f:
            self.proposed_content = f.read()
            self.proposed_lines = self.proposed_content.splitlines(keepends=True)
        
        # Generate hunks
        self.hunks = self._generate_hunks()
        self.current_hunk_idx = 0
        self.filename = proposed_path.name
    
    def _detect_keybinding_mode(self) -> str:
        """Auto-detect keybinding preference from environment."""
        # Check if user has vim/nvim in their environment
        editor = os.environ.get("EDITOR", "").lower()
        visual = os.environ.get("VISUAL", "").lower()
        
        if "vim" in editor or "vim" in visual or "nvim" in editor or "nvim" in visual:
            return "nvim"
        return "fresh"
    
    def _generate_hunks(self) -> List[Hunk]:
        """Generate hunks from diff."""
        hunks = []
        differ = difflib.Differ()
        diff = list(differ.compare(self.original_lines, self.proposed_lines))
        
        i = 0
        while i < len(diff):
            # Find start of a hunk (lines that differ)
            while i < len(diff) and diff[i].startswith("  "):
                i += 1
            
            if i >= len(diff):
                break
            
            # Collect the hunk
            original_lines = []
            proposed_lines = []
            original_start = i
            proposed_start = i
            
            while i < len(diff) and not diff[i].startswith("  "):
                line = diff[i]
                if line.startswith("- "):
                    original_lines.append(line[2:])
                elif line.startswith("+ "):
                    proposed_lines.append(line[2:])
                elif line.startswith("? "):
                    # Skip hint lines
                    pass
                i += 1
            
            if original_lines or proposed_lines:
                hunks.append(Hunk(
                    original_lines,
                    proposed_lines,
                    original_start,
                    proposed_start
                ))
        
        return hunks
    
    def _get_keybindings(self) -> dict:
        """Get keybindings based on mode."""
        if self.keybinding_mode == "nvim":
            return {
                "accept": ["y", "a"],
                "reject": ["n", "d"],
                "edit": ["e", "c"],
                "split": ["s"],
                "quit": ["q", "ZZ"],
                "accept_all": ["A"],
                "reject_all": ["D"],
                "undo": ["u"],
                "help": ["?", "h"],
                "next": ["j", "n"],
                "prev": ["k", "p"],
                "goto_first": ["gg"],
                "goto_last": ["G"],
            }
        else:  # fresh mode
            return {
                "accept": ["y", "Enter"],
                "reject": ["n", "Backspace"],
                "edit": ["e"],
                "split": ["s"],
                "quit": ["q", "Esc"],
                "accept_all": ["Ctrl-A"],
                "reject_all": ["Ctrl-R"],
                "undo": ["Ctrl-Z"],
                "help": ["F1", "?"],
                "next": ["Down", "j"],
                "prev": ["Up", "k"],
                "goto_first": ["Home"],
                "goto_last": ["End"],
            }
    
    def _show_help(self) -> None:
        """Display help panel."""
        kb = self._get_keybindings()
        mode_name = "Neovim" if self.keybinding_mode == "nvim" else "Fresh"
        
        table = Table(title=f"{mode_name} Keybindings", show_header=True)
        table.add_column("Action", style="cyan")
        table.add_column("Keys", style="green")
        
        table.add_row("Accept hunk", " or ".join(kb["accept"]))
        table.add_row("Reject hunk", " or ".join(kb["reject"]))
        table.add_row("Edit hunk", " or ".join(kb["edit"]))
        table.add_row("Split hunk", " or ".join(kb["split"]))
        table.add_row("Next hunk", " or ".join(kb["next"]))
        table.add_row("Previous hunk", " or ".join(kb["prev"]))
        table.add_row("Accept all", " or ".join(kb["accept_all"]))
        table.add_row("Reject all", " or ".join(kb["reject_all"]))
        table.add_row("Undo", " or ".join(kb["undo"]))
        table.add_row("Quit", " or ".join(kb["quit"]))
        table.add_row("Help", " or ".join(kb["help"]))
        
        self.console.print(table)
        self.console.print("\n[dim]Press any key to continue...[/dim]")
        self.console.input()
    
    def _display_hunk(self, hunk: Hunk) -> None:
        """Display a single hunk with syntax highlighting."""
        self.console.clear()
        
        # Title
        mode_indicator = "🎹 Neovim" if self.keybinding_mode == "nvim" else "✨ Fresh"
        self.console.print(
            Panel(
                f"{mode_indicator} Mode | {self.filename}",
                title=f"Hunk {self.current_hunk_idx + 1}/{len(self.hunks)}",
                border_style="blue"
            )
        )
        
        # Show original (if any deletions)
        if hunk.original_lines:
            self.console.print("\n[bold red]━━━ Original (-):[/bold red]")
            for line in hunk.original_lines:
                self.console.print(f"[red]- {line}[/red]", end="")
        
        # Show proposed (if any additions)
        if hunk.proposed_lines:
            self.console.print("\n[bold green]━━━ Proposed (+):[/bold green]")
            for line in hunk.proposed_lines:
                self.console.print(f"[green]+ {line}[/green]", end="")
        
        # Context
        context = hunk.get_context()
        self.console.print(f"\n[dim]Context: {context}[/dim]")
        
        # Status
        status = "✓ Accepted" if hunk.accepted is True else "✗ Rejected" if hunk.accepted is False else "? Undecided"
        self.console.print(f"Status: {status}\n")
    
    def _show_prompt(self) -> None:
        """Show action prompt based on keybinding mode."""
        kb = self._get_keybindings()
        
        if self.keybinding_mode == "nvim":
            prompt = (
                f"[cyan][y]es [n]o [e]dit [s]plit | "
                f"[j]next [k]prev [q]uit [?]help[/cyan]"
            )
        else:  # fresh
            prompt = (
                f"[cyan][y]es [n]o [e]dit [s]plit | "
                f"[↓]next [↑]prev [q]uit [?]help[/cyan]"
            )
        
        self.console.print(prompt)
    
    def run(self) -> Optional[str]:
        """Run the interactive diff viewer.
        
        Returns:
            Final content with accepted changes or None if cancelled
        """
        if not self.hunks:
            self.console.print("[yellow]No differences found[/yellow]")
            return self.original_content
        
        # Show initial help
        self._show_help()
        
        while self.current_hunk_idx < len(self.hunks):
            hunk = self.hunks[self.current_hunk_idx]
            self._display_hunk(hunk)
            self._show_prompt()
            
            # Get user input
            choice = self.console.input("\nYour choice: ").strip().lower()
            
            kb = self._get_keybindings()
            
            # Process choice
            if choice in kb["accept"]:
                hunk.accepted = True
                self.current_hunk_idx += 1
            elif choice in kb["reject"]:
                hunk.accepted = False
                self.current_hunk_idx += 1
            elif choice in kb["edit"]:
                self.console.print("[yellow]Edit mode not yet implemented[/yellow]")
                self.console.input("Press Enter to continue...")
            elif choice in kb["split"]:
                self.console.print("[yellow]Split mode not yet implemented[/yellow]")
                self.console.input("Press Enter to continue...")
            elif choice in kb["next"]:
                if self.current_hunk_idx < len(self.hunks) - 1:
                    self.current_hunk_idx += 1
            elif choice in kb["prev"]:
                if self.current_hunk_idx > 0:
                    self.current_hunk_idx -= 1
            elif choice in kb["accept_all"]:
                for h in self.hunks[self.current_hunk_idx:]:
                    h.accepted = True
                break
            elif choice in kb["reject_all"]:
                for h in self.hunks[self.current_hunk_idx:]:
                    h.accepted = False
                break
            elif choice in kb["quit"]:
                self.console.print("[yellow]Quitting without applying changes[/yellow]")
                return None
            elif choice in kb["help"]:
                self._show_help()
            else:
                self.console.print(f"[red]Unknown command: {choice}[/red]")
                self.console.input("Press Enter to continue...")
        
        # Apply accepted changes
        return self._apply_changes()
    
    def _apply_changes(self) -> str:
        """Apply accepted changes and return final content."""
        result_lines = list(self.original_lines)
        
        # Apply hunks in reverse order to maintain line numbers
        for hunk in reversed(self.hunks):
            if hunk.accepted:
                # Remove original lines
                for _ in hunk.original_lines:
                    if hunk.original_start < len(result_lines):
                        result_lines.pop(hunk.original_start)
                
                # Insert proposed lines
                for i, line in enumerate(hunk.proposed_lines):
                    result_lines.insert(hunk.original_start + i, line)
        
        return "".join(result_lines)
