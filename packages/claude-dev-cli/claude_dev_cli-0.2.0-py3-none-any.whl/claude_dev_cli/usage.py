"""Usage tracking and statistics."""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from claude_dev_cli.config import Config


# Pricing per 1M tokens (as of Dec 2024)
MODEL_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


class UsageTracker:
    """Track and display API usage statistics."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize usage tracker."""
        self.config = config or Config()
    
    def _read_logs(
        self,
        days: Optional[int] = None,
        api_config: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Read usage logs with optional filters."""
        if not self.config.usage_log.exists():
            return []
        
        cutoff = None
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = []
        with open(self.config.usage_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                    
                    # Apply filters
                    if cutoff and timestamp < cutoff:
                        continue
                    if api_config and entry.get("api_config") != api_config:
                        continue
                    
                    logs.append(entry)
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a given usage."""
        pricing = MODEL_PRICING.get(model, {"input": 3.00, "output": 15.00})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def display_usage(
        self,
        console: Console,
        days: Optional[int] = None,
        api_config: Optional[str] = None
    ) -> None:
        """Display usage statistics."""
        logs = self._read_logs(days=days, api_config=api_config)
        
        if not logs:
            console.print("[yellow]No usage data found.[/yellow]")
            return
        
        # Calculate totals
        total_input = 0
        total_output = 0
        total_cost = 0.0
        total_calls = len(logs)
        
        by_api = defaultdict(lambda: {"input": 0, "output": 0, "calls": 0, "cost": 0.0})
        by_date = defaultdict(lambda: {"input": 0, "output": 0, "calls": 0, "cost": 0.0})
        by_model = defaultdict(lambda: {"input": 0, "output": 0, "calls": 0, "cost": 0.0})
        
        for entry in logs:
            input_tokens = entry["input_tokens"]
            output_tokens = entry["output_tokens"]
            model = entry["model"]
            api = entry["api_config"]
            date = entry["timestamp"][:10]
            
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            total_input += input_tokens
            total_output += output_tokens
            total_cost += cost
            
            by_api[api]["input"] += input_tokens
            by_api[api]["output"] += output_tokens
            by_api[api]["calls"] += 1
            by_api[api]["cost"] += cost
            
            by_date[date]["input"] += input_tokens
            by_date[date]["output"] += output_tokens
            by_date[date]["calls"] += 1
            by_date[date]["cost"] += cost
            
            by_model[model]["input"] += input_tokens
            by_model[model]["output"] += output_tokens
            by_model[model]["calls"] += 1
            by_model[model]["cost"] += cost
        
        # Display summary
        title = "Usage Summary"
        if days:
            title += f" (Last {days} days)"
        if api_config:
            title += f" - {api_config}"
        
        summary = f"""[bold]Total Calls:[/bold] {total_calls:,}
[bold]Input Tokens:[/bold] {total_input:,}
[bold]Output Tokens:[/bold] {total_output:,}
[bold]Total Tokens:[/bold] {total_input + total_output:,}
[bold]Estimated Cost:[/bold] ${total_cost:.2f}"""
        
        console.print(Panel(summary, title=title, border_style="green"))
        
        # Display by API config
        if len(by_api) > 1:
            console.print("\n[bold]By API Config:[/bold]")
            api_table = Table(show_header=True, header_style="bold cyan")
            api_table.add_column("API Config")
            api_table.add_column("Calls", justify="right")
            api_table.add_column("Input Tokens", justify="right")
            api_table.add_column("Output Tokens", justify="right")
            api_table.add_column("Cost", justify="right")
            
            for api_name in sorted(by_api.keys()):
                stats = by_api[api_name]
                api_table.add_row(
                    api_name,
                    f"{stats['calls']:,}",
                    f"{stats['input']:,}",
                    f"{stats['output']:,}",
                    f"${stats['cost']:.2f}"
                )
            
            console.print(api_table)
        
        # Display by model
        if len(by_model) > 1:
            console.print("\n[bold]By Model:[/bold]")
            model_table = Table(show_header=True, header_style="bold cyan")
            model_table.add_column("Model")
            model_table.add_column("Calls", justify="right")
            model_table.add_column("Input Tokens", justify="right")
            model_table.add_column("Output Tokens", justify="right")
            model_table.add_column("Cost", justify="right")
            
            for model_name in sorted(by_model.keys()):
                stats = by_model[model_name]
                model_table.add_row(
                    model_name.split("-")[-1],  # Show short version
                    f"{stats['calls']:,}",
                    f"{stats['input']:,}",
                    f"{stats['output']:,}",
                    f"${stats['cost']:.2f}"
                )
            
            console.print(model_table)
        
        # Display by date (last 7 days)
        console.print("\n[bold]By Date:[/bold]")
        date_table = Table(show_header=True, header_style="bold cyan")
        date_table.add_column("Date")
        date_table.add_column("Calls", justify="right")
        date_table.add_column("Tokens", justify="right")
        date_table.add_column("Cost", justify="right")
        
        for date in sorted(by_date.keys(), reverse=True)[:7]:
            stats = by_date[date]
            total_tokens = stats['input'] + stats['output']
            date_table.add_row(
                date,
                f"{stats['calls']:,}",
                f"{total_tokens:,}",
                f"${stats['cost']:.2f}"
            )
        
        console.print(date_table)
