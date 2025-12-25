# Path: zn-vault-sdk-python/src/znvault/http/client.py
"""HTTP client implementation using requests."""

import time
from typing import Any, TypeVar
import urllib3

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from znvault.config import ZnVaultConfig
from znvault.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    ZnVaultError,
)

T = TypeVar("T")


class HttpClient:
    """HTTP client for ZN-Vault API."""

    def __init__(self, config: ZnVaultConfig) -> None:
        """Initialize HTTP client with configuration."""
        self.config = config
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Disable SSL warnings if trusting self-signed certs
        if self.config.trust_self_signed:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

    def set_tokens(self, access_token: str, refresh_token: str | None = None) -> None:
        """Set authentication tokens."""
        self._access_token = access_token
        self._refresh_token = refresh_token

    def clear_tokens(self) -> None:
        """Clear authentication tokens."""
        self._access_token = None
        self._refresh_token = None

    @property
    def access_token(self) -> str | None:
        """Get current access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Get current refresh token."""
        return self._refresh_token

    def _get_headers(self, include_content_type: bool = True) -> dict[str, str]:
        """Get request headers including authentication.

        Args:
            include_content_type: Whether to include Content-Type header.
                                  Set to False for requests without body (DELETE, some GETs).
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            **self.config.headers,
        }

        if include_content_type:
            headers["Content-Type"] = "application/json"

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        elif self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        return headers

    def _get_verify(self) -> bool:
        """Get SSL verification setting."""
        if self.config.trust_self_signed:
            return False
        return self.config.verify_ssl

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code >= 200 and response.status_code < 300:
            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return response.text

        # Parse error details
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text or "Unknown error"}

        message = error_data.get("message", error_data.get("error", "Unknown error"))
        details = error_data.get("details", {})

        # Map status codes to exceptions
        if response.status_code == 400:
            fields = error_data.get("fields", {})
            raise ValidationError(message, fields=fields, details=details)
        elif response.status_code == 401:
            raise AuthenticationError(message, details=details)
        elif response.status_code == 403:
            raise AuthorizationError(message, details=details)
        elif response.status_code == 404:
            resource = error_data.get("resource", "Resource")
            resource_id = error_data.get("resourceId")
            raise NotFoundError(resource, resource_id, details=details)
        elif response.status_code == 409:
            raise ConflictError(message, details=details)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(message, retry_after=retry_seconds, details=details)
        elif response.status_code >= 500:
            raise ServerError(message, status_code=response.status_code, details=details)
        else:
            raise ZnVaultError(message, status_code=response.status_code, details=details)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        url = f"{self.config.base_url}{path}"
        response = self._session.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)

    def post(self, path: str, data: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        url = f"{self.config.base_url}{path}"
        response = self._session.post(
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)

    def put(self, path: str, data: dict[str, Any] | None = None) -> Any:
        """Make a PUT request."""
        url = f"{self.config.base_url}{path}"
        response = self._session.put(
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)

    def patch(self, path: str, data: dict[str, Any] | None = None) -> Any:
        """Make a PATCH request."""
        url = f"{self.config.base_url}{path}"
        response = self._session.patch(
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)

    def delete(self, path: str) -> Any:
        """Make a DELETE request."""
        url = f"{self.config.base_url}{path}"
        response = self._session.delete(
            url,
            headers=self._get_headers(include_content_type=False),
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)

    def get_unauthenticated(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request without authentication headers (for public endpoints)."""
        url = f"{self.config.base_url}{path}"
        headers: dict[str, str] = {
            "Accept": "application/json",
            **self.config.headers,
        }
        response = self._session.get(
            url,
            headers=headers,
            params=params,
            timeout=self.config.timeout,
            verify=self._get_verify(),
        )
        return self._handle_response(response)
