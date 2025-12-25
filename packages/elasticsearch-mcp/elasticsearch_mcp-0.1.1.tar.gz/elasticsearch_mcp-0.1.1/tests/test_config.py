"""Tests for elasticsearch_mcp configuration."""

from elasticsearch_mcp.config import settings


def test_settings_defaults() -> None:
    """Test that settings have sensible defaults."""
    assert settings.max_results > 0
    assert settings.timeout > 0
