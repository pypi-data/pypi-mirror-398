# Path: zn-vault-sdk-python/tests/test_exceptions.py
"""Tests for exception classes."""

import pytest
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


class TestZnVaultError:
    """Test ZnVaultError base class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = ZnVaultError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.status_code is None

    def test_error_with_status_code(self) -> None:
        """Test error with status code."""
        error = ZnVaultError("Error", status_code=500)
        assert str(error) == "[500] Error"
        assert error.status_code == 500

    def test_error_with_details(self) -> None:
        """Test error with details."""
        error = ZnVaultError("Error", details={"key": "value"})
        assert error.details == {"key": "value"}


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthenticationError()
        assert "Authentication failed" in str(error)
        assert error.status_code == 401

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = AuthenticationError("Invalid credentials")
        assert "Invalid credentials" in str(error)


class TestAuthorizationError:
    """Test AuthorizationError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthorizationError()
        assert "Access denied" in str(error)
        assert error.status_code == 403


class TestNotFoundError:
    """Test NotFoundError class."""

    def test_resource_not_found(self) -> None:
        """Test resource not found."""
        error = NotFoundError("Secret", "secret-123")
        assert "Secret 'secret-123' not found" in str(error)
        assert error.status_code == 404
        assert error.resource == "Secret"
        assert error.resource_id == "secret-123"

    def test_resource_without_id(self) -> None:
        """Test resource not found without ID."""
        error = NotFoundError("Resource")
        assert "Resource not found" in str(error)


class TestValidationError:
    """Test ValidationError class."""

    def test_basic_validation_error(self) -> None:
        """Test basic validation error."""
        error = ValidationError("Invalid input")
        assert "Invalid input" in str(error)
        assert error.status_code == 400

    def test_validation_error_with_fields(self) -> None:
        """Test validation error with field errors."""
        error = ValidationError(
            "Validation failed",
            fields={"username": "required", "password": "too short"},
        )
        error_str = str(error)
        assert "Validation failed" in error_str
        assert "username" in error_str
        assert "required" in error_str


class TestRateLimitError:
    """Test RateLimitError class."""

    def test_basic_rate_limit(self) -> None:
        """Test basic rate limit error."""
        error = RateLimitError()
        assert "Rate limit" in str(error)
        assert error.status_code == 429

    def test_rate_limit_with_retry(self) -> None:
        """Test rate limit error with retry after."""
        error = RateLimitError(retry_after=60)
        error_str = str(error)
        assert "retry after 60s" in error_str
        assert error.retry_after == 60


class TestConflictError:
    """Test ConflictError class."""

    def test_conflict_error(self) -> None:
        """Test conflict error."""
        error = ConflictError("Resource already exists")
        assert "Resource already exists" in str(error)
        assert error.status_code == 409


class TestServerError:
    """Test ServerError class."""

    def test_default_server_error(self) -> None:
        """Test default server error."""
        error = ServerError()
        assert "Server error" in str(error)
        assert error.status_code == 500

    def test_custom_status_code(self) -> None:
        """Test custom status code."""
        error = ServerError("Service unavailable", status_code=503)
        assert error.status_code == 503


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_configuration_error(self) -> None:
        """Test configuration error."""
        error = ConfigurationError("Base URL is required")
        assert "Base URL is required" in str(error)
        assert error.status_code is None
