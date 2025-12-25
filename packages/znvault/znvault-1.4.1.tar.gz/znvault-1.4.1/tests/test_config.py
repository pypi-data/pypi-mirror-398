# Path: zn-vault-sdk-python/tests/test_config.py
"""Tests for configuration module."""

import pytest
from znvault.config import ZnVaultConfig
from znvault.exceptions import ConfigurationError


class TestZnVaultConfig:
    """Test ZnVaultConfig class."""

    def test_config_creation(self) -> None:
        """Test basic config creation."""
        config = ZnVaultConfig(
            base_url="https://vault.example.com:8443",
            api_key="test-key",
            timeout=60,
            trust_self_signed=True,
        )

        assert config.base_url == "https://vault.example.com:8443"
        assert config.api_key == "test-key"
        assert config.timeout == 60
        assert config.trust_self_signed is True

    def test_config_strips_trailing_slash(self) -> None:
        """Test that trailing slash is stripped from base URL."""
        config = ZnVaultConfig(base_url="https://vault.example.com/")
        assert config.base_url == "https://vault.example.com"

    def test_config_requires_base_url(self) -> None:
        """Test that base URL is required."""
        with pytest.raises(ConfigurationError) as exc_info:
            ZnVaultConfig(base_url="")
        assert "Base URL" in str(exc_info.value)

    def test_config_defaults(self) -> None:
        """Test default configuration values."""
        config = ZnVaultConfig(base_url="https://vault.example.com")

        assert config.api_key is None
        assert config.timeout == 30
        assert config.verify_ssl is True
        assert config.trust_self_signed is False
        assert config.retry_attempts == 3
        assert config.retry_delay == 0.5


class TestZnVaultConfigBuilder:
    """Test ZnVaultConfig.Builder class."""

    def test_builder_basic(self) -> None:
        """Test basic builder usage."""
        config = (
            ZnVaultConfig.Builder()
            .base_url("https://vault.example.com:8443")
            .api_key("test-key")
            .timeout(60)
            .trust_self_signed(True)
            .build()
        )

        assert config.base_url == "https://vault.example.com:8443"
        assert config.api_key == "test-key"
        assert config.timeout == 60
        assert config.trust_self_signed is True

    def test_builder_requires_base_url(self) -> None:
        """Test that builder requires base URL."""
        with pytest.raises(ConfigurationError) as exc_info:
            ZnVaultConfig.Builder().build()
        assert "Base URL" in str(exc_info.value)

    def test_builder_custom_headers(self) -> None:
        """Test adding custom headers."""
        config = (
            ZnVaultConfig.Builder()
            .base_url("https://vault.example.com")
            .header("X-Custom", "value")
            .build()
        )

        assert config.headers.get("X-Custom") == "value"

    def test_builder_retry_config(self) -> None:
        """Test retry configuration."""
        config = (
            ZnVaultConfig.Builder()
            .base_url("https://vault.example.com")
            .retry_attempts(5)
            .retry_delay(1.0)
            .build()
        )

        assert config.retry_attempts == 5
        assert config.retry_delay == 1.0
