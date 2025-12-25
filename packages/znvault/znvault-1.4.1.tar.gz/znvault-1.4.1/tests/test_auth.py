# Path: zn-vault-sdk-python/tests/test_auth.py
"""Tests for authentication client including API key rotation."""

import os
import time
import pytest
from unittest.mock import Mock, patch

from znvault.auth.client import AuthClient
from znvault.models.auth import ApiKey


class TestAuthClientApiKeys:
    """Test AuthClient API key methods."""

    @pytest.fixture
    def mock_http(self):
        """Create a mock HTTP client."""
        return Mock()

    @pytest.fixture
    def auth_client(self, mock_http):
        """Create an AuthClient with mock HTTP."""
        return AuthClient(mock_http)

    def test_create_api_key(self, auth_client, mock_http):
        """Test creating an API key."""
        mock_http.post.return_value = {
            "id": "key-123",
            "name": "test-key",
            "prefix": "znv_abc",
            "key": "znv_abc123xyz",
            "createdAt": "2024-01-01T00:00:00Z",
            "expiresAt": "2024-04-01T00:00:00Z",
        }

        result = auth_client.create_api_key("test-key", expires_in="90d")

        assert result.id == "key-123"
        assert result.name == "test-key"
        mock_http.post.assert_called_once_with(
            "/auth/api-keys",
            {"name": "test-key", "expiresIn": "90d"},
        )

    def test_list_api_keys(self, auth_client, mock_http):
        """Test listing API keys."""
        mock_http.get.return_value = {
            "keys": [
                {"id": "key-1", "name": "key1", "prefix": "znv_a"},
                {"id": "key-2", "name": "key2", "prefix": "znv_b"},
            ]
        }

        result = auth_client.list_api_keys()

        assert len(result) == 2
        assert result[0].name == "key1"
        assert result[1].name == "key2"
        mock_http.get.assert_called_once_with("/auth/api-keys")

    def test_revoke_api_key(self, auth_client, mock_http):
        """Test revoking an API key."""
        mock_http.delete.return_value = {}

        auth_client.revoke_api_key("key-123")

        mock_http.delete.assert_called_once_with("/auth/api-keys/key-123")

    def test_rotate_api_key(self, auth_client, mock_http):
        """Test rotating an API key by ID."""
        mock_http.post.return_value = {
            "id": "key-456",
            "name": "test-key",
            "prefix": "znv_xyz",
            "key": "znv_xyz789abc",
            "createdAt": "2024-01-01T00:00:00Z",
            "expiresAt": "2024-04-01T00:00:00Z",
        }

        result = auth_client.rotate_api_key("key-123")

        assert result.id == "key-456"
        assert result.key_prefix == "znv_xyz"
        mock_http.post.assert_called_once_with("/auth/api-keys/key-123/rotate", {})

    def test_get_current_api_key(self, auth_client, mock_http):
        """Test getting current API key info."""
        mock_http.get.return_value = {
            "id": "key-123",
            "name": "my-service-key",
            "prefix": "znv_abc",
            "createdAt": "2024-01-01T00:00:00Z",
            "lastUsed": "2024-01-15T00:00:00Z",
        }

        result = auth_client.get_current_api_key()

        assert result.id == "key-123"
        assert result.name == "my-service-key"
        mock_http.get.assert_called_once_with("/auth/api-keys/self")

    def test_rotate_current_api_key(self, auth_client, mock_http):
        """Test self-rotating the current API key."""
        mock_http.post.return_value = {
            "id": "key-789",
            "name": "my-service-key",
            "prefix": "znv_new",
            "key": "znv_new123abc",
            "createdAt": "2024-01-15T00:00:00Z",
            "expiresAt": "2024-04-15T00:00:00Z",
        }

        result = auth_client.rotate_current_api_key()

        assert result.id == "key-789"
        assert result.key_prefix == "znv_new"
        assert result.key == "znv_new123abc"
        mock_http.post.assert_called_once_with("/auth/api-keys/self/rotate", {})


class TestApiKeyRotationIntegration:
    """Integration tests for API key rotation (requires running server)."""

    @pytest.fixture
    def client(self):
        """Create a ZnVault client for integration tests."""
        from znvault.client import ZnVaultClient

        base_url = os.environ.get("ZN_VAULT_URL", "https://localhost:8443")
        return (
            ZnVaultClient.builder()
            .base_url(base_url)
            .trust_self_signed(True)
            .verify_ssl(False)
            .build()
        )

    @pytest.mark.integration
    def test_api_key_lifecycle(self, client):
        """Test full API key lifecycle: create, rotate, delete."""
        # Login first
        username = os.environ.get("ZN_VAULT_USER", "admin")
        password = os.environ.get("ZN_VAULT_PASS", "Admin123456#")
        client.auth.login(username, password)

        # Create a key
        key_name = f"test-key-{int(time.time())}"
        created = client.auth.create_api_key(key_name, expires_in="1d")
        assert created.key is not None
        assert created.key.startswith("znv_")

        try:
            # Rotate the key
            rotated = client.auth.rotate_api_key(created.id)
            assert rotated.key != created.key
            assert rotated.name == created.name

            # Delete the rotated key
            client.auth.revoke_api_key(rotated.id)
        except Exception:
            # Cleanup on failure
            client.auth.revoke_api_key(created.id)
            raise

    @pytest.mark.integration
    def test_self_rotation(self, client):
        """Test self-rotation of API key."""
        from znvault.client import ZnVaultClient

        # Login and create an API key
        username = os.environ.get("ZN_VAULT_USER", "admin")
        password = os.environ.get("ZN_VAULT_PASS", "Admin123456#")
        client.auth.login(username, password)

        key_name = f"self-rotate-{int(time.time())}"
        original = client.auth.create_api_key(key_name, expires_in="1d")

        try:
            # Create a client with the API key
            base_url = os.environ.get("ZN_VAULT_URL", "https://localhost:8443")
            api_key_client = (
                ZnVaultClient.builder()
                .base_url(base_url)
                .api_key(original.key)
                .trust_self_signed(True)
                .verify_ssl(False)
                .build()
            )

            # Get current key info
            current = api_key_client.auth.get_current_api_key()
            assert current.name == key_name

            # Self-rotate
            rotated = api_key_client.auth.rotate_current_api_key()
            assert rotated.key != original.key
            assert rotated.name == original.name

            # Cleanup using admin client
            client.auth.revoke_api_key(rotated.id)
        except Exception:
            # Cleanup on failure
            client.auth.revoke_api_key(original.id)
            raise
