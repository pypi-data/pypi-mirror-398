"""Tests for toon_utils module."""

import json
from unittest.mock import patch, Mock

import pytest

from claude_dev_cli import toon_utils


class TestToonUtils:
    """Tests for TOON utilities."""
    
    def test_is_toon_available_true(self) -> None:
        """Test is_toon_available when toon-format is installed."""
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            assert toon_utils.is_toon_available() is True
    
    def test_is_toon_available_false(self) -> None:
        """Test is_toon_available when toon-format is not installed."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            assert toon_utils.is_toon_available() is False
    
    def test_to_toon_not_available_raises(self) -> None:
        """Test to_toon raises when toon-format not installed."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            with pytest.raises(ImportError, match="TOON format support not installed"):
                toon_utils.to_toon({"test": "data"})
    
    def test_to_toon_with_toon_available(self) -> None:
        """Test to_toon when toon-format is available."""
        mock_encode = Mock(return_value="toon_string")
        
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            with patch.object(toon_utils, "toon_encode", mock_encode):
                result = toon_utils.to_toon({"test": "data"})
                
                assert result == "toon_string"
                mock_encode.assert_called_once_with({"test": "data"})
    
    def test_from_toon_not_available_raises(self) -> None:
        """Test from_toon raises when toon-format not installed."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            with pytest.raises(ImportError, match="TOON format support not installed"):
                toon_utils.from_toon("toon_string")
    
    def test_from_toon_with_toon_available(self) -> None:
        """Test from_toon when toon-format is available."""
        mock_decode = Mock(return_value={"test": "data"})
        
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            with patch.object(toon_utils, "toon_decode", mock_decode):
                result = toon_utils.from_toon("toon_string")
                
                assert result == {"test": "data"}
                mock_decode.assert_called_once_with("toon_string")
    
    def test_format_for_llm_prefers_toon(self) -> None:
        """Test format_for_llm prefers TOON when available."""
        mock_encode = Mock(return_value="toon_output")
        
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            with patch.object(toon_utils, "toon_encode", mock_encode):
                result = toon_utils.format_for_llm({"test": "data"})
                
                assert result == "toon_output"
    
    def test_format_for_llm_falls_back_to_json(self) -> None:
        """Test format_for_llm falls back to JSON when TOON unavailable."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            result = toon_utils.format_for_llm({"test": "data"})
            
            data = json.loads(result)
            assert data == {"test": "data"}
    
    def test_format_for_llm_use_toon_false(self) -> None:
        """Test format_for_llm with use_toon=False."""
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            result = toon_utils.format_for_llm({"test": "data"}, use_toon=False)
            
            data = json.loads(result)
            assert data == {"test": "data"}
    
    def test_format_for_llm_toon_encoding_fails(self) -> None:
        """Test format_for_llm falls back to JSON if TOON encoding fails."""
        mock_encode = Mock(side_effect=Exception("TOON error"))
        
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            with patch.object(toon_utils, "toon_encode", mock_encode):
                result = toon_utils.format_for_llm({"test": "data"})
                
                # Should fall back to JSON
                data = json.loads(result)
                assert data == {"test": "data"}
    
    def test_auto_detect_format_toon(self) -> None:
        """Test auto_detect_format with TOON content."""
        mock_decode = Mock(return_value={"test": "data"})
        
        with patch.object(toon_utils, "TOON_AVAILABLE", True):
            with patch.object(toon_utils, "toon_decode", mock_decode):
                format_name, data = toon_utils.auto_detect_format("toon_content")
                
                assert format_name == "toon"
                assert data == {"test": "data"}
    
    def test_auto_detect_format_json(self) -> None:
        """Test auto_detect_format with JSON content."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            format_name, data = toon_utils.auto_detect_format('{"test": "data"}')
            
            assert format_name == "json"
            assert data == {"test": "data"}
    
    def test_auto_detect_format_invalid(self) -> None:
        """Test auto_detect_format with invalid content."""
        with patch.object(toon_utils, "TOON_AVAILABLE", False):
            with pytest.raises(ValueError, match="neither valid TOON nor JSON"):
                toon_utils.auto_detect_format("not valid format")
