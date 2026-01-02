"""Core Claude API client with routing and tracking."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from anthropic import Anthropic

from claude_dev_cli.config import Config


class ClaudeClient:
    """Claude API client with multi-key routing and usage tracking."""
    
    def __init__(self, config: Optional[Config] = None, api_config_name: Optional[str] = None):
        """Initialize Claude client."""
        self.config = config or Config()
        
        # Determine which API config to use
        project_profile = self.config.get_project_profile()
        if project_profile:
            api_config_name = project_profile.api_config
        
        self.api_config = self.config.get_api_config(api_config_name)
        if not self.api_config:
            raise ValueError(
                "No API configuration found. Run 'cdc config add' to set up an API key."
            )
        
        self.client = Anthropic(api_key=self.api_config.api_key)
        self.model = self.config.get_model()
        self.max_tokens = self.config.get_max_tokens()
    
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        stream: bool = False
    ) -> str:
        """Make a call to Claude API."""
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        # Check project profile for system prompt
        project_profile = self.config.get_project_profile()
        if project_profile and project_profile.system_prompt and not system_prompt:
            system_prompt = project_profile.system_prompt
        
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        start_time = datetime.utcnow()
        response = self.client.messages.create(**kwargs)
        end_time = datetime.utcnow()
        
        # Log usage
        self._log_usage(
            prompt=prompt,
            response=response,
            model=model,
            duration_ms=int((end_time - start_time).total_seconds() * 1000),
            api_config_name=self.api_config.name
        )
        
        # Extract text from response
        text_blocks = [
            block.text for block in response.content if hasattr(block, 'text')
        ]
        return '\n'.join(text_blocks)
    
    def call_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0
    ):
        """Make a streaming call to Claude API."""
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        # Check project profile for system prompt
        project_profile = self.config.get_project_profile()
        if project_profile and project_profile.system_prompt and not system_prompt:
            system_prompt = project_profile.system_prompt
        
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    
    def _log_usage(
        self,
        prompt: str,
        response: Any,
        model: str,
        duration_ms: int,
        api_config_name: str
    ) -> None:
        """Log API usage to file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_config": api_config_name,
            "model": model,
            "prompt_preview": prompt[:100],
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "duration_ms": duration_ms,
        }
        
        with open(self.config.usage_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
