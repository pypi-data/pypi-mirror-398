# Path: zn-vault-sdk-python/src/znvault/models/secrets.py
"""Secret management models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SecretType(str, Enum):
    """Secret storage type enumeration."""

    OPAQUE = "opaque"
    CREDENTIAL = "credential"
    SETTING = "setting"


class SecretSubType(str, Enum):
    """Secret semantic sub-type enumeration."""

    # Credential sub-types
    PASSWORD = "password"
    API_KEY = "api_key"

    # Opaque sub-types
    FILE = "file"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    KEYPAIR = "keypair"
    SSH_KEY = "ssh_key"
    TOKEN = "token"
    GENERIC = "generic"
    # Public key sub-types
    RSA_PUBLIC_KEY = "rsa_public_key"
    ED25519_PUBLIC_KEY = "ed25519_public_key"
    ECDSA_PUBLIC_KEY = "ecdsa_public_key"

    # Setting sub-types
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    PROPERTIES = "properties"
    TOML = "toml"


# Mapping of sub-types to their parent types
SUB_TYPE_TO_TYPE: dict[SecretSubType, SecretType] = {
    SecretSubType.PASSWORD: SecretType.CREDENTIAL,
    SecretSubType.API_KEY: SecretType.CREDENTIAL,
    SecretSubType.FILE: SecretType.OPAQUE,
    SecretSubType.CERTIFICATE: SecretType.OPAQUE,
    SecretSubType.PRIVATE_KEY: SecretType.OPAQUE,
    SecretSubType.KEYPAIR: SecretType.OPAQUE,
    SecretSubType.SSH_KEY: SecretType.OPAQUE,
    SecretSubType.TOKEN: SecretType.OPAQUE,
    SecretSubType.GENERIC: SecretType.OPAQUE,
    SecretSubType.RSA_PUBLIC_KEY: SecretType.OPAQUE,
    SecretSubType.ED25519_PUBLIC_KEY: SecretType.OPAQUE,
    SecretSubType.ECDSA_PUBLIC_KEY: SecretType.OPAQUE,
    SecretSubType.JSON: SecretType.SETTING,
    SecretSubType.YAML: SecretType.SETTING,
    SecretSubType.ENV: SecretType.SETTING,
    SecretSubType.PROPERTIES: SecretType.SETTING,
    SecretSubType.TOML: SecretType.SETTING,
}


@dataclass
class Secret:
    """Secret metadata (not decrypted value)."""

    id: str
    alias: str
    tenant: str
    type: SecretType
    version: int
    sub_type: SecretSubType | None = None
    tags: list[str] = field(default_factory=list)
    # File metadata (queryable without decryption)
    file_name: str | None = None
    file_size: int | None = None
    file_mime: str | None = None
    file_checksum: str | None = None
    # Expiration tracking
    expires_at: datetime | None = None
    ttl_until: datetime | None = None
    # Content type (for settings)
    content_type: str | None = None
    # Audit
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Secret":
        """Create from API response dictionary."""
        secret_type = data.get("type", "opaque")
        if isinstance(secret_type, str):
            try:
                secret_type = SecretType(secret_type.lower())
            except ValueError:
                secret_type = SecretType.OPAQUE

        # Parse sub_type
        sub_type_str = data.get("subType") or data.get("sub_type")
        sub_type = None
        if sub_type_str:
            try:
                sub_type = SecretSubType(sub_type_str.lower())
            except ValueError:
                sub_type = None

        return cls(
            id=data.get("id", ""),
            alias=data.get("alias", ""),
            tenant=data.get("tenant", ""),
            type=secret_type,
            version=data.get("version", 1),
            sub_type=sub_type,
            tags=data.get("tags") or [],
            file_name=data.get("fileName") or data.get("file_name"),
            file_size=data.get("fileSize") or data.get("file_size"),
            file_mime=data.get("fileMime") or data.get("file_mime"),
            file_checksum=data.get("fileChecksum") or data.get("file_checksum"),
            expires_at=_parse_datetime(data.get("expiresAt") or data.get("expires_at")),
            ttl_until=_parse_datetime(data.get("ttlUntil") or data.get("ttl_until")),
            content_type=data.get("contentType") or data.get("content_type"),
            created_by=data.get("createdBy") or data.get("created_by"),
            created_at=_parse_datetime(data.get("createdAt") or data.get("created_at")),
            updated_at=_parse_datetime(data.get("updatedAt") or data.get("updated_at")),
        )


@dataclass
class SecretData:
    """Decrypted secret with data."""

    id: str
    alias: str
    tenant: str
    type: SecretType
    version: int
    data: dict[str, Any]
    sub_type: SecretSubType | None = None
    # File metadata
    file_name: str | None = None
    file_size: int | None = None
    file_mime: str | None = None
    file_checksum: str | None = None
    # Expiration tracking
    expires_at: datetime | None = None
    ttl_until: datetime | None = None
    # Content type
    content_type: str | None = None
    # Audit
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    decrypted_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretData":
        """Create from API response dictionary."""
        secret_type = data.get("type", "opaque")
        if isinstance(secret_type, str):
            try:
                secret_type = SecretType(secret_type.lower())
            except ValueError:
                secret_type = SecretType.OPAQUE

        # Parse sub_type
        sub_type_str = data.get("subType") or data.get("sub_type")
        sub_type = None
        if sub_type_str:
            try:
                sub_type = SecretSubType(sub_type_str.lower())
            except ValueError:
                sub_type = None

        return cls(
            id=data.get("id", ""),
            alias=data.get("alias", ""),
            tenant=data.get("tenant", ""),
            type=secret_type,
            version=data.get("version", 1),
            data=data.get("data", {}),
            sub_type=sub_type,
            file_name=data.get("fileName") or data.get("file_name"),
            file_size=data.get("fileSize") or data.get("file_size"),
            file_mime=data.get("fileMime") or data.get("file_mime"),
            file_checksum=data.get("fileChecksum") or data.get("file_checksum"),
            expires_at=_parse_datetime(data.get("expiresAt") or data.get("expires_at")),
            ttl_until=_parse_datetime(data.get("ttlUntil") or data.get("ttl_until")),
            content_type=data.get("contentType") or data.get("content_type"),
            created_by=data.get("createdBy") or data.get("created_by"),
            created_at=_parse_datetime(data.get("createdAt") or data.get("created_at")),
            updated_at=_parse_datetime(data.get("updatedAt") or data.get("updated_at")),
            decrypted_at=datetime.now(),
        )


@dataclass
class SecretVersion:
    """Secret version history entry."""

    id: int
    version: int
    tenant: str | None = None
    alias: str | None = None
    type: str | None = None
    sub_type: SecretSubType | None = None
    tags: list[str] | None = None
    # File metadata
    file_name: str | None = None
    file_size: int | None = None
    file_mime: str | None = None
    # Expiration tracking
    expires_at: datetime | None = None
    # Audit
    created_at: datetime | None = None
    created_by: str | None = None
    superseded_at: datetime | None = None
    superseded_by: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretVersion":
        """Create from API response dictionary."""
        # Parse sub_type
        sub_type_str = data.get("subType") or data.get("sub_type")
        sub_type = None
        if sub_type_str:
            try:
                sub_type = SecretSubType(sub_type_str.lower())
            except ValueError:
                sub_type = None

        return cls(
            id=data.get("id", 0),
            version=data.get("version", 1),
            tenant=data.get("tenant"),
            alias=data.get("alias"),
            type=data.get("type"),
            sub_type=sub_type,
            tags=data.get("tags"),
            file_name=data.get("fileName") or data.get("file_name"),
            file_size=data.get("fileSize") or data.get("file_size"),
            file_mime=data.get("fileMime") or data.get("file_mime"),
            expires_at=_parse_datetime(data.get("expiresAt") or data.get("expires_at")),
            created_at=_parse_datetime(data.get("createdAt") or data.get("created_at")),
            created_by=data.get("createdBy") or data.get("created_by"),
            superseded_at=_parse_datetime(
                data.get("supersededAt") or data.get("superseded_at")
            ),
            superseded_by=data.get("supersededBy") or data.get("superseded_by"),
        )


@dataclass
class CreateSecretRequest:
    """Request to create a secret."""

    alias: str
    type: SecretType
    data: dict[str, Any]
    tenant: str | None = None
    sub_type: SecretSubType | None = None
    tags: list[str] = field(default_factory=list)
    file_name: str | None = None
    expires_at: datetime | None = None
    ttl_until: datetime | None = None
    content_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {
            "alias": self.alias,
            "type": self.type.value,
            "data": self.data,
        }
        if self.tenant:
            result["tenant"] = self.tenant
        if self.sub_type:
            result["subType"] = self.sub_type.value
        if self.tags:
            result["tags"] = self.tags
        if self.file_name:
            result["fileName"] = self.file_name
        if self.expires_at:
            result["expiresAt"] = self.expires_at.isoformat()
        if self.ttl_until:
            result["ttlUntil"] = self.ttl_until.isoformat()
        if self.content_type:
            result["contentType"] = self.content_type
        return result


@dataclass
class UpdateSecretRequest:
    """Request to update a secret."""

    data: dict[str, Any]
    sub_type: SecretSubType | None = None
    tags: list[str] | None = None
    file_name: str | None = None
    expires_at: datetime | None = None
    ttl_until: datetime | None = None
    content_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {"data": self.data}
        if self.sub_type:
            result["subType"] = self.sub_type.value
        if self.tags is not None:
            result["tags"] = self.tags
        if self.file_name:
            result["fileName"] = self.file_name
        if self.expires_at:
            result["expiresAt"] = self.expires_at.isoformat()
        if self.ttl_until:
            result["ttlUntil"] = self.ttl_until.isoformat()
        if self.content_type:
            result["contentType"] = self.content_type
        return result


@dataclass
class SecretFilter:
    """Filter options for listing secrets."""

    type: SecretType | None = None
    sub_type: SecretSubType | None = None
    file_mime: str | None = None
    expiring_before: datetime | None = None
    alias_prefix: str | None = None
    tags: list[str] | None = None
    page: int = 1
    page_size: int = 100

    def to_params(self) -> dict[str, Any]:
        """Convert to query parameters."""
        params: dict[str, Any] = {
            "page": self.page,
            "pageSize": self.page_size,
        }
        if self.type:
            params["type"] = self.type.value
        if self.sub_type:
            params["subType"] = self.sub_type.value
        if self.file_mime:
            params["fileMime"] = self.file_mime
        if self.expiring_before:
            params["expiringBefore"] = self.expiring_before.isoformat()
        if self.alias_prefix:
            params["aliasPrefix"] = self.alias_prefix
        if self.tags:
            params["tags"] = ",".join(self.tags)
        return params


@dataclass
class GenerateKeypairRequest:
    """Request to generate a cryptographic keypair."""

    algorithm: str  # 'RSA' | 'Ed25519' | 'ECDSA'
    alias: str
    tenant: str
    rsa_bits: int | None = None  # 2048 | 4096 for RSA
    ecdsa_curve: str | None = None  # 'P-256' | 'P-384' for ECDSA
    comment: str | None = None
    publish_public_key: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request dictionary."""
        result: dict[str, Any] = {
            "algorithm": self.algorithm,
            "alias": self.alias,
            "tenant": self.tenant,
        }
        if self.rsa_bits is not None:
            result["rsaBits"] = self.rsa_bits
        if self.ecdsa_curve is not None:
            result["ecdsaCurve"] = self.ecdsa_curve
        if self.comment is not None:
            result["comment"] = self.comment
        if self.publish_public_key:
            result["publishPublicKey"] = self.publish_public_key
        if self.tags:
            result["tags"] = self.tags
        return result


