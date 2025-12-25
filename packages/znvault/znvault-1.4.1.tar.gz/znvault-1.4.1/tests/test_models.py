# Path: zn-vault-sdk-python/tests/test_models.py
"""Tests for model classes."""

import json
import pytest
from datetime import datetime

from znvault.models import (
    # Auth
    AuthResult,
    User,
    ApiKey,
    # Secrets
    Secret,
    SecretData,
    SecretType,
    CreateSecretRequest,
    SecretFilter,
    # KMS
    KmsKey,
    KeySpec,
    KeyUsage,
    KeyState,
    CreateKeyRequest,
    EncryptResult,
    # Admin
    Tenant,
    Role,
    PolicyDocument,
    PolicyStatement,
    PolicyEffect,
    # Audit
    AuditEntry,
    AuditVerifyResult,
    # Health
    HealthStatus,
    # Common
    Page,
)


class TestAuthModels:
    """Test authentication models."""

    def test_auth_result_from_dict(self) -> None:
        """Test AuthResult parsing."""
        data = {
            "accessToken": "access123",
            "refreshToken": "refresh456",
            "expiresIn": 3600,
            "tokenType": "Bearer",
        }
        result = AuthResult.from_dict(data)

        assert result.access_token == "access123"
        assert result.refresh_token == "refresh456"
        assert result.expires_in == 3600
        assert result.token_type == "Bearer"

    def test_user_from_dict(self) -> None:
        """Test User parsing."""
        data = {
            "id": "user-123",
            "username": "alice",
            "email": "alice@example.com",
            "role": "admin",
            "tenantId": "acme",
            "totpEnabled": True,
        }
        user = User.from_dict(data)

        assert user.id == "user-123"
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.role == "admin"
        assert user.tenant_id == "acme"
        assert user.totp_enabled is True

    def test_api_key_from_dict(self) -> None:
        """Test ApiKey parsing."""
        data = {
            "id": "key-123",
            "name": "my-key",
            "keyPrefix": "znv_",
            "key": "znv_full_key_value",
        }
        key = ApiKey.from_dict(data)

        assert key.id == "key-123"
        assert key.name == "my-key"
        assert key.key_prefix == "znv_"
        assert key.key == "znv_full_key_value"


class TestSecretModels:
    """Test secret models."""

    def test_secret_type_enum(self) -> None:
        """Test SecretType enum values."""
        assert SecretType.OPAQUE.value == "opaque"
        assert SecretType.CREDENTIAL.value == "credential"
        assert SecretType.SETTING.value == "setting"

    def test_secret_from_dict(self) -> None:
        """Test Secret parsing."""
        data = {
            "id": "secret-123",
            "alias": "api/prod/db-creds",
            "tenant": "acme",
            "type": "credential",
            "version": 2,
            "tags": ["production", "database"],
        }
        secret = Secret.from_dict(data)

        assert secret.id == "secret-123"
        assert secret.alias == "api/prod/db-creds"
        assert secret.tenant == "acme"
        assert secret.type == SecretType.CREDENTIAL
        assert secret.version == 2
        assert secret.tags == ["production", "database"]

    def test_secret_data_from_dict(self) -> None:
        """Test SecretData parsing."""
        data = {
            "data": {"username": "user", "password": "pass"},
            "version": 1,
        }
        secret_data = SecretData.from_dict(data)

        assert secret_data.data["username"] == "user"
        assert secret_data.data["password"] == "pass"
        assert secret_data.version == 1

    def test_create_secret_request_to_dict(self) -> None:
        """Test CreateSecretRequest serialization."""
        request = CreateSecretRequest(
            alias="api/prod/key",
            type=SecretType.CREDENTIAL,
            data={"key": "value"},
            tags=["test"],
        )
        result = request.to_dict()

        assert result["alias"] == "api/prod/key"
        assert result["type"] == "credential"
        assert result["data"]["key"] == "value"
        assert result["tags"] == ["test"]

    def test_secret_filter_to_params(self) -> None:
        """Test SecretFilter query param generation."""
        filter = SecretFilter(
            type=SecretType.CREDENTIAL,
            tags=["test"],
            limit=50,
        )
        params = filter.to_params()

        assert params["type"] == "credential"
        assert params["tags"] == "test"
        assert params["limit"] == 50


