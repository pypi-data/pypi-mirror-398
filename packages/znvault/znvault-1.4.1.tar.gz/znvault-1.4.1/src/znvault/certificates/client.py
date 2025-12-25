# Path: zn-vault-sdk-python/src/znvault/certificates/client.py
"""Certificates client for ZN-Vault."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from urllib.parse import quote

from znvault.models.certificates import (
    Certificate,
    DecryptedCertificate,
    StoreCertificateRequest,
    UpdateCertificateRequest,
    RotateCertificateRequest,
    CertificateFilter,
    CertificateStats,
    CertificateAccessLogEntry,
    CertificateListResponse,
    CertificateType,
    CertificatePurpose,
)

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class CertificatesClient:
    """Client for certificate lifecycle management operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the certificates client."""
        self._http = http

    def store(
        self, request: StoreCertificateRequest, tenant_id: str | None = None
    ) -> Certificate:
        """
        Store a new certificate for custody.

        Args:
            request: The certificate storage request.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The certificate metadata.
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.post("/v1/certificates", request.to_dict(), params=params)
        return Certificate.from_dict(response)

    def get(self, certificate_id: str, tenant_id: str | None = None) -> Certificate:
        """
        Get certificate metadata by ID.

        Args:
            certificate_id: The certificate ID.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The certificate metadata.
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.get(f"/v1/certificates/{certificate_id}", params=params)
        return Certificate.from_dict(response)

    def get_by_identity(
        self,
        client_id: str,
        kind: str,
        alias: str,
        tenant_id: str | None = None,
    ) -> Certificate:
        """
        Get certificate by business identity (clientId/kind/alias).

        Args:
            client_id: External customer identifier (e.g., NIF/CIF).
            kind: Certificate kind (AEAT, FNMT, CUSTOM, etc.).
            alias: Human-readable identifier.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The certificate metadata.
        """
        encoded_client_id = quote(client_id, safe="")
        encoded_kind = quote(kind, safe="")
        encoded_alias = quote(alias, safe="")
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.get(
            f"/v1/certificates/by-identity/{encoded_client_id}/{encoded_kind}/{encoded_alias}",
            params=params,
        )
        return Certificate.from_dict(response)

    def list(
        self, filter: CertificateFilter | None = None, tenant_id: str | None = None
    ) -> CertificateListResponse:
        """
        List certificates with optional filtering.

        Args:
            filter: Optional filter parameters.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            Paginated list of certificates.
        """
        params = filter.to_params() if filter else {}
        if tenant_id:
            params["tenantId"] = tenant_id
        response = self._http.get("/v1/certificates", params=params)
        return CertificateListResponse.from_dict(response)

    def get_stats(self, tenant_id: str | None = None) -> CertificateStats:
        """
        Get certificate statistics.

        Args:
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            Statistics including counts by status and kind.
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.get("/v1/certificates/stats", params=params)
        return CertificateStats.from_dict(response)

    def list_expiring(
        self, days: int = 30, tenant_id: str | None = None
    ) -> list[Certificate]:
        """
        List certificates expiring within a specified number of days.

        Args:
            days: Number of days to look ahead (default: 30).
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            List of expiring certificates.
        """
        params: dict[str, str] = {"days": str(days)}
        if tenant_id:
            params["tenantId"] = tenant_id
        response = self._http.get("/v1/certificates/expiring", params=params)
        return [Certificate.from_dict(c) for c in response]

    def update(
        self,
        certificate_id: str,
        request: UpdateCertificateRequest,
        tenant_id: str | None = None,
    ) -> Certificate:
        """
        Update certificate metadata.

        Args:
            certificate_id: The certificate ID.
            request: The update request.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The updated certificate metadata.
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.patch(
            f"/v1/certificates/{certificate_id}", request.to_dict(), params=params
        )
        return Certificate.from_dict(response)

    def decrypt(
        self, certificate_id: str, purpose: str, tenant_id: str | None = None
    ) -> DecryptedCertificate:
        """
        Decrypt certificate (retrieve the actual certificate data).

        Requires business justification - the purpose is logged for audit.

        Args:
            certificate_id: The certificate ID.
            purpose: Business justification for accessing the certificate.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            Decrypted certificate data (base64 encoded).
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.post(
            f"/v1/certificates/{certificate_id}/decrypt",
            {"purpose": purpose},
            params=params,
        )
        return DecryptedCertificate.from_dict(response)

    def rotate(
        self,
        certificate_id: str,
        request: RotateCertificateRequest,
        tenant_id: str | None = None,
    ) -> Certificate:
        """
        Rotate certificate (replace with a new certificate).

        The old certificate is preserved in history.

        Args:
            certificate_id: The certificate ID.
            request: The rotation request with new certificate data.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The updated certificate metadata.
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        response = self._http.post(
            f"/v1/certificates/{certificate_id}/rotate",
            request.to_dict(),
            params=params,
        )
        return Certificate.from_dict(response)

    def delete(self, certificate_id: str, tenant_id: str | None = None) -> None:
        """
        Delete a certificate.

        The underlying secret data is preserved for audit purposes.

        Args:
            certificate_id: The certificate ID.
            tenant_id: Optional tenant ID (required if not in JWT).
        """
        params = {"tenantId": tenant_id} if tenant_id else {}
        self._http.delete(f"/v1/certificates/{certificate_id}", params=params)

    def get_access_log(
        self, certificate_id: str, limit: int = 100, tenant_id: str | None = None
    ) -> list[CertificateAccessLogEntry]:
        """
        Get certificate access log.

        Args:
            certificate_id: The certificate ID.
            limit: Maximum number of entries to return (default: 100).
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            Access log entries.
        """
        params: dict[str, str] = {"limit": str(limit)}
        if tenant_id:
            params["tenantId"] = tenant_id
        response = self._http.get(
            f"/v1/certificates/{certificate_id}/access-log", params=params
        )
        entries = response.get("entries", [])
        return [CertificateAccessLogEntry.from_dict(e) for e in entries]

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def store_p12(
        self,
        client_id: str,
        kind: str,
        alias: str,
        p12_data: bytes | str,
        passphrase: str,
        purpose: CertificatePurpose,
        *,
        client_name: str | None = None,
        organization_id: str | None = None,
        contact_email: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        tenant_id: str | None = None,
    ) -> Certificate:
        """
        Store a P12 certificate with simplified parameters.

        Args:
            client_id: External customer identifier (e.g., NIF/CIF).
            kind: Certificate kind (AEAT, FNMT, CUSTOM, etc.).
            alias: Human-readable identifier.
            p12_data: P12 certificate data (bytes or base64 string).
            passphrase: P12 passphrase.
            purpose: Certificate purpose.
            client_name: Optional customer display name.
            organization_id: Optional organization identifier.
            contact_email: Optional contact email.
            tags: Optional tags.
            metadata: Optional custom metadata.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The certificate metadata.
        """
        if isinstance(p12_data, bytes):
            certificate_data = base64.b64encode(p12_data).decode("utf-8")
        else:
            certificate_data = p12_data

        request = StoreCertificateRequest(
            client_id=client_id,
            kind=kind,
            alias=alias,
            certificate_data=certificate_data,
            certificate_type=CertificateType.P12,
            passphrase=passphrase,
            purpose=purpose,
            client_name=client_name,
            organization_id=organization_id,
            contact_email=contact_email,
            tags=tags or [],
            metadata=metadata or {},
        )
        return self.store(request, tenant_id)

    def store_pem(
        self,
        client_id: str,
        kind: str,
        alias: str,
        pem_data: bytes | str,
        purpose: CertificatePurpose,
        *,
        client_name: str | None = None,
        organization_id: str | None = None,
        contact_email: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        tenant_id: str | None = None,
    ) -> Certificate:
        """
        Store a PEM certificate with simplified parameters.

        Args:
            client_id: External customer identifier (e.g., NIF/CIF).
            kind: Certificate kind.
            alias: Human-readable identifier.
            pem_data: PEM certificate data (bytes or base64 string).
            purpose: Certificate purpose.
            client_name: Optional customer display name.
            organization_id: Optional organization identifier.
            contact_email: Optional contact email.
            tags: Optional tags.
            metadata: Optional custom metadata.
            tenant_id: Optional tenant ID (required if not in JWT).

        Returns:
            The certificate metadata.
        """
        if isinstance(pem_data, bytes):
            certificate_data = base64.b64encode(pem_data).decode("utf-8")
        else:
            certificate_data = pem_data

        request = StoreCertificateRequest(
            client_id=client_id,
            kind=kind,
            alias=alias,
            certificate_data=certificate_data,
            certificate_type=CertificateType.PEM,
            purpose=purpose,
            client_name=client_name,
            organization_id=organization_id,
            contact_email=contact_email,
            tags=tags or [],
            metadata=metadata or {},
        )
        return self.store(request, tenant_id)

    def list_by_client(
        self,
        client_id: str,
        tenant_id: str | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> CertificateListResponse:
        """
        List certificates by client ID.

        Args:
            client_id: The client ID to filter by.
            tenant_id: Optional tenant ID (required if not in JWT).
            page: Page number.
            page_size: Page size.

        Returns:
            Paginated list of certificates.
        """
        return self.list(
            CertificateFilter(client_id=client_id, page=page, page_size=page_size),
            tenant_id,
        )

    def list_by_kind(
        self,
        kind: str,
        tenant_id: str | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> CertificateListResponse:
        """
        List certificates by kind (AEAT, FNMT, CUSTOM, etc.).

        Args:
            kind: The kind to filter by.
            tenant_id: Optional tenant ID (required if not in JWT).
            page: Page number.
            page_size: Page size.

        Returns:
            Paginated list of certificates.
        """
        return self.list(
            CertificateFilter(kind=kind, page=page, page_size=page_size), tenant_id
        )

    def list_active(
        self,
        tenant_id: str | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> CertificateListResponse:
        """
        List active certificates only.

        Args:
            tenant_id: Optional tenant ID (required if not in JWT).
            page: Page number.
            page_size: Page size.

        Returns:
            Paginated list of active certificates.
        """
        from znvault.models.certificates import CertificateStatus

        return self.list(
            CertificateFilter(
                status=CertificateStatus.ACTIVE, page=page, page_size=page_size
            ),
            tenant_id,
        )

    def list_expired(
        self,
        tenant_id: str | None = None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> CertificateListResponse:
        """
        List expired certificates only.

        Args:
            tenant_id: Optional tenant ID (required if not in JWT).
            page: Page number.
            page_size: Page size.

        Returns:
            Paginated list of expired certificates.
        """
        from znvault.models.certificates import CertificateStatus

        return self.list(
            CertificateFilter(
                status=CertificateStatus.EXPIRED, page=page, page_size=page_size
            ),
            tenant_id,
        )

    def download(
        self, certificate_id: str, purpose: str, tenant_id: str | None = None
    ) -> bytes:
        """
        Download certificate as bytes.

        Args:
            certificate_id: The certificate ID.
            purpose: Business justification.
            tenant_id: Optional tenant ID.

        Returns:
            Certificate data as bytes.
        """
        decrypted = self.decrypt(certificate_id, purpose, tenant_id)
        return base64.b64decode(decrypted.certificate_data)
