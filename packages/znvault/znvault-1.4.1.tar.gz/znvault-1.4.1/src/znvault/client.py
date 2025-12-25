# Path: zn-vault-sdk-python/src/znvault/client.py
"""Main ZN-Vault client facade."""

from znvault.config import ZnVaultConfig
from znvault.http.client import HttpClient
from znvault.auth.client import AuthClient
from znvault.secrets.client import SecretsClient
from znvault.kms.client import KmsClient
from znvault.certificates.client import CertificatesClient
from znvault.admin.users import UsersClient
from znvault.admin.tenants import TenantsClient
from znvault.admin.roles import RolesClient
from znvault.admin.policies import PoliciesClient
from znvault.audit.client import AuditClient
from znvault.health.client import HealthClient
from znvault.exceptions import ConfigurationError


class ZnVaultClient:
    """
    Main client for interacting with ZN-Vault.

    This is the primary entry point for the SDK. It provides access to all
    ZN-Vault operations through specialized client instances.

    Example:
        >>> client = ZnVaultClient.builder()
        ...     .base_url("https://vault.example.com:8443")
        ...     .api_key("znv_xxx")
        ...     .build()
        >>> health = client.health.check()
        >>> print(health.status)
        'ok'
    """

    def __init__(self, config: ZnVaultConfig) -> None:
        """
        Initialize the ZN-Vault client.

        Args:
            config: The client configuration.
        """
        self._config = config
        self._http = HttpClient(config)

        # Initialize all sub-clients
        self._auth = AuthClient(self._http)
        self._secrets = SecretsClient(self._http)
        self._kms = KmsClient(self._http)
        self._certificates = CertificatesClient(self._http)
        self._users = UsersClient(self._http)
        self._tenants = TenantsClient(self._http)
        self._roles = RolesClient(self._http)
        self._policies = PoliciesClient(self._http)
        self._audit = AuditClient(self._http)
        self._health = HealthClient(self._http)

    @classmethod
    def builder(cls) -> "ZnVaultClientBuilder":
        """
        Create a new client builder.

        Returns:
            A new builder instance.
        """
        return ZnVaultClientBuilder()

    @classmethod
    def create(cls, base_url: str, api_key: str | None = None) -> "ZnVaultClient":
        """
        Create a client with minimal configuration.

        Args:
            base_url: The vault base URL.
            api_key: Optional API key for authentication.

        Returns:
            A configured client instance.
        """
        builder = cls.builder().base_url(base_url)
        if api_key:
            builder.api_key(api_key)
        return builder.build()

    @property
    def auth(self) -> AuthClient:
        """Get the authentication client."""
        return self._auth

    @property
    def secrets(self) -> SecretsClient:
        """Get the secrets client."""
        return self._secrets

    @property
    def kms(self) -> KmsClient:
        """Get the KMS client."""
        return self._kms

    @property
    def certificates(self) -> CertificatesClient:
        """Get the certificates client for certificate lifecycle management."""
        return self._certificates

    @property
    def users(self) -> UsersClient:
        """Get the users management client."""
        return self._users

    @property
    def tenants(self) -> TenantsClient:
        """Get the tenants management client."""
        return self._tenants

    @property
    def roles(self) -> RolesClient:
        """Get the roles management client."""
        return self._roles

    @property
    def policies(self) -> PoliciesClient:
        """Get the policies management client."""
        return self._policies

    @property
    def audit(self) -> AuditClient:
        """Get the audit client."""
        return self._audit

    @property
    def health(self) -> HealthClient:
        """Get the health client."""
        return self._health

    @property
    def config(self) -> ZnVaultConfig:
        """Get the client configuration."""
        return self._config


class ZnVaultClientBuilder:
    """Builder for ZnVaultClient instances."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._base_url: str | None = None
        self._api_key: str | None = None
        self._timeout: int = 30
        self._verify_ssl: bool = True
        self._trust_self_signed: bool = False
        self._retry_attempts: int = 3
        self._retry_delay: float = 0.5
        self._headers: dict[str, str] = {}

    def base_url(self, url: str) -> "ZnVaultClientBuilder":
        """
        Set the base URL.

        Args:
            url: The vault base URL.

        Returns:
            The builder instance.
        """
        self._base_url = url
        return self

    def api_key(self, key: str) -> "ZnVaultClientBuilder":
        """
        Set the API key.

        Args:
            key: The API key for authentication.

        Returns:
            The builder instance.
        """
        self._api_key = key
        return self

    def timeout(self, seconds: int) -> "ZnVaultClientBuilder":
        """
        Set the request timeout.

        Args:
            seconds: Timeout in seconds.

        Returns:
            The builder instance.
        """
        self._timeout = seconds
        return self

    def verify_ssl(self, verify: bool) -> "ZnVaultClientBuilder":
        """
        Set whether to verify SSL certificates.

        Args:
            verify: Whether to verify SSL.

        Returns:
            The builder instance.
        """
        self._verify_ssl = verify
        return self

    def trust_self_signed(self, trust: bool) -> "ZnVaultClientBuilder":
        """
        Set whether to trust self-signed certificates.

        Args:
            trust: Whether to trust self-signed certs.

        Returns:
            The builder instance.
        """
        self._trust_self_signed = trust
        return self

    def retry_attempts(self, attempts: int) -> "ZnVaultClientBuilder":
        """
        Set the number of retry attempts.

        Args:
            attempts: Number of retry attempts.

        Returns:
            The builder instance.
        """
        self._retry_attempts = attempts
        return self

    def retry_delay(self, delay: float) -> "ZnVaultClientBuilder":
        """
        Set the delay between retries.

        Args:
            delay: Delay in seconds.

        Returns:
            The builder instance.
        """
        self._retry_delay = delay
        return self

    def header(self, name: str, value: str) -> "ZnVaultClientBuilder":
        """
        Add a custom header.

        Args:
            name: Header name.
            value: Header value.

        Returns:
            The builder instance.
        """
        self._headers[name] = value
        return self

    def build(self) -> ZnVaultClient:
        """
        Build the client instance.

        Returns:
            A configured ZnVaultClient.

        Raises:
            ConfigurationError: If required configuration is missing.
        """
        if not self._base_url:
            raise ConfigurationError("Base URL is required")

        config = ZnVaultConfig(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
            verify_ssl=self._verify_ssl,
            trust_self_signed=self._trust_self_signed,
            retry_attempts=self._retry_attempts,
            retry_delay=self._retry_delay,
            headers=self._headers,
        )

        return ZnVaultClient(config)