class TestKmsModels:
    """Test KMS models."""

    def test_key_spec_enum(self) -> None:
        """Test KeySpec enum values."""
        assert KeySpec.AES_256.value == "AES_256"
        assert KeySpec.AES_128.value == "AES_128"
        assert KeySpec.RSA_2048.value == "RSA_2048"

    def test_key_usage_enum(self) -> None:
        """Test KeyUsage enum values."""
        assert KeyUsage.ENCRYPT_DECRYPT.value == "ENCRYPT_DECRYPT"
        assert KeyUsage.SIGN_VERIFY.value == "SIGN_VERIFY"
        assert KeyUsage.GENERATE_DATA_KEY.value == "GENERATE_DATA_KEY"

    def test_kms_key_from_dict(self) -> None:
        """Test KmsKey parsing."""
        data = {
            "keyId": "key-123",
            "alias": "alias/my-key",
            "description": "Test key",
            "keySpec": "AES_256",
            "usage": "ENCRYPT_DECRYPT",
            "state": "Enabled",
            "version": 1,
        }
        key = KmsKey.from_dict(data)

        assert key.key_id == "key-123"
        assert key.alias == "alias/my-key"
        assert key.description == "Test key"
        assert key.key_spec == KeySpec.AES_256
        assert key.usage == KeyUsage.ENCRYPT_DECRYPT
        assert key.state == KeyState.ENABLED

    def test_create_key_request_to_dict(self) -> None:
        """Test CreateKeyRequest serialization."""
        request = CreateKeyRequest(
            alias="alias/test-key",
            tenant="acme",
            description="Test key",
            usage=KeyUsage.ENCRYPT_DECRYPT,
            key_spec=KeySpec.AES_256,
            rotation_enabled=True,
            rotation_days=90,
        )
        result = request.to_dict()

        assert result["alias"] == "alias/test-key"
        assert result["tenant"] == "acme"
        assert result["description"] == "Test key"
        assert result["usage"] == "ENCRYPT_DECRYPT"
        assert result["keySpec"] == "AES_256"
        assert result["rotationEnabled"] is True
        assert result["rotationDays"] == 90

    def test_encrypt_result_from_dict(self) -> None:
        """Test EncryptResult parsing."""
        data = {
            "ciphertext": "base64encodeddata",
            "keyId": "key-123",
            "keyVersion": 1,
        }
        result = EncryptResult.from_dict(data)

        assert result.ciphertext == "base64encodeddata"
        assert result.key_id == "key-123"
        assert result.key_version == 1


class TestAdminModels:
    """Test admin models."""

    def test_tenant_from_dict(self) -> None:
        """Test Tenant parsing."""
        data = {
            "id": "tenant-123",
            "name": "acme",
            "displayName": "ACME Corp",
            "description": "Test tenant",
            "enabled": True,
        }
        tenant = Tenant.from_dict(data)

        assert tenant.id == "tenant-123"
        assert tenant.name == "acme"
        assert tenant.display_name == "ACME Corp"
        assert tenant.description == "Test tenant"
        assert tenant.enabled is True

    def test_role_from_dict(self) -> None:
        """Test Role parsing."""
        data = {
            "id": "role-123",
            "name": "SecretManager",
            "description": "Manages secrets",
            "permissions": ["secret:read", "secret:write"],
            "isSystem": False,
        }
        role = Role.from_dict(data)

        assert role.id == "role-123"
        assert role.name == "SecretManager"
        assert role.permissions == ["secret:read", "secret:write"]
        assert role.is_system is False

    def test_policy_document_to_json(self) -> None:
        """Test PolicyDocument JSON serialization."""
        document = PolicyDocument(
            statements=[
                PolicyStatement(
                    effect=PolicyEffect.ALLOW,
                    actions=["secret:read:*"],
                    resources=["secret:acme/*"],
                )
            ]
        )
        json_str = document.to_json()
        parsed = json.loads(json_str)

        assert parsed["statements"][0]["effect"] == "Allow"
        assert "secret:read:*" in parsed["statements"][0]["actions"]

    def test_policy_effect_enum(self) -> None:
        """Test PolicyEffect enum values."""
        assert PolicyEffect.ALLOW.value == "Allow"
        assert PolicyEffect.DENY.value == "Deny"


class TestAuditModels:
    """Test audit models."""

    def test_audit_entry_from_dict(self) -> None:
        """Test AuditEntry parsing."""
        data = {
            "id": "audit-123",
            "timestamp": "2024-01-01T00:00:00Z",
            "action": "secret:read",
            "actor": "alice",
            "result": "success",
        }
        entry = AuditEntry.from_dict(data)

        assert entry.id == "audit-123"
        assert entry.action == "secret:read"
        assert entry.actor == "alice"
        assert entry.result == "success"

    def test_audit_verify_result_from_dict(self) -> None:
        """Test AuditVerifyResult parsing."""
        data = {
            "valid": True,
            "entriesVerified": 100,
            "firstEntryId": "entry-1",
            "lastEntryId": "entry-100",
        }
        result = AuditVerifyResult.from_dict(data)

        assert result.valid is True
        assert result.entries_verified == 100
        assert result.first_entry_id == "entry-1"
        assert result.last_entry_id == "entry-100"


class TestHealthModels:
    """Test health models."""

    def test_health_status_from_dict(self) -> None:
        """Test HealthStatus parsing."""
        data = {
            "status": "ok",
            "version": "1.0.0",
            "uptime": 3600,
        }
        status = HealthStatus.from_dict(data)

        assert status.status == "ok"
        assert status.version == "1.0.0"
        assert status.uptime == 3600
        assert status.is_healthy is True

    def test_health_status_unhealthy(self) -> None:
        """Test unhealthy status detection."""
        data = {"status": "error"}
        status = HealthStatus.from_dict(data)

        assert status.is_healthy is False


class TestPageModel:
    """Test Page generic model."""

    def test_page_has_more(self) -> None:
        """Test hasMore calculation."""
        page_with_more = Page(
            items=["a", "b", "c"],
            total=10,
            limit=3,
            offset=0,
        )
        assert page_with_more.has_more is True

        last_page = Page(
            items=["a"],
            total=10,
            limit=3,
            offset=9,
        )
        assert last_page.has_more is False
