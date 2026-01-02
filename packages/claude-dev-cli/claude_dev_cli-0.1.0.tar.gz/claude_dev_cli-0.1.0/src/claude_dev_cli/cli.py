"""Command-line interface for Claude Dev CLI."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from claude_dev_cli import __version__
from claude_dev_cli.config import Config
from claude_dev_cli.core import ClaudeClient
from claude_dev_cli.commands import (
    generate_tests,
    code_review,
    debug_code,
    generate_docs,
    refactor_code,
    git_commit_message,
)
from claude_dev_cli.usage import UsageTracker

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Claude Dev CLI - AI-powered development assistant with multi-API routing."""
    ctx.ensure_object(dict)
    ctx.obj['console'] = console


@main.command()
@click.argument('prompt', required=False)
@click.option('-f', '--file', type=click.Path(exists=True), help='Include file content in prompt')
@click.option('-s', '--system', help='System prompt')
@click.option('-a', '--api', help='API config to use')
@click.option('-m', '--model', help='Claude model to use')
@click.option('--stream/--no-stream', default=True, help='Stream response')
@click.pass_context
def ask(
    ctx: click.Context,
    prompt: Optional[str],
    file: Optional[str],
    system: Optional[str],
    api: Optional[str],
    model: Optional[str],
    stream: bool
) -> None:
    """Ask Claude a question (single-shot mode)."""
    console = ctx.obj['console']
    
    # Build prompt
    prompt_parts = []
    
    if file:
        with open(file, 'r') as f:
            file_content = f.read()
            prompt_parts.append(f"File: {file}\n\n{file_content}\n\n")
    
    # Read from stdin if available
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            prompt_parts.append(f"{stdin_content}\n\n")
    
    if prompt:
        prompt_parts.append(prompt)
    elif not prompt_parts:
        console.print("[red]Error: No prompt provided[/red]")
        sys.exit(1)
    
    full_prompt = ''.join(prompt_parts)
    
    try:
        client = ClaudeClient(api_config_name=api)
        
        if stream:
            for chunk in client.call_streaming(
                full_prompt,
                system_prompt=system,
                model=model
            ):
                console.print(chunk, end='')
            console.print()  # New line at end
        else:
            response = client.call(full_prompt, system_prompt=system, model=model)
            md = Markdown(response)
            console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def interactive(ctx: click.Context, api: Optional[str]) -> None:
    """Start interactive chat mode."""
    console = ctx.obj['console']
    
    console.print(Panel.fit(
        "Claude Dev CLI - Interactive Mode\n"
        "Type 'exit' or 'quit' to end\n"
        "Type 'clear' to reset conversation",
        title="Welcome",
        border_style="blue"
    ))
    
    try:
        client = ClaudeClient(api_config_name=api)
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                if not user_input:
                    continue
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                for chunk in client.call_streaming(user_input):
                    console.print(chunk, end='')
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command('add')
@click.argument('name')
@click.option('--api-key', help='API key (or set {NAME}_ANTHROPIC_API_KEY env var)')
@click.option('--description', help='Description of this API config')
@click.option('--default', is_flag=True, help='Set as default API config')
@click.pass_context
def config_add(
    ctx: click.Context,
    name: str,
    api_key: Optional[str],
    description: Optional[str],
    default: bool
) -> None:
    """Add a new API configuration."""
    console = ctx.obj['console']
    
    try:
        config = Config()
        config.add_api_config(
            name=name,
            api_key=api_key,
            description=description,
            make_default=default
        )
        console.print(f"[green]✓[/green] Added API config: {name}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command('list')
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """List all API configurations."""
    console = ctx.obj['console']
    
    config = Config()
    api_configs = config.list_api_configs()
    
    if not api_configs:
        console.print("[yellow]No API configurations found.[/yellow]")
        console.print("Run 'cdc config add' to add one.")
        return
    
    for cfg in api_configs:
        default_marker = " [bold green](default)[/bold green]" if cfg.default else ""
        console.print(f"• {cfg.name}{default_marker}")
        if cfg.description:
            console.print(f"  {cfg.description}")
        console.print(f"  API Key: {cfg.api_key[:15]}...")


@main.group()
def generate() -> None:
    """Generate code, tests, and documentation."""
    pass


@generate.command('tests')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path')
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def gen_tests(
    ctx: click.Context,
    file_path: str,
    output: Optional[str],
    api: Optional[str]
) -> None:
    """Generate pytest tests for a Python file."""
    console = ctx.obj['console']
    
    try:
        with console.status("[bold blue]Generating tests..."):
            result = generate_tests(file_path, api_config_name=api)
        
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"[green]✓[/green] Tests saved to: {output}")
        else:
            console.print(result)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@generate.command('docs')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path')
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def gen_docs(
    ctx: click.Context,
    file_path: str,
    output: Optional[str],
    api: Optional[str]
) -> None:
    """Generate documentation for a Python file."""
    console = ctx.obj['console']
    
    try:
        with console.status("[bold blue]Generating documentation..."):
            result = generate_docs(file_path, api_config_name=api)
        
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"[green]✓[/green] Documentation saved to: {output}")
        else:
            md = Markdown(result)
            console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('review')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def review(
    ctx: click.Context,
    file_path: str,
    api: Optional[str]
) -> None:
    """Review code for bugs and improvements."""
    console = ctx.obj['console']
    
    try:
        with console.status("[bold blue]Reviewing code..."):
            result = code_review(file_path, api_config_name=api)
        
        md = Markdown(result)
        console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('debug')
@click.option('-f', '--file', type=click.Path(exists=True), help='File to debug')
@click.option('-e', '--error', help='Error message to analyze')
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def debug(
    ctx: click.Context,
    file: Optional[str],
    error: Optional[str],
    api: Optional[str]
) -> None:
    """Debug code and analyze errors."""
    console = ctx.obj['console']
    
    # Read from stdin if available
    stdin_content = None
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
    
    try:
        with console.status("[bold blue]Analyzing error..."):
            result = debug_code(
                file_path=file,
                error_message=error or stdin_content,
                api_config_name=api
            )
        
        md = Markdown(result)
        console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('refactor')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path')
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def refactor(
    ctx: click.Context,
    file_path: str,
    output: Optional[str],
    api: Optional[str]
) -> None:
    """Suggest refactoring improvements."""
    console = ctx.obj['console']
    
    try:
        with console.status("[bold blue]Analyzing code..."):
            result = refactor_code(file_path, api_config_name=api)
        
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"[green]✓[/green] Refactored code saved to: {output}")
        else:
            md = Markdown(result)
            console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def git() -> None:
    """Git workflow helpers."""
    pass


@git.command('commit')
@click.option('-a', '--api', help='API config to use')
@click.pass_context
def git_commit(ctx: click.Context, api: Optional[str]) -> None:
    """Generate commit message from staged changes."""
    console = ctx.obj['console']
    
    try:
        with console.status("[bold blue]Analyzing changes..."):
            result = git_commit_message(api_config_name=api)
        
        console.print("\n[bold green]Suggested commit message:[/bold green]")
        console.print(Panel(result, border_style="green"))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('usage')
@click.option('--days', type=int, help='Filter by days')
@click.option('--api', help='Filter by API config')
@click.pass_context
def usage(ctx: click.Context, days: Optional[int], api: Optional[str]) -> None:
    """Show API usage statistics."""
    console = ctx.obj['console']
    
    try:
        tracker = UsageTracker()
        tracker.display_usage(console, days=days, api_config=api)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main(obj={})
