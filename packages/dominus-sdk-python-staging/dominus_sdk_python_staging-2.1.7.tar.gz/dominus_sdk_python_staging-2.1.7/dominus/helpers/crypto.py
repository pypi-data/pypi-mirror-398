"""
Cryptographic helpers for password and PSK hashing.

All hashing is done client-side (in SDK) before sending to Architect.
This ensures passwords/PSKs are never transmitted in plaintext.
"""
import bcrypt
import hashlib
import secrets
import string


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Raw password string

    Returns:
        Bcrypt hash string (includes salt)
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password_local(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash locally.

    This is primarily for testing. In production, verification
    happens via Architect's verify_user_password endpoint.

    Args:
        password: Raw password to verify
        password_hash: Bcrypt hash to compare against

    Returns:
        True if password matches hash
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def hash_psk(psk: str) -> str:
    """
    Hash a PSK (Pre-Shared Key) using bcrypt.

    Args:
        psk: Raw PSK string

    Returns:
        Bcrypt hash string (includes salt)
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(psk.encode('utf-8'), salt).decode('utf-8')


def verify_psk_local(psk: str, psk_hash: str) -> bool:
    """
    Verify a PSK against a bcrypt hash locally.

    This is primarily for testing. In production, verification
    happens via Architect's verify_client_psk endpoint.

    Args:
        psk: Raw PSK to verify
        psk_hash: Bcrypt hash to compare against

    Returns:
        True if PSK matches hash
    """
    return bcrypt.checkpw(psk.encode('utf-8'), psk_hash.encode('utf-8'))


def generate_psk_local(length: int = 32) -> str:
    """
    Generate a random PSK locally.

    Note: In production, prefer using Sovereign's /generate-psk endpoint
    for centralized PSK generation. This is a fallback.

    Args:
        length: Length of PSK to generate (default: 32)

    Returns:
        Random PSK string
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256.

    Used for refresh tokens where we need fast comparison
    and don't need the security properties of bcrypt.

    Args:
        token: Raw token string

    Returns:
        SHA-256 hex digest
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generate_token(length: int = 64) -> str:
    """
    Generate a random token string.

    Args:
        length: Length of token to generate (default: 64)

    Returns:
        Random URL-safe token string
    """
    return secrets.token_urlsafe(length)
