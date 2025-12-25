# Path: zn-vault-sdk-python/src/znvault/health/client.py
"""Health client for ZN-Vault."""

from typing import TYPE_CHECKING

from znvault.models.health import HealthStatus

if TYPE_CHECKING:
    from znvault.http.client import HttpClient


class HealthClient:
    """Client for health check operations."""

    def __init__(self, http: "HttpClient") -> None:
        """Initialize the health client."""
        self._http = http

    def check(self) -> HealthStatus:
        """
        Check the health status of the vault.

        Returns:
            The health status.
        """
        response = self._http.get("/v1/health")
        return HealthStatus.from_dict(response)

    def is_healthy(self) -> bool:
        """
        Quick check if the vault is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            status = self.check()
            return status.is_healthy
        except Exception:
            return False

    def ready(self) -> bool:
        """
        Check if the vault is ready to accept requests.

        Returns:
            True if ready, False otherwise.
        """
        try:
            response = self._http.get("/v1/health/ready")
            return response.get("ready", False) if response else False
        except Exception:
            return False

    def live(self) -> bool:
        """
        Check if the vault process is alive (liveness probe).

        Returns:
            True if alive, False otherwise.
        """
        try:
            response = self._http.get("/v1/health/live")
            return response.get("live", True) if response else True
        except Exception:
            return False
