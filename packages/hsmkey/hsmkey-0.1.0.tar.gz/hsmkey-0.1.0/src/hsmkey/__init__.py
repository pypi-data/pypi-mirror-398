"""HSMKey - HSM-backed cryptographic keys for Python.

This module provides cryptography-compatible key implementations that
perform all cryptographic operations on a Hardware Security Module (HSM)
via PKCS#11.

Example usage:

    from hsmkey import SessionPool
    from hsmkey.keys import PKCS11RSAPrivateKey

    # Create session pool
    pool = SessionPool(
        module_path="/usr/lib/softhsm/libsofthsm2.so",
        token_label="my-token",
        user_pin="123456",
    )

    # Use session to access keys
    with pool.session() as session:
        key = PKCS11RSAPrivateKey(session, key_label="my-rsa-key")
        signature = key.sign(b"data", padding.PKCS1v15(), hashes.SHA256())
"""

from __future__ import annotations


from .config import HSMConfig, find_softhsm_module, get_softhsm_conf
from .exceptions import (
    HSMConfigError,
    HSMError,
    HSMKeyNotFoundError,
    HSMOperationError,
    HSMPinError,
    HSMSessionError,
    HSMUnsupportedError,
)
from .session import SessionPool

# Key imports
from .keys import (
    PKCS11RSAPrivateKey,
    PKCS11RSAPublicKey,
    PKCS11EllipticCurvePrivateKey,
    PKCS11EllipticCurvePublicKey,
    PKCS11Ed25519PrivateKey,
    PKCS11Ed25519PublicKey,
    PKCS11Ed448PrivateKey,
    PKCS11Ed448PublicKey,
)

__all__ = [
    # Version
    "__version__",
    # Config
    "HSMConfig",
    "find_softhsm_module",
    "get_softhsm_conf",
    # Exceptions
    "HSMError",
    "HSMSessionError",
    "HSMKeyNotFoundError",
    "HSMPinError",
    "HSMOperationError",
    "HSMUnsupportedError",
    "HSMConfigError",
    # Session
    "SessionPool",
    # RSA Keys
    "PKCS11RSAPrivateKey",
    "PKCS11RSAPublicKey",
    # EC Keys
    "PKCS11EllipticCurvePrivateKey",
    "PKCS11EllipticCurvePublicKey",
    # Ed25519 Keys
    "PKCS11Ed25519PrivateKey",
    "PKCS11Ed25519PublicKey",
    # Ed448 Keys
    "PKCS11Ed448PrivateKey",
    "PKCS11Ed448PublicKey",
]
