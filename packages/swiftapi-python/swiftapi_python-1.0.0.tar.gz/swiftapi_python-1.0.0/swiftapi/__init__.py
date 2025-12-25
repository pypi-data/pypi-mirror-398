"""
SwiftAPI Python SDK

No AI action executes without verification.

Usage:
    from swiftapi import SwiftAPI, Enforcement

    # Initialize client
    api = SwiftAPI(key="swiftapi_live_...")

    # Create enforcement point
    guard = Enforcement(api)

    # Protect dangerous operations
    guard.run(
        lambda: os.system("rm -rf /tmp/data"),
        action="file_delete",
        intent="Cleanup temporary data"
    )

    # Or use decorator
    @guard.protect(action="api_call", intent="Send email")
    def send_email(to, subject, body):
        ...

    # Or use context manager
    with guard.guard(action="database_write", intent="Update user"):
        db.update(user_id, data)
"""

__version__ = "1.0.0"
__author__ = "Rayan Pal"

# Core exports
from .client import SwiftAPI
from .enforcement import Enforcement, enforce
from .verifier import verify_signature, is_valid, get_public_key

# Exceptions
from .exceptions import (
    SwiftAPIError,
    AuthenticationError,
    PolicyViolation,
    SignatureVerificationError,
    AttestationExpiredError,
    AttestationRevokedError,
    RateLimitError,
    NetworkError,
)

# UX utilities
from .utils import (
    Colors,
    Symbols,
    print_approved,
    print_denied,
    print_verified,
    print_error,
    print_info,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "SwiftAPI",
    "Enforcement",
    "enforce",
    # Verification
    "verify_signature",
    "is_valid",
    "get_public_key",
    # Exceptions
    "SwiftAPIError",
    "AuthenticationError",
    "PolicyViolation",
    "SignatureVerificationError",
    "AttestationExpiredError",
    "AttestationRevokedError",
    "RateLimitError",
    "NetworkError",
    # UX
    "Colors",
    "Symbols",
    "print_approved",
    "print_denied",
    "print_verified",
    "print_error",
    "print_info",
]
