"""
SwiftAPI SDK - Enforcement Point (The Golden Loop)

This module provides the high-level enforcement mechanism that ensures
no action executes without proper verification and attestation.

The Golden Loop:
1. API Call: client.verify() -> Get Attestation
2. Crypto Check: verifier.verify_signature() -> OFFLINE TRUTH
3. Online Check: client.check_revocation() -> ONLINE TRUTH (optional)
4. Execute: Run the protected function

If any step fails, the action is BLOCKED.
"""

from typing import Callable, Any, Dict, Optional
from functools import wraps

from .client import SwiftAPI
from .verifier import verify_signature, is_valid
from .exceptions import (
    PolicyViolation,
    SignatureVerificationError,
    AttestationRevokedError,
    AttestationExpiredError,
    SwiftAPIError,
)
from .utils import print_approved, print_denied, print_verified, print_error


class Enforcement:
    """
    SwiftAPI Enforcement Point.

    This is the "ignition key" - no action executes without verification.

    Usage:
        api = SwiftAPI(key="swiftapi_live_...")
        guard = Enforcement(api)

        # Option 1: Run with enforcement
        guard.run(
            lambda: dangerous_operation(),
            action="file_delete",
            intent="Remove temp files"
        )

        # Option 2: Decorator
        @guard.protect(action="api_call", intent="Send notification")
        def send_notification(user_id, message):
            ...
    """

    def __init__(
        self,
        client: SwiftAPI,
        paranoid: bool = False,
        verbose: bool = True,
    ):
        """
        Initialize enforcement point.

        Args:
            client: SwiftAPI client instance
            paranoid: If True, always check revocation online (slower but safer)
            verbose: If True, print status messages
        """
        self.client = client
        self.paranoid = paranoid
        self.verbose = verbose

    def run(
        self,
        func: Callable[[], Any],
        action: str,
        intent: str,
        params: Optional[Dict[str, Any]] = None,
        actor: str = "sdk",
    ) -> Any:
        """
        Execute a function with SwiftAPI enforcement.

        The function will ONLY execute if:
        1. SwiftAPI approves the action
        2. The attestation signature is valid (cryptographic proof)
        3. The attestation is not revoked (if paranoid mode)

        Args:
            func: The function to execute (takes no arguments)
            action: Action type for verification
            intent: Human-readable intent description
            params: Optional action parameters
            actor: Actor identifier

        Returns:
            The return value of func()

        Raises:
            PolicyViolation: If action is denied by policy
            SignatureVerificationError: If attestation signature is invalid
            AttestationRevokedError: If attestation was revoked
            SwiftAPIError: For other API errors
        """
        # Step 1: API Call - Get attestation
        try:
            result = self.client.verify(
                action_type=action,
                intent=intent,
                params=params,
                actor=actor,
            )
        except PolicyViolation as e:
            if self.verbose:
                print_denied(action, intent, e.denial_reason)
            raise

        # Check if approved
        if not result.get("approved"):
            reason = result.get("reason", "Unknown denial reason")
            if self.verbose:
                print_denied(action, intent, reason)
            raise PolicyViolation(
                message=f"Action denied: {reason}",
                action_type=action,
                denial_reason=reason,
            )

        attestation = result.get("execution_attestation")
        if not attestation:
            raise SwiftAPIError("No attestation in response")

        jti = attestation.get("jti")

        # Step 2: Crypto Check - OFFLINE TRUTH
        try:
            verify_signature(attestation)
            if self.verbose:
                print_verified(jti)
        except (SignatureVerificationError, AttestationExpiredError) as e:
            if self.verbose:
                print_error(str(e))
            raise

        # Step 3: Online Check - ONLINE TRUTH (optional but recommended)
        if self.paranoid:
            if self.client.check_revocation(jti):
                if self.verbose:
                    print_error(f"Attestation {jti} has been revoked")
                raise AttestationRevokedError(jti)

        # Step 4: Execute - THE ACTION RUNS
        if self.verbose:
            print_approved(action, intent)

        return func()

    def protect(
        self,
        action: str,
        intent: str,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Decorator to protect a function with SwiftAPI enforcement.

        Usage:
            @guard.protect(action="file_write", intent="Save config")
            def save_config(data):
                with open("/etc/config", "w") as f:
                    f.write(data)

        Args:
            action: Action type for verification
            intent: Human-readable intent description
            params: Optional action parameters
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.run(
                    func=lambda: func(*args, **kwargs),
                    action=action,
                    intent=intent,
                    params=params,
                    actor=func.__name__,
                )
            return wrapper
        return decorator

    def guard(
        self,
        action: str,
        intent: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> "AttestationGuard":
        """
        Context manager for guarded execution blocks.

        Usage:
            with guard.guard(action="file_delete", intent="Cleanup temp"):
                os.remove("/tmp/file.txt")

        Args:
            action: Action type for verification
            intent: Human-readable intent description
            params: Optional action parameters
        """
        return AttestationGuard(self, action, intent, params)


class AttestationGuard:
    """Context manager for guarded execution."""

    def __init__(
        self,
        enforcement: Enforcement,
        action: str,
        intent: str,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.enforcement = enforcement
        self.action = action
        self.intent = intent
        self.params = params
        self.attestation = None

    def __enter__(self):
        # Get and verify attestation before entering the block
        result = self.enforcement.client.verify(
            action_type=self.action,
            intent=self.intent,
            params=self.params,
        )

        if not result.get("approved"):
            reason = result.get("reason", "Unknown")
            if self.enforcement.verbose:
                print_denied(self.action, self.intent, reason)
            raise PolicyViolation(
                message=f"Action denied: {reason}",
                action_type=self.action,
                denial_reason=reason,
            )

        self.attestation = result.get("execution_attestation")
        verify_signature(self.attestation)

        if self.enforcement.paranoid:
            jti = self.attestation.get("jti")
            if self.enforcement.client.check_revocation(jti):
                raise AttestationRevokedError(jti)

        if self.enforcement.verbose:
            print_approved(self.action, self.intent)

        return self.attestation

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions


# Convenience function for one-off protected execution
def enforce(
    client: SwiftAPI,
    func: Callable[[], Any],
    action: str,
    intent: str,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    One-off enforcement without creating an Enforcement instance.

    Usage:
        from swiftapi import SwiftAPI, enforce

        api = SwiftAPI(key="...")
        enforce(api, lambda: rm_rf("/"), action="file_delete", intent="Nuke it")
    """
    guard = Enforcement(client)
    return guard.run(func, action, intent, params)