@dataclass
class PublicKeyInfo:
    """Public key information."""

    id: str
    alias: str
    is_public: bool
    fingerprint: str
    algorithm: str
    public_key_pem: str
    public_key_openssh: str
    bits: int | None = None
    tenant: str | None = None
    sub_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublicKeyInfo":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            alias=data.get("alias", ""),
            is_public=data.get("isPublic", False),
            fingerprint=data.get("fingerprint", ""),
            algorithm=data.get("algorithm", ""),
            public_key_pem=data.get("publicKeyPem", ""),
            public_key_openssh=data.get("publicKeyOpenSSH", ""),
            bits=data.get("bits"),
            tenant=data.get("tenant"),
            sub_type=data.get("subType") or data.get("sub_type"),
        )


@dataclass
class GeneratedKeypair:
    """Generated cryptographic keypair response."""

    private_key: Secret
    public_key: PublicKeyInfo

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedKeypair":
        """Create from API response dictionary."""
        return cls(
            private_key=Secret.from_dict(data.get("privateKey", {})),
            public_key=PublicKeyInfo.from_dict(data.get("publicKey", {})),
        )


@dataclass
class PublishResult:
    """Result of publishing a public key."""

    message: str
    public_url: str
    fingerprint: str
    algorithm: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublishResult":
        """Create from API response dictionary."""
        return cls(
            message=data.get("message", ""),
            public_url=data.get("publicUrl", ""),
            fingerprint=data.get("fingerprint", ""),
            algorithm=data.get("algorithm", ""),
        )


@dataclass
class PublicKeyListItem:
    """Public key list item."""

    id: str
    alias: str
    tenant: str
    sub_type: str
    public_key: str
    fingerprint: str
    algorithm: str
    bits: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublicKeyListItem":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            alias=data.get("alias", ""),
            tenant=data.get("tenant", ""),
            sub_type=data.get("subType", ""),
            public_key=data.get("publicKey", ""),
            fingerprint=data.get("fingerprint", ""),
            algorithm=data.get("algorithm", ""),
            bits=data.get("bits"),
        )


@dataclass
class PublicKeyList:
    """List of public keys for a tenant."""

    tenant: str
    keys: list[PublicKeyListItem]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PublicKeyList":
        """Create from API response dictionary."""
        keys_data = data.get("keys", [])
        return cls(
            tenant=data.get("tenant", ""),
            keys=[PublicKeyListItem.from_dict(k) for k in keys_data],
        )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
