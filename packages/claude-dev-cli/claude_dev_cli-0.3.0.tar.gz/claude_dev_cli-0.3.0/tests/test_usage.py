"""Tests for usage module."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

import pytest
from rich.console import Console

from claude_dev_cli.usage import UsageTracker, MODEL_PRICING


class TestUsageTracker:
    """Tests for UsageTracker class."""
    
    def test_init(self, config_file: Path) -> None:
        """Test UsageTracker initialization."""
        tracker = UsageTracker()
        
        assert tracker.config is not None
    
    def test_read_logs_empty(self, temp_config_dir: Path) -> None:
        """Test reading logs when file is empty."""
        tracker = UsageTracker()
        logs = tracker._read_logs()
        
        assert logs == []
    
    def test_read_logs_with_entries(self, usage_log_file: Path) -> None:
        """Test reading logs with entries."""
        tracker = UsageTracker()
        logs = tracker._read_logs()
        
        assert len(logs) == 2
        assert logs[0]["api_config"] == "personal"
        assert logs[1]["api_config"] == "client"
    
    def test_read_logs_filter_by_days(
        self, temp_config_dir: Path
    ) -> None:
        """Test filtering logs by days."""
        # Create logs with different dates
        log_path = temp_config_dir / "usage.jsonl"
        old_log = {
            "timestamp": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "api_config": "old",
            "model": "claude-3-5-sonnet-20241022",
            "prompt_preview": "Old prompt",
            "input_tokens": 100,
            "output_tokens": 200,
            "duration_ms": 1500,
        }
        recent_log = {
            "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "api_config": "recent",
            "model": "claude-3-5-sonnet-20241022",
            "prompt_preview": "Recent prompt",
            "input_tokens": 150,
            "output_tokens": 250,
            "duration_ms": 1800,
        }
        
        with open(log_path, "w") as f:
            f.write(json.dumps(old_log) + "\n")
            f.write(json.dumps(recent_log) + "\n")
        
        tracker = UsageTracker()
        logs = tracker._read_logs(days=7)
        
        assert len(logs) == 1
        assert logs[0]["api_config"] == "recent"
    
    def test_read_logs_filter_by_api_config(self, usage_log_file: Path) -> None:
        """Test filtering logs by API config."""
        tracker = UsageTracker()
        logs = tracker._read_logs(api_config="personal")
        
        assert len(logs) == 1
        assert logs[0]["api_config"] == "personal"
    
    def test_read_logs_handles_malformed_json(
        self, temp_config_dir: Path
    ) -> None:
        """Test that malformed JSON entries are skipped."""
        log_path = temp_config_dir / "usage.jsonl"
        good_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_config": "personal",
            "model": "claude-3-5-sonnet-20241022",
            "prompt_preview": "Test",
            "input_tokens": 100,
            "output_tokens": 200,
            "duration_ms": 1500,
        }
        
        with open(log_path, "w") as f:
            f.write(json.dumps(good_log) + "\n")
            f.write("this is not json\n")
            f.write(json.dumps(good_log) + "\n")
        
        tracker = UsageTracker()
        logs = tracker._read_logs()
        
        # Should skip the malformed line
        assert len(logs) == 2
    
    def test_calculate_cost_sonnet(self) -> None:
        """Test cost calculation for Sonnet model."""
        tracker = UsageTracker()
        
        cost = tracker._calculate_cost(
            "claude-3-5-sonnet-20241022",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        
        # Sonnet: $3/M input, $15/M output
        expected = (1_000_000 / 1_000_000) * 3.00 + (1_000_000 / 1_000_000) * 15.00
        assert cost == expected
    
    def test_calculate_cost_haiku(self) -> None:
        """Test cost calculation for Haiku model."""
        tracker = UsageTracker()
        
        cost = tracker._calculate_cost(
            "claude-3-haiku-20240307",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        
        # Haiku: $0.25/M input, $1.25/M output
        expected = (1_000_000 / 1_000_000) * 0.25 + (1_000_000 / 1_000_000) * 1.25
        assert cost == expected
    
    def test_calculate_cost_unknown_model(self) -> None:
        """Test cost calculation for unknown model uses default pricing."""
        tracker = UsageTracker()
        
        cost = tracker._calculate_cost(
            "unknown-model",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        
        # Unknown model defaults to Sonnet pricing
        expected = (1_000_000 / 1_000_000) * 3.00 + (1_000_000 / 1_000_000) * 15.00
        assert cost == expected
    
    def test_display_usage_no_data(
        self, temp_config_dir: Path
    ) -> None:
        """Test displaying usage when no data exists."""
        tracker = UsageTracker()
        console = Console(file=StringIO())
        
        tracker.display_usage(console)
        
        # Should not raise an error
    
    def test_display_usage_with_data(self, usage_log_file: Path) -> None:
        """Test displaying usage with data."""
        tracker = UsageTracker()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        
        tracker.display_usage(console)
        
        result = output.getvalue()
        
        # Check that summary information is present
        assert "Total Calls" in result
        assert "Input Tokens" in result
        assert "Output Tokens" in result
        assert "Estimated Cost" in result
    
    def test_display_usage_calculates_totals_correctly(
        self, usage_log_file: Path
    ) -> None:
        """Test that usage totals are calculated correctly."""
        tracker = UsageTracker()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        
        tracker.display_usage(console)
        
        result = output.getvalue()
        
        # From fixture: 100+150 input, 200+250 output
        assert "250" in result  # Total input tokens
        assert "450" in result  # Total output tokens
        assert "700" in result  # Total tokens (250+450)
    
    def test_display_usage_by_api_config(self, usage_log_file: Path) -> None:
        """Test usage display grouped by API config."""
        tracker = UsageTracker()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        
        tracker.display_usage(console)
        
        result = output.getvalue()
        
        # Should show both API configs
        assert "personal" in result
        assert "client" in result
    
    def test_display_usage_filter_by_api(self, usage_log_file: Path) -> None:
        """Test filtering display by API config."""
        tracker = UsageTracker()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        
        tracker.display_usage(console, api_config="personal")
        
        result = output.getvalue()
        
        # Should only show personal API usage
        assert "personal" in result
        # Total should be just the personal usage: 100 input + 200 output = 300 tokens
        assert "100" in result  # Input tokens
        assert "200" in result  # Output tokens
