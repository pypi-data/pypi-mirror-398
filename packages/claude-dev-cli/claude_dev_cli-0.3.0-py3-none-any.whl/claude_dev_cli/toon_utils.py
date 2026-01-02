"""TOON format utilities for token-efficient LLM communication."""

from typing import Any, Optional

# Try to import toon-format, but make it optional
try:
    from toon_format import encode as toon_encode, decode as toon_decode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    toon_encode = None
    toon_decode = None


def is_toon_available() -> bool:
    """Check if TOON format support is available."""
    return TOON_AVAILABLE


def to_toon(data: Any) -> str:
    """
    Convert Python data to TOON format.
    
    Args:
        data: Python dict, list, or primitive to encode
        
    Returns:
        TOON-formatted string
        
    Raises:
        ImportError: If toon-format is not installed
    """
    if not TOON_AVAILABLE:
        raise ImportError(
            "TOON format support not installed. "
            "Install with: pip install claude-dev-cli[toon]"
        )
    
    return toon_encode(data)


def from_toon(toon_str: str) -> Any:
    """
    Convert TOON format back to Python data.
    
    Args:
        toon_str: TOON-formatted string
        
    Returns:
        Python dict, list, or primitive
        
    Raises:
        ImportError: If toon-format is not installed
    """
    if not TOON_AVAILABLE:
        raise ImportError(
            "TOON format support not installed. "
            "Install with: pip install claude-dev-cli[toon]"
        )
    
    return toon_decode(toon_str)


def format_for_llm(data: Any, use_toon: bool = True) -> str:
    """
    Format data for LLM consumption, preferring TOON if available.
    
    Args:
        data: Data to format
        use_toon: Whether to use TOON format if available (default: True)
        
    Returns:
        Formatted string (TOON if available and requested, else JSON)
    """
    import json
    
    if use_toon and TOON_AVAILABLE:
        try:
            return to_toon(data)
        except Exception:
            # Fall back to JSON if TOON encoding fails
            pass
    
    return json.dumps(data, indent=2)


def auto_detect_format(content: str) -> tuple[str, Any]:
    """
    Auto-detect if content is TOON or JSON and decode accordingly.
    
    Args:
        content: String content to decode
        
    Returns:
        Tuple of (format_name, decoded_data)
        
    Raises:
        ValueError: If content cannot be parsed as either format
    """
    import json
    
    # Try TOON first if available
    if TOON_AVAILABLE:
        try:
            data = from_toon(content)
            return ("toon", data)
        except Exception:
            pass
    
    # Try JSON
    try:
        data = json.loads(content)
        return ("json", data)
    except json.JSONDecodeError:
        pass
    
    raise ValueError("Content is neither valid TOON nor JSON")
