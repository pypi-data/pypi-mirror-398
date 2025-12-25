# Path: zn-vault-sdk-python/src/znvault/models/kms.py
"""KMS (Key Management Service) models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KeySpec(str, Enum):
    """Key specification enumeration."""

    AES_256 = "AES_256"
    AES_128 = "AES_128"
    RSA_2048 = "RSA_2048"
    RSA_3072 = "RSA_3072"
    RSA_4096 = "RSA_4096"
    ECC_NIST_P256 = "ECC_NIST_P256"
    ECC_NIST_P384 = "ECC_NIST_P384"


class KeyUsage(str, Enum):
    """Key usage enumeration."""

    ENCRYPT_DECRYPT = "ENCRYPT_DECRYPT"
    SIGN_VERIFY = "SIGN_VERIFY"
    GENERATE_DATA_KEY = "GENERATE_DATA_KEY"


class KeyState(str, Enum):
    """Key state enumeration."""

    ENABLED = "Enabled"
    DISABLED = "Disabled"
    PENDING_DELETION = "PendingDeletion"
    PENDING_IMPORT = "PendingImport"


@dataclass
class KmsKey:
    """KMS key metadata."""

    key_id: str
    alias: str | None = None
    description: str | None = None
    key_spec: KeySpec = KeySpec.AES_256
    usage: KeyUsage = KeyUsage.ENCRYPT_DECRYPT
    state: KeyState = KeyState.ENABLED
    tenant: str | None = None
    version: int = 1
    rotation_enabled: bool = False
    rotation_days: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deletion_date: datetime | None = None
    next_rotation_date: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KmsKey":
        """Create from API response dictionary."""
        key_spec = data.get("keySpec", "AES_256")
        if isinstance(key_spec, str):
            try:
                key_spec = KeySpec(key_spec)
            except ValueError:
                key_spec = KeySpec.AES_256

        usage = data.get("usage", "ENCRYPT_DECRYPT")
        if isinstance(usage, str):
            try:
                usage = KeyUsage(usage)
            except ValueError:
                usage = KeyUsage.ENCRYPT_DECRYPT

        state = data.get("state", "Enabled")
        if isinstance(state, str):
            try:
                state = KeyState(state)
            except ValueError:
                state = KeyState.ENABLED

        return cls(
            key_id=data.get("keyId", data.get("id", "")),
            alias=data.get("alias"),
            description=data.get("description"),
            key_spec=key_spec,
            usage=usage,
            state=state,
            tenant=data.get("tenant"),
            version=data.get("version", 1),
            rotation_enabled=data.get("rotationEnabled", False),
            rotation_days=data.get("rotationDays"),
            created_at=_parse_datetime(data.get("createdAt")),
            updated_at=_parse_datetime(data.get("updatedAt")),
            deletion_date=_parse_datetime(data.get("deletionDate")),
            next_rotation_date=_parse_datetime(data.get("nextRotationDate")),
        )


@dataclass
class EncryptResult:
    """Result of encryption operation."""

    ciphertext: str  # Base64-encoded ciphertext
    key_id: str
    key_version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptResult":
        """Create from API response dictionary."""
        return cls(
            ciphertext=data.get("ciphertext", ""),
            key_id=data.get("keyId", ""),
            key_version=data.get("keyVersion", 1),
        )


@dataclass
class DecryptResult:
    """Result of decryption operation."""

    plaintext: str  # Base64-encoded plaintext
    key_id: str
    key_version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecryptResult":
        """Create from API response dictionary."""
        return cls(
            plaintext=data.get("plaintext", ""),
            key_id=data.get("keyId", ""),
            key_version=data.get("keyVersion", 1),
        )


@dataclass
class DataKeyResult:
    """Result of data key generation."""

    plaintext: str  # Base64-encoded plaintext data key
    ciphertext: str  # Base64-encoded encrypted data key
    key_id: str
    key_version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataKeyResult":
        """Create from API response dictionary."""
        return cls(
            plaintext=data.get("plaintext", ""),
            ciphertext=data.get("ciphertext", data.get("ciphertextBlob", "")),
            key_id=data.get("keyId", ""),
            key_version=data.get("keyVersion", 1),
        )


@dataclass
class CreateKeyRequest:
    """Request to create a KMS key."""

    alias: str
    tenant: str
    description: str | None = None
    usage: KeyUsage = KeyUsage.ENCRYPT_DECRYPT
    key_spec: KeySpec = KeySpec.AES_256
    rotation_enabled: bool = False
    rotation_days: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {
            "alias": self.alias,
            "tenant": self.tenant,
            "usage": self.usage.value,
            "keySpec": self.key_spec.value,
        }
        if self.description:
            result["description"] = self.description
        if self.rotation_enabled:
            result["rotationEnabled"] = True
        if self.rotation_days:
            result["rotationDays"] = self.rotation_days
        return result


@dataclass
class KeyFilter:
    """Filter options for listing KMS keys."""

    tenant: str | None = None
    state: KeyState | None = None
    usage: KeyUsage | None = None
    limit: int = 100
    offset: int = 0
    marker: str | None = None

    def to_params(self) -> dict[str, Any]:
        """Convert to query parameters."""
        params: dict[str, Any] = {
            "limit": self.limit,
            "offset": self.offset,
        }
        if self.tenant:
            params["tenant"] = self.tenant
        if self.state:
            params["state"] = self.state.value
        if self.usage:
            params["usage"] = self.usage.value
        if self.marker:
            params["marker"] = self.marker
        return params


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
