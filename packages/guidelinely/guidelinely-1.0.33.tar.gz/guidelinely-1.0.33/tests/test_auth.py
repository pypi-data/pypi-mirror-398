"""Tests for authentication helpers."""

from guidelinely.auth import get_api_key


def test_get_api_key_from_argument():
    """Test getting API key from direct argument."""
    key = get_api_key("test_key_123")
    assert key == "test_key_123"


def test_get_api_key_from_environment(monkeypatch):
    """Test getting API key from environment variable."""
    monkeypatch.setenv("GUIDELINELY_API_KEY", "env_key_456")
    key = get_api_key()
    assert key == "env_key_456"


def test_get_api_key_argument_overrides_environment(monkeypatch):
    """Test that direct argument takes precedence over environment."""
    monkeypatch.setenv("GUIDELINELY_API_KEY", "env_key")
    key = get_api_key("arg_key")
    assert key == "arg_key"


def test_get_api_key_none_when_not_set(monkeypatch):
    """Test that None is returned when no key is available."""
    monkeypatch.delenv("GUIDELINELY_API_KEY", raising=False)
    key = get_api_key()
    assert key is None


def test_get_api_key_none_when_empty_string(monkeypatch):
    """Test that None is returned when environment variable is empty."""
    monkeypatch.setenv("GUIDELINELY_API_KEY", "")
    key = get_api_key()
    assert key is None
