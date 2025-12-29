"""Tests for configuration Q&A functionality."""

import pytest
from pathlib import Path
from sparkwise.config_qa import ConfigurationAssistant


class TestConfigurationAssistant:
    """Test suite for ConfigurationAssistant."""
    
    def test_assistant_initializes(self):
        """Test that assistant initializes without errors."""
        assistant = ConfigurationAssistant()
        assert assistant is not None
    
    def test_search_returns_list(self):
        """Test that search returns a list."""
        assistant = ConfigurationAssistant()
        results = assistant.search("shuffle")
        
        assert isinstance(results, list)
    
    def test_config_doesnt_crash_on_unknown(self):
        """Test that config() handles unknown configs gracefully."""
        assistant = ConfigurationAssistant()
        
        # Should not raise exception
        try:
            assistant.config("nonexistent.config.parameter")
        except Exception as e:
            pytest.fail(f"config() raised {e} on unknown parameter")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
