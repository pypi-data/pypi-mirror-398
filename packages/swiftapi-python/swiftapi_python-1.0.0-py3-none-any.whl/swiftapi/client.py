"""
SwiftAPI SDK - HTTP Client

This module provides the HTTP client for communicating with SwiftAPI.
"""

import requests
from typing import Dict, Any, Optional, List

from .exceptions import (
    SwiftAPIError,
    AuthenticationError,
    PolicyViolation,
    RateLimitError,
    NetworkError,
)

DEFAULT_BASE_URL = "https://swiftapi.ai"
DEFAULT_TIMEOUT = 30


class SwiftAPI:
    """
    SwiftAPI HTTP Client.

    Usage:
        api = SwiftAPI(key="swiftapi_live_...")
        result = api.verify("file_write", "Save config", {"path": "/etc/config"})
    """

    def __init__(
        self,
        key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize SwiftAPI client.

        Args:
            key: SwiftAPI authority key (swiftapi_live_...)
            base_url: API base URL (default: https://swiftapi.ai)
            timeout: Request timeout in seconds
        """
        if not key:
            raise AuthenticationError("API key is required")
        if not key.startswith("swiftapi_live_"):
            raise AuthenticationError("Invalid key format: must start with 'swiftapi_live_'")

        self.key = key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-SwiftAPI-Authority": key,
            "Content-Type": "application/json",
            "User-Agent": "swiftapi-python/1.0.0",
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Dict = None,
        params: Dict = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to SwiftAPI."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Failed to connect to SwiftAPI: {e}")
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")

        # Handle response
        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        # Rate limit
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)

        # Auth errors
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if response.status_code == 403:
            try:
                data = response.json()
                raise AuthenticationError(data.get("detail", {}).get("message", "Forbidden"))
            except ValueError:
                raise AuthenticationError("Forbidden")

        # Parse JSON
        try:
            data = response.json()
        except ValueError:
            raise SwiftAPIError(f"Invalid JSON response: {response.text[:200]}")

        # Policy violations (denied actions)
        if response.status_code == 200 and data.get("approved") is False:
            raise PolicyViolation(
                message=data.get("reason", "Action denied by policy"),
                action_type=data.get("action", {}).get("type"),
                denial_reason=data.get("reason"),
            )

        # Other errors
        if response.status_code >= 400:
            detail = data.get("detail", {})
            if isinstance(detail, dict):
                message = detail.get("message", str(detail))
            else:
                message = str(detail)
            raise SwiftAPIError(message, response.status_code, data)

        return data

    # =========================================================================
    # Core Endpoints
    # =========================================================================

    def verify(
        self,
        action_type: str,
        intent: str,
        params: Optional[Dict[str, Any]] = None,
        actor: str = "sdk",
        app_id: str = "swiftapi-python",
    ) -> Dict[str, Any]:
        """
        Submit an action for verification and get an execution attestation.

        Args:
            action_type: Type of action (e.g., "file_write", "api_call")
            intent: Human-readable description of intent
            params: Optional action parameters
            actor: Identifier for the requesting agent
            app_id: Application identifier

        Returns:
            Full verification response including execution_attestation

        Raises:
            PolicyViolation: If action is denied
            AuthenticationError: If key is invalid
            SwiftAPIError: For other errors
        """
        payload = {
            "action": {
                "type": action_type,
                "intent": intent,
                "params": params or {},
            },
            "actor": actor,
            "app_id": app_id,
        }
        return self._request("POST", "/verify", json=payload)

    def verify_attestation(self, attestation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an existing attestation with the server.

        Args:
            attestation: The execution_attestation to verify

        Returns:
            Verification result
        """
        return self._request("POST", "/attestation/verify", json=attestation)

    def revoke(self, jti: str, reason: str = "SDK revocation") -> Dict[str, Any]:
        """
        Revoke an attestation by JTI.

        Args:
            jti: The attestation's unique identifier
            reason: Reason for revocation

        Returns:
            Revocation confirmation
        """
        payload = {"jti": jti, "reason": reason}
        return self._request("POST", "/attestation/revoke", json=payload)

    def check_revocation(self, jti: str) -> bool:
        """
        Check if an attestation has been revoked.

        This is a fast check - use for real-time revocation verification.

        Args:
            jti: The attestation's unique identifier

        Returns:
            True if revoked, False if valid
        """
        try:
            result = self._request("GET", f"/attestation/revoked/{jti}")
            return result.get("revoked", False)
        except SwiftAPIError:
            # If endpoint fails, assume not revoked (fail-open for availability)
            return False

    # =========================================================================
    # Info Endpoints
    # =========================================================================

    def get_info(self) -> Dict[str, Any]:
        """Get API info and public key."""
        return self._request("GET", "/")

    def health(self) -> bool:
        """Check API health."""
        try:
            result = self._request("GET", "/health")
            return result.get("status") == "healthy"
        except Exception:
            return False

    def get_policies(self) -> List[Dict[str, Any]]:
        """Get active policies."""
        result = self._request("GET", "/policies")
        return result.get("policies", [])

    def get_scopes(self) -> List[str]:
        """Get available authority scopes."""
        result = self._request("GET", "/authority/scopes")
        return result.get("scopes", [])

    # =========================================================================
    # Key Management (Admin Only)
    # =========================================================================

    def list_keys(self) -> List[Dict[str, Any]]:
        """List authority keys (requires admin scope)."""
        result = self._request("GET", "/authority/keys")
        return result.get("keys", [])

    def create_key(
        self,
        name: str,
        scopes: List[str],
    ) -> Dict[str, Any]:
        """
        Create a new authority key (requires admin scope).

        Args:
            name: Key name
            scopes: List of scopes to grant

        Returns:
            New key details (including the key itself - shown only once!)
        """
        payload = {"name": name, "scopes": scopes}
        return self._request("POST", "/authority/keys", json=payload)

    def revoke_key(self, key_hash: str) -> Dict[str, Any]:
        """Revoke an authority key by hash."""
        return self._request("DELETE", f"/authority/keys/{key_hash}")

    # =========================================================================
    # Context Manager
    # =========================================================================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        return False
