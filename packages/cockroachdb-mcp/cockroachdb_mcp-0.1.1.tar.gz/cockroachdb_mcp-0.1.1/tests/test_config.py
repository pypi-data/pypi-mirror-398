"""Tests for cockroachdb_mcp configuration."""

from cockroachdb_mcp.config import settings


def test_settings_defaults() -> None:
    """Test that settings have sensible defaults."""
    assert settings.max_rows > 0
    assert settings.query_timeout > 0
