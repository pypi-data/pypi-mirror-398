# Path: zn-vault-sdk-python/src/znvault/__init__.py
"""
ZN-Vault Python SDK

A Python client library for ZN-Vault secrets management system.
"""

from znvault.client import ZnVaultClient
from znvault.config import ZnVaultConfig
from znvault.exceptions import (
    ZnVaultError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ConflictError,
    ServerError,
    ConfigurationError,
)
from znvault.models import (
    # Auth
    AuthResult,
    User,
    ApiKey,
    # Secrets
    Secret,
    SecretData,
    SecretType,
    SecretVersion,
    CreateSecretRequest,
    UpdateSecretRequest,
    SecretFilter,
    # KMS
    KmsKey,
    KeySpec,
    KeyUsage,
    KeyState,
    EncryptResult,
    DecryptResult,
    DataKeyResult,
    CreateKeyRequest,
    KeyFilter,
    # Admin
    Tenant,
    Role,
    Policy,
    PolicyDocument,
    PolicyStatement,
    PolicyEffect,
    CreateUserRequest,
    CreateTenantRequest,
    CreateRoleRequest,
    # Audit
    AuditEntry,
    AuditFilter,
    AuditVerifyResult,
    # Health
    HealthStatus,
    # Common
    Page,
)

__version__ = "1.0.0"
__all__ = [
    # Client
    "ZnVaultClient",
    "ZnVaultConfig",
    # Exceptions
    "ZnVaultError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ConflictError",
    "ServerError",
    "ConfigurationError",
    # Auth models
    "AuthResult",
    "User",
    "ApiKey",
    # Secret models
    "Secret",
    "SecretData",
    "SecretType",
    "SecretVersion",
    "CreateSecretRequest",
    "UpdateSecretRequest",
    "SecretFilter",
    # KMS models
    "KmsKey",
    "KeySpec",
    "KeyUsage",
    "KeyState",
    "EncryptResult",
    "DecryptResult",
    "DataKeyResult",
    "CreateKeyRequest",
    "KeyFilter",
    # Admin models
    "Tenant",
    "Role",
    "Policy",
    "PolicyDocument",
    "PolicyStatement",
    "PolicyEffect",
    "CreateUserRequest",
    "CreateTenantRequest",
    "CreateRoleRequest",
    # Audit models
    "AuditEntry",
    "AuditFilter",
    "AuditVerifyResult",
    # Health models
    "HealthStatus",
    # Common
    "Page",
]
