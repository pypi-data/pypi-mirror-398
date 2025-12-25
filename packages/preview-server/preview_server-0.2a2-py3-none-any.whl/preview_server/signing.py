"""Hostname signing and verification for secure preview URLs.

This module provides cryptographic signing of hostnames to prevent
unauthorized access to arbitrary git refs. When enabled, only
pre-signed hostnames will be accepted.

The signature uses HMAC-SHA256 with lowercase hex encoding to ensure
compatibility with subdomain naming rules (case-insensitive).
"""

import hashlib
import hmac
from typing import Optional

# Signature length in hex characters (20 chars = 80 bits of entropy)
SIGNATURE_LENGTH = 20


def sign_hostname(hostname: str, secret: str) -> str:
    """Sign a hostname with the given secret.

    Args:
        hostname: The hostname/subdomain to sign (e.g., "main" or "backend--feature")
        secret: The shared secret for signing

    Returns:
        Signed hostname in format: hostname--signature
    """
    signature = _generate_signature(hostname, secret)
    return f"{hostname}--{signature}"


def _generate_signature(hostname: str, secret: str) -> str:
    """Generate a subdomain-safe signature for a hostname.

    Uses HMAC-SHA256 with lowercase hex encoding. Lowercase hex ensures
    the signature is valid in subdomains (which are case-insensitive).

    Args:
        hostname: The hostname to sign
        secret: The shared secret

    Returns:
        Lowercase hex signature string (20 characters = 80 bits)
    """
    # Create HMAC-SHA256 signature
    key = secret.encode("utf-8")
    message = hostname.encode("utf-8")
    signature = hmac.new(key, message, hashlib.sha256).digest()

    # Encode as lowercase hex and truncate
    # 20 hex chars = 80 bits of entropy, sufficient for this use case
    return signature.hex()[:SIGNATURE_LENGTH]


def verify_signature(signed_hostname: str, secret: str) -> bool:
    """Verify a signed hostname against the secret.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        signed_hostname: The signed hostname (e.g., "main--abc123def456")
        secret: The shared secret to verify against

    Returns:
        True if signature is valid, False otherwise
    """
    # Extract hostname and signature
    parts = signed_hostname.rsplit("--", 1)
    if len(parts) != 2:
        return False

    hostname, provided_sig = parts

    # Empty signature is invalid
    if not provided_sig:
        return False

    # Generate expected signature
    expected_sig = _generate_signature(hostname, secret)

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_sig, provided_sig)


def _is_hex_signature(s: str) -> bool:
    """Check if a string looks like a hex signature.

    Args:
        s: The string to check

    Returns:
        True if it's a valid hex signature (lowercase hex, correct length)
    """
    if len(s) != SIGNATURE_LENGTH:
        return False
    try:
        int(s, 16)  # Will raise ValueError if not valid hex
        return s == s.lower()  # Must be lowercase
    except ValueError:
        return False


def extract_hostname(signed_hostname: str) -> str:
    """Extract the original hostname from a signed hostname.

    If the hostname doesn't contain a signature portion (no '--'),
    returns the original hostname as-is.

    Args:
        signed_hostname: The potentially signed hostname

    Returns:
        The original hostname without signature
    """
    # Count the number of -- separators
    # If we have at least one, the last part might be a signature
    parts = signed_hostname.rsplit("--", 1)
    if len(parts) == 2:
        # Check if the last part looks like a signature (lowercase hex, 20 chars)
        potential_sig = parts[1]
        if _is_hex_signature(potential_sig):
            return parts[0]

    # No signature found, return as-is
    return signed_hostname


def extract_hostname_if_valid(signed_hostname: str, secret: str) -> Optional[str]:
    """Extract hostname only if signature is valid.

    This combines verification and extraction in one step.

    Args:
        signed_hostname: The signed hostname to verify
        secret: The shared secret

    Returns:
        The original hostname if valid, None if invalid
    """
    if verify_signature(signed_hostname, secret):
        parts = signed_hostname.rsplit("--", 1)
        return parts[0] if len(parts) == 2 else None
    return None
