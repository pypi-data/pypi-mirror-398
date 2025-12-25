# Path: zn-vault-sdk-python/src/znvault/models/certificates.py
"""Certificate models for ZN-Vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CertificateType(str, Enum):
    """Certificate format types."""

    P12 = "P12"
    PEM = "PEM"
    DER = "DER"


class CertificatePurpose(str, Enum):
    """Certificate purpose/usage."""

    TLS = "TLS"
    MTLS = "mTLS"
    SIGNING = "SIGNING"
    ENCRYPTION = "ENCRYPTION"
    AUTHENTICATION = "AUTHENTICATION"


class CertificateStatus(str, Enum):
    """Certificate lifecycle status."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"
    PENDING_DELETION = "PENDING_DELETION"


class CertificateKind(str, Enum):
    """Certificate kind/category."""

    AEAT = "AEAT"
    FNMT = "FNMT"
    CAMERFIRMA = "CAMERFIRMA"
    CUSTOM = "CUSTOM"


@dataclass
class Certificate:
    """Certificate metadata (without encrypted data)."""

    id: str
    tenant_id: str
    client_id: str
    kind: str
    alias: str
    certificate_type: CertificateType
    purpose: CertificatePurpose
    fingerprint_sha256: str
    subject_cn: str
    issuer_cn: str
    not_before: datetime
    not_after: datetime
    client_name: str
    status: CertificateStatus
    version: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    access_count: int
    tags: list[str]
    days_until_expiry: int
    is_expired: bool
    organization_id: str | None = None
    contact_email: str | None = None
    last_accessed_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Certificate":
        """Create a Certificate from a dictionary."""
        return cls(
            id=data["id"],
            tenant_id=data["tenantId"],
            client_id=data["clientId"],
            kind=data["kind"],
            alias=data["alias"],
            certificate_type=CertificateType(data["certificateType"]),
            purpose=CertificatePurpose(data["purpose"]),
            fingerprint_sha256=data["fingerprintSha256"],
            subject_cn=data["subjectCn"],
            issuer_cn=data["issuerCn"],
            not_before=datetime.fromisoformat(data["notBefore"].replace("Z", "+00:00")),
            not_after=datetime.fromisoformat(data["notAfter"].replace("Z", "+00:00")),
            client_name=data["clientName"],
            organization_id=data.get("organizationId"),
            contact_email=data.get("contactEmail"),
            status=CertificateStatus(data["status"]),
            version=data["version"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            created_by=data["createdBy"],
            updated_at=datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00")),
            last_accessed_at=(
                datetime.fromisoformat(data["lastAccessedAt"].replace("Z", "+00:00"))
                if data.get("lastAccessedAt")
                else None
            ),
            access_count=data["accessCount"],
            tags=data.get("tags", []),
            days_until_expiry=data["daysUntilExpiry"],
            is_expired=data["isExpired"],
        )


@dataclass
class DecryptedCertificate:
    """Decrypted certificate response."""

    id: str
    certificate_data: str
    certificate_type: CertificateType
    fingerprint_sha256: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecryptedCertificate":
        """Create a DecryptedCertificate from a dictionary."""
        return cls(
            id=data["id"],
            certificate_data=data["certificateData"],
            certificate_type=CertificateType(data["certificateType"]),
            fingerprint_sha256=data["fingerprintSha256"],
        )


@dataclass
class StoreCertificateRequest:
    """Request to store a new certificate."""

    client_id: str
    kind: str
    alias: str
    certificate_data: str
    certificate_type: CertificateType
    purpose: CertificatePurpose
    passphrase: str | None = None
    client_name: str | None = None
    organization_id: str | None = None
    contact_email: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {
            "clientId": self.client_id,
            "kind": self.kind,
            "alias": self.alias,
            "certificateData": self.certificate_data,
            "certificateType": self.certificate_type.value,
            "purpose": self.purpose.value,
        }
        if self.passphrase:
            result["passphrase"] = self.passphrase
        if self.client_name:
            result["clientName"] = self.client_name
        if self.organization_id:
            result["organizationId"] = self.organization_id
        if self.contact_email:
            result["contactEmail"] = self.contact_email
        if self.tags:
            result["tags"] = self.tags
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class UpdateCertificateRequest:
    """Request to update certificate metadata."""

    alias: str | None = None
    client_name: str | None = None
    contact_email: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {}
        if self.alias is not None:
            result["alias"] = self.alias
        if self.client_name is not None:
            result["clientName"] = self.client_name
        if self.contact_email is not None:
            result["contactEmail"] = self.contact_email
        if self.tags is not None:
            result["tags"] = self.tags
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result


@dataclass
class RotateCertificateRequest:
    """Request to rotate a certificate."""

    certificate_data: str
    certificate_type: CertificateType
    passphrase: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        result: dict[str, Any] = {
            "certificateData": self.certificate_data,
            "certificateType": self.certificate_type.value,
        }
        if self.passphrase:
            result["passphrase"] = self.passphrase
        if self.reason:
            result["reason"] = self.reason
        return result


@dataclass
class CertificateFilter:
    """Filter options for listing certificates."""

    client_id: str | None = None
    kind: str | None = None
    status: CertificateStatus | None = None
    expiring_before: datetime | None = None
    tags: list[str] | None = None
    page: int = 1
    page_size: int = 20

    def to_params(self) -> dict[str, str]:
        """Convert to query parameters."""
        params: dict[str, str] = {}
        if self.client_id:
            params["clientId"] = self.client_id
        if self.kind:
            params["kind"] = self.kind
        if self.status:
            params["status"] = self.status.value
        if self.expiring_before:
            params["expiringBefore"] = self.expiring_before.isoformat()
        if self.tags:
            params["tags"] = ",".join(self.tags)
        params["page"] = str(self.page)
        params["pageSize"] = str(self.page_size)
        return params


@dataclass
class CertificateStats:
    """Certificate statistics."""

    total: int
    by_status: dict[str, int]
    by_kind: dict[str, int]
    expiring_in_30_days: int
    expiring_in_7_days: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateStats":
        """Create from a dictionary."""
        return cls(
            total=data["total"],
            by_status=data.get("byStatus", {}),
            by_kind=data.get("byKind", {}),
            expiring_in_30_days=data.get("expiringIn30Days", 0),
            expiring_in_7_days=data.get("expiringIn7Days", 0),
        )


@dataclass
class CertificateAccessLogEntry:
    """Certificate access log entry."""

    id: int
    certificate_id: str
    tenant_id: str
    purpose: str
    operation: str
    accessed_at: datetime
    success: bool
    user_id: str | None = None
    api_key_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    error_message: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateAccessLogEntry":
        """Create from a dictionary."""
        return cls(
            id=data["id"],
            certificate_id=data["certificateId"],
            tenant_id=data["tenantId"],
            user_id=data.get("userId"),
            api_key_id=data.get("apiKeyId"),
            purpose=data["purpose"],
            operation=data["operation"],
            ip_address=data.get("ipAddress"),
            user_agent=data.get("userAgent"),
            accessed_at=datetime.fromisoformat(data["accessedAt"].replace("Z", "+00:00")),
            success=data["success"],
            error_message=data.get("errorMessage"),
        )


@dataclass
class CertificateListResponse:
    """Paginated list response for certificates."""

    items: list[Certificate]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CertificateListResponse":
        """Create from a dictionary."""
        return cls(
            items=[Certificate.from_dict(item) for item in data.get("items", [])],
            total=data.get("total", 0),
            page=data.get("page", 1),
            page_size=data.get("pageSize", 20),
        )
