# Path: zn-vault-sdk-python/src/znvault/config.py
"""ZN-Vault client configuration."""

from dataclasses import dataclass, field
from typing import Any

from znvault.exceptions import ConfigurationError


@dataclass
class ZnVaultConfig:
    """Configuration for ZN-Vault client."""

    base_url: str
    api_key: str | None = None
    timeout: int = 30
    verify_ssl: bool = True
    trust_self_signed: bool = False
    retry_attempts: int = 3
    retry_delay: float = 0.5
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.base_url:
            raise ConfigurationError("Base URL is required")
        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")

    class Builder:
        """Builder for ZnVaultConfig."""

        def __init__(self) -> None:
            self._base_url: str | None = None
            self._api_key: str | None = None
            self._timeout: int = 30
            self._verify_ssl: bool = True
            self._trust_self_signed: bool = False
            self._retry_attempts: int = 3
            self._retry_delay: float = 0.5
            self._headers: dict[str, str] = {}

        def base_url(self, url: str) -> "ZnVaultConfig.Builder":
            """Set the base URL."""
            self._base_url = url
            return self

        def api_key(self, key: str) -> "ZnVaultConfig.Builder":
            """Set the API key."""
            self._api_key = key
            return self

        def timeout(self, seconds: int) -> "ZnVaultConfig.Builder":
            """Set the request timeout in seconds."""
            self._timeout = seconds
            return self

        def verify_ssl(self, verify: bool) -> "ZnVaultConfig.Builder":
            """Set whether to verify SSL certificates."""
            self._verify_ssl = verify
            return self

        def trust_self_signed(self, trust: bool) -> "ZnVaultConfig.Builder":
            """Set whether to trust self-signed certificates."""
            self._trust_self_signed = trust
            return self

        def retry_attempts(self, attempts: int) -> "ZnVaultConfig.Builder":
            """Set the number of retry attempts."""
            self._retry_attempts = attempts
            return self

        def retry_delay(self, delay: float) -> "ZnVaultConfig.Builder":
            """Set the delay between retries in seconds."""
            self._retry_delay = delay
            return self

        def header(self, name: str, value: str) -> "ZnVaultConfig.Builder":
            """Add a custom header."""
            self._headers[name] = value
            return self

        def build(self) -> "ZnVaultConfig":
            """Build the configuration."""
            if not self._base_url:
                raise ConfigurationError("Base URL is required")

            return ZnVaultConfig(
                base_url=self._base_url,
                api_key=self._api_key,
                timeout=self._timeout,
                verify_ssl=self._verify_ssl,
                trust_self_signed=self._trust_self_signed,
                retry_attempts=self._retry_attempts,
                retry_delay=self._retry_delay,
                headers=self._headers,
            )
