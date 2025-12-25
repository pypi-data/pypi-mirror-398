# Path: zn-vault-sdk-python/tests/test_client.py
"""Tests for client module."""

import pytest
from znvault.client import ZnVaultClient, ZnVaultClientBuilder
from znvault.exceptions import ConfigurationError


class TestZnVaultClient:
    """Test ZnVaultClient class."""

    def test_client_builder(self) -> None:
        """Test building client with builder."""
        client = (
            ZnVaultClient.builder()
            .base_url("https://vault.example.com:8443")
            .api_key("test-key")
            .timeout(60)
            .trust_self_signed(True)
            .build()
        )

        assert client.config.base_url == "https://vault.example.com:8443"
        assert client.config.api_key == "test-key"
        assert client.config.timeout == 60

    def test_client_builder_requires_base_url(self) -> None:
        """Test that builder requires base URL."""
        with pytest.raises(ConfigurationError) as exc_info:
            ZnVaultClient.builder().build()
        assert "Base URL" in str(exc_info.value)

    def test_client_create_factory(self) -> None:
        """Test create factory method."""
        client = ZnVaultClient.create(
            "https://vault.example.com:8443",
            api_key="test-key",
        )

        assert client.config.base_url == "https://vault.example.com:8443"
        assert client.config.api_key == "test-key"

    def test_client_has_all_sub_clients(self) -> None:
        """Test that client has all sub-clients."""
        client = ZnVaultClient.create("https://vault.example.com")

        assert client.auth is not None
        assert client.secrets is not None
        assert client.kms is not None
        assert client.users is not None
        assert client.tenants is not None
        assert client.roles is not None
        assert client.policies is not None
        assert client.audit is not None
        assert client.health is not None


class TestZnVaultClientBuilder:
    """Test ZnVaultClientBuilder class."""

    def test_builder_fluent_api(self) -> None:
        """Test builder fluent API returns self."""
        builder = ZnVaultClientBuilder()

        assert builder.base_url("https://vault.example.com") is builder
        assert builder.api_key("key") is builder
        assert builder.timeout(30) is builder
        assert builder.verify_ssl(True) is builder
        assert builder.trust_self_signed(False) is builder
        assert builder.retry_attempts(3) is builder
        assert builder.retry_delay(0.5) is builder
        assert builder.header("X-Custom", "value") is builder

    def test_builder_all_options(self) -> None:
        """Test builder with all options."""
        client = (
            ZnVaultClientBuilder()
            .base_url("https://vault.example.com")
            .api_key("test-key")
            .timeout(45)
            .verify_ssl(False)
            .trust_self_signed(True)
            .retry_attempts(5)
            .retry_delay(1.0)
            .header("X-Request-ID", "123")
            .build()
        )

        config = client.config
        assert config.base_url == "https://vault.example.com"
        assert config.api_key == "test-key"
        assert config.timeout == 45
        assert config.verify_ssl is False
        assert config.trust_self_signed is True
        assert config.retry_attempts == 5
        assert config.retry_delay == 1.0
        assert config.headers["X-Request-ID"] == "123"
