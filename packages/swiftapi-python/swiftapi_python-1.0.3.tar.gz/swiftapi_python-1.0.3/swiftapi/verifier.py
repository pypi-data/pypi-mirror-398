"""
SwiftAPI SDK - Ed25519 Signature Verifier (The Shield)

This module provides OFFLINE cryptographic verification of execution attestations.
It does not require network connectivity - it uses the hardcoded SwiftAPI public key.
"""

import base64
import json
from datetime import datetime, timezone
from typing import Dict, Any

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from .exceptions import (
    SignatureVerificationError,
    AttestationExpiredError,
)

# SwiftAPI's Ed25519 Public Key (Base64)
# This is the ONLY source of truth for attestation verification
SWIFTAPI_PUBLIC_KEY_B64 = "jajZXZ0R3CUWkE5/5Mxx5Y76CdsSzaPDuT7aWnooZSk="

# Decode public key once at module load
SWIFTAPI_PUBLIC_KEY = base64.b64decode(SWIFTAPI_PUBLIC_KEY_B64)
VERIFY_KEY = VerifyKey(SWIFTAPI_PUBLIC_KEY)


def verify_signature(attestation: Dict[str, Any]) -> bool:
    """
    Verify the Ed25519 signature of an execution attestation.

    This is OFFLINE verification - no network required.
    The signature proves the attestation was issued by SwiftAPI.

    Args:
        attestation: The execution_attestation dict from /verify response

    Returns:
        True if signature is valid

    Raises:
        SignatureVerificationError: If signature is invalid or missing
        AttestationExpiredError: If attestation has expired
    """
    # Extract required fields
    signature_b64 = attestation.get("signature")
    if not signature_b64:
        raise SignatureVerificationError("Missing signature in attestation")

    jti = attestation.get("jti")
    action_fingerprint = attestation.get("action_fingerprint")
    expires_at = attestation.get("expires_at")

    if not all([jti, action_fingerprint, expires_at]):
        raise SignatureVerificationError("Incomplete attestation: missing required fields")

    # Check expiration FIRST
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now > expiry:
            raise AttestationExpiredError(f"Attestation expired at {expires_at}")
    except ValueError as e:
        raise SignatureVerificationError(f"Invalid expiration format: {e}")

    # Reconstruct the signed payload (deterministic serialization)
    # This MUST match the server's signing logic exactly
    signed_payload = _reconstruct_signed_payload(attestation)

    # Decode signature
    try:
        signature = base64.b64decode(signature_b64)
    except Exception as e:
        raise SignatureVerificationError(f"Invalid signature encoding: {e}")

    # Verify signature
    try:
        VERIFY_KEY.verify(signed_payload, signature)
        return True
    except BadSignatureError:
        raise SignatureVerificationError(
            "INVALID SIGNATURE: Attestation was not signed by SwiftAPI. "
            "This could indicate a forged or tampered attestation."
        )


def _reconstruct_signed_payload(attestation: Dict[str, Any]) -> bytes:
    """
    Reconstruct the exact payload that was signed by SwiftAPI.

    The server signs the attestation BEFORE adding signature/signing_mode fields.
    We must reconstruct that exact payload.
    """
    # Copy attestation and remove signature fields (they weren't in the signed payload)
    signed_fields = {k: v for k, v in attestation.items() if k not in ("signature", "signing_mode")}

    # Deterministic JSON serialization (must match server exactly)
    payload_str = json.dumps(signed_fields, sort_keys=True, separators=(",", ":"))
    return payload_str.encode("utf-8")


def get_public_key() -> str:
    """Return SwiftAPI's public key in Base64 format."""
    return SWIFTAPI_PUBLIC_KEY_B64


def is_valid(attestation: Dict[str, Any]) -> bool:
    """
    Check if attestation is valid without raising exceptions.

    Args:
        attestation: The execution_attestation dict

    Returns:
        True if valid, False otherwise
    """
    try:
        return verify_signature(attestation)
    except Exception:
        return False
