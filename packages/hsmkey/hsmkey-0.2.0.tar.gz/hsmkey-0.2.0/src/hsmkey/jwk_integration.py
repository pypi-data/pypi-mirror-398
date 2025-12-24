"""JWCrypto integration for HSM-backed keys.

This module provides JWK (JSON Web Key) support for HSM-backed keys,
allowing seamless use of HSM keys with jwcrypto for JWS and JWE operations.

Example usage:

    from hsmkey import SessionPool
    from hsmkey.jwk_integration import HSMJWK
    from jwcrypto import JWS

    pool = SessionPool(
        module_path="/usr/lib/softhsm/libsofthsm2.so",
        token_label="my-token",
        user_pin="123456",
    )

    with pool.session() as session:
        # Create JWK from HSM key
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Sign with JWS (signing happens on HSM)
        jws = JWS(b'{"sub": "user@example.com"}')
        jws.add_signature(key, alg='RS256', protected='{"typ":"JWT"}')
        token = jws.serialize(compact=True)
"""

from __future__ import annotations

import base64
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator, Union

from cryptography.hazmat.primitives.asymmetric import ec, ed25519, ed448, rsa
from jwcrypto.jwk import JWK
from pkcs11 import Attribute, KeyType, ObjectClass

from .algorithms import CURVE_ALIASES, OID_TO_CURVE
from .exceptions import HSMKeyNotFoundError, HSMSessionError
from .keys import (
    PKCS11EllipticCurvePrivateKey,
    PKCS11EllipticCurvePublicKey,
    PKCS11Ed25519PrivateKey,
    PKCS11Ed25519PublicKey,
    PKCS11Ed448PrivateKey,
    PKCS11Ed448PublicKey,
    PKCS11RSAPrivateKey,
    PKCS11RSAPublicKey,
)
from .session import SessionPool

if TYPE_CHECKING:
    from pkcs11 import Session

# Type alias for all supported HSM private key types
HSMPrivateKey = Union[
    PKCS11RSAPrivateKey,
    PKCS11EllipticCurvePrivateKey,
    PKCS11Ed25519PrivateKey,
    PKCS11Ed448PrivateKey,
]

# Type alias for all supported HSM public key types
HSMPublicKey = Union[
    PKCS11RSAPublicKey,
    PKCS11EllipticCurvePublicKey,
    PKCS11Ed25519PublicKey,
    PKCS11Ed448PublicKey,
]

# Curve name to JWK 'crv' parameter mapping
CURVE_TO_JWK_CRV: dict[str, str] = {
    "secp256r1": "P-256",
    "secp384r1": "P-384",
    "secp521r1": "P-521",
    "secp256k1": "secp256k1",
    "brainpoolP256r1": "BP-256",
    "brainpoolP384r1": "BP-384",
    "brainpoolP512r1": "BP-512",
}

# EdDSA OIDs
ED25519_OID = bytes.fromhex("06032b6570")  # 1.3.101.112
ED448_OID = bytes.fromhex("06032b6571")  # 1.3.101.113


def _base64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _int_to_bytes(value: int, length: int | None = None) -> bytes:
    """Convert integer to big-endian bytes.

    Args:
        value: Integer to convert
        length: Optional fixed length (pads with zeros if needed)

    Returns:
        Big-endian byte representation
    """
    if length is None:
        length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "big")


class HSMJWK(JWK):
    """JWK backed by HSM keys.

    This class extends jwcrypto's JWK to support HSM-backed keys. All
    cryptographic operations (signing, decryption) are performed on the HSM,
    while public key parameters are extracted for JWK representation.

    The private key material never leaves the HSM.

    Attributes:
        _hsm_private_key: The HSM private key object
        _hsm_public_key: The HSM public key object
        _session: The PKCS#11 session
        _key_id: PKCS#11 key ID
        _key_label: PKCS#11 key label
    """

    def __init__(
        self,
        session: Session | None = None,
        key_id: bytes | None = None,
        key_label: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize HSM JWK.

        Args:
            session: PKCS#11 session (optional, can be set later)
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
            **kwargs: Additional JWK parameters
        """
        self._session = session
        self._key_id = key_id
        self._key_label = key_label
        self._hsm_private_key: HSMPrivateKey | None = None
        self._hsm_public_key: HSMPublicKey | None = None

        super().__init__(**kwargs)

    @classmethod
    def from_hsm(
        cls,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
        kid: str | None = None,
        use: str | None = None,
        key_ops: list[str] | None = None,
    ) -> "HSMJWK":
        """Create a JWK from an HSM key.

        This factory method loads a key from the HSM and creates a JWK
        representation with the public key parameters.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
            kid: JWK Key ID to assign
            use: Key use ('sig' or 'enc')
            key_ops: Allowed key operations

        Returns:
            HSMJWK instance backed by the HSM key

        Raises:
            HSMKeyNotFoundError: If the key is not found
            ValueError: If key type is not supported
        """
        if key_id is None and key_label is None:
            raise ValueError("Either key_id or key_label must be provided")

        # Try to find the private key and determine its type
        hsm_key, key_type = cls._load_hsm_key(session, key_id, key_label)

        # Build JWK parameters based on key type
        jwk_params = cls._extract_jwk_params(hsm_key, key_type)

        # Add optional parameters
        if kid is not None:
            jwk_params["kid"] = kid
        if use is not None:
            jwk_params["use"] = use
        if key_ops is not None:
            jwk_params["key_ops"] = key_ops

        # Create instance
        instance = cls(
            session=session,
            key_id=key_id,
            key_label=key_label,
            **jwk_params,
        )

        # Cache the loaded key
        instance._hsm_private_key = hsm_key
        instance._hsm_public_key = hsm_key.public_key()

        return instance

    @classmethod
    def _load_hsm_key(
        cls,
        session: Session,
        key_id: bytes | None,
        key_label: str | None,
    ) -> tuple[HSMPrivateKey, str]:
        """Load HSM key and determine its type.

        Args:
            session: PKCS#11 session
            key_id: Key ID
            key_label: Key label

        Returns:
            Tuple of (HSM private key, key type string)

        Raises:
            HSMKeyNotFoundError: If key not found
        """
        # Try RSA first
        try:
            key = PKCS11RSAPrivateKey(session, key_id, key_label)
            # Access property to trigger key loading
            _ = key.key_size
            return key, "RSA"
        except (HSMKeyNotFoundError, Exception):
            pass

        # Try EC
        try:
            key = PKCS11EllipticCurvePrivateKey(session, key_id, key_label)
            _ = key.curve
            return key, "EC"
        except (HSMKeyNotFoundError, Exception):
            pass

        # Try Ed25519
        try:
            key = PKCS11Ed25519PrivateKey(session, key_id, key_label)
            # Verify it's actually Ed25519 by checking the curve
            ec_params = bytes(key.pkcs11_public_key[Attribute.EC_PARAMS])
            if ec_params == ED25519_OID:
                return key, "Ed25519"
        except (HSMKeyNotFoundError, Exception):
            pass

        # Try Ed448
        try:
            key = PKCS11Ed448PrivateKey(session, key_id, key_label)
            ec_params = bytes(key.pkcs11_public_key[Attribute.EC_PARAMS])
            if ec_params == ED448_OID:
                return key, "Ed448"
        except (HSMKeyNotFoundError, Exception):
            pass

        raise HSMKeyNotFoundError(
            f"Key not found: id={key_id}, label={key_label}"
        )

    @classmethod
    def _extract_jwk_params(
        cls,
        hsm_key: HSMPrivateKey,
        key_type: str,
    ) -> dict[str, Any]:
        """Extract JWK parameters from HSM key.

        Args:
            hsm_key: HSM private key
            key_type: Key type string ("RSA", "EC", "Ed25519", "Ed448")

        Returns:
            Dictionary of JWK parameters
        """
        if key_type == "RSA":
            assert isinstance(hsm_key, PKCS11RSAPrivateKey)
            return cls._extract_rsa_params(hsm_key)
        elif key_type == "EC":
            assert isinstance(hsm_key, PKCS11EllipticCurvePrivateKey)
            return cls._extract_ec_params(hsm_key)
        elif key_type == "Ed25519":
            assert isinstance(hsm_key, PKCS11Ed25519PrivateKey)
            return cls._extract_ed25519_params(hsm_key)
        elif key_type == "Ed448":
            assert isinstance(hsm_key, PKCS11Ed448PrivateKey)
            return cls._extract_ed448_params(hsm_key)
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

    @classmethod
    def _extract_rsa_params(cls, hsm_key: PKCS11RSAPrivateKey) -> dict[str, Any]:
        """Extract RSA JWK parameters.

        Args:
            hsm_key: RSA private key

        Returns:
            JWK parameters for RSA key
        """
        pub_key = hsm_key.public_key()
        numbers = pub_key.public_numbers()

        # Convert to base64url
        n_bytes = _int_to_bytes(numbers.n)
        e_bytes = _int_to_bytes(numbers.e)

        return {
            "kty": "RSA",
            "n": _base64url_encode(n_bytes),
            "e": _base64url_encode(e_bytes),
        }

    @classmethod
    def _extract_ec_params(
        cls, hsm_key: PKCS11EllipticCurvePrivateKey
    ) -> dict[str, Any]:
        """Extract EC JWK parameters.

        Args:
            hsm_key: EC private key

        Returns:
            JWK parameters for EC key
        """
        pub_key = hsm_key.public_key()
        numbers = pub_key.public_numbers()

        # Get curve name and map to JWK crv
        curve_name = numbers.curve.name
        # Normalize curve name
        curve_name = CURVE_ALIASES.get(curve_name, curve_name)
        crv = CURVE_TO_JWK_CRV.get(curve_name, curve_name)

        # Determine coordinate size based on curve
        key_size = hsm_key.key_size
        coord_size = (key_size + 7) // 8

        # Convert coordinates to fixed-size bytes
        x_bytes = _int_to_bytes(numbers.x, coord_size)
        y_bytes = _int_to_bytes(numbers.y, coord_size)

        return {
            "kty": "EC",
            "crv": crv,
            "x": _base64url_encode(x_bytes),
            "y": _base64url_encode(y_bytes),
        }

    @classmethod
    def _extract_ed25519_params(
        cls, hsm_key: PKCS11Ed25519PrivateKey
    ) -> dict[str, Any]:
        """Extract Ed25519 JWK parameters.

        Args:
            hsm_key: Ed25519 private key

        Returns:
            JWK parameters for Ed25519 key (OKP type)
        """
        pub_key = hsm_key.public_key()
        x_bytes = pub_key.public_bytes_raw()

        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": _base64url_encode(x_bytes),
        }

    @classmethod
    def _extract_ed448_params(cls, hsm_key: PKCS11Ed448PrivateKey) -> dict[str, Any]:
        """Extract Ed448 JWK parameters.

        Args:
            hsm_key: Ed448 private key

        Returns:
            JWK parameters for Ed448 key (OKP type)
        """
        pub_key = hsm_key.public_key()
        x_bytes = pub_key.public_bytes_raw()

        return {
            "kty": "OKP",
            "crv": "Ed448",
            "x": _base64url_encode(x_bytes),
        }

    def _get_hsm_private_key(self) -> HSMPrivateKey:
        """Get or load the HSM private key.

        Returns:
            HSM private key

        Raises:
            HSMSessionError: If session is not available
            HSMKeyNotFoundError: If key not found
        """
        if self._hsm_private_key is not None:
            return self._hsm_private_key

        if self._session is None:
            raise HSMSessionError("No HSM session available")

        self._hsm_private_key, _ = self._load_hsm_key(
            self._session, self._key_id, self._key_label
        )
        return self._hsm_private_key

    def _get_hsm_public_key(self) -> HSMPublicKey:
        """Get or load the HSM public key.

        Returns:
            HSM public key
        """
        if self._hsm_public_key is not None:
            return self._hsm_public_key

        # Get from private key
        private_key = self._get_hsm_private_key()
        self._hsm_public_key = private_key.public_key()
        return self._hsm_public_key

    def get_op_key(
        self,
        operation: str | None = None,
        arg: Any = None,
    ) -> Any:
        """Return the key object for the specified operation.

        This method is called by jwcrypto's JWS and JWE implementations
        to get the actual key for cryptographic operations.

        For HSM keys:
        - Sign, decrypt, unwrapKey: Returns HSM private key
        - Verify, encrypt, wrapKey: Returns HSM public key

        Args:
            operation: The operation to perform ('sign', 'verify', etc.)
            arg: Optional argument (algorithm, etc.)

        Returns:
            HSM key object (compatible with cryptography library interfaces)
        """
        if operation in ("sign", "decrypt", "unwrapKey"):
            return self._get_hsm_private_key()
        elif operation in ("verify", "encrypt", "wrapKey"):
            return self._get_hsm_public_key()
        else:
            # For unknown operations, try to return private key
            # or fall back to parent implementation
            try:
                return self._get_hsm_private_key()
            except (HSMSessionError, HSMKeyNotFoundError):
                return super().get_op_key(operation, arg)

    def has_private(self) -> bool:
        """Check if this JWK has a private key.

        For HSM keys, the private key exists on the HSM but cannot be exported.

        Returns:
            True (HSM keys always have private key)
        """
        return True

    def export_private(self, as_dict: bool = False) -> dict | str:
        """Export private key.

        For HSM keys, this raises an error since private keys cannot leave the HSM.

        Raises:
            HSMSessionError: Always raised for HSM keys
        """
        raise HSMSessionError(
            "Cannot export private key from HSM. "
            "Private key material is protected and cannot leave the HSM."
        )

    def export_public(self, as_dict: bool = False) -> dict | str:
        """Export public key.

        Returns the public key parameters in JWK format.

        Args:
            as_dict: If True, return as dictionary; otherwise return JSON string

        Returns:
            Public key in JWK format
        """
        return super().export_public(as_dict=as_dict)


class HSMJWKSet:
    """JWK Set backed by HSM keys.

    Manages a collection of HSM-backed JWKs for use with jwcrypto.
    """

    def __init__(self, session: Session) -> None:
        """Initialize HSM JWK Set.

        Args:
            session: PKCS#11 session
        """
        self._session = session
        self._keys: dict[str, HSMJWK] = {}

    def add_key(
        self,
        key_id: bytes | None = None,
        key_label: str | None = None,
        kid: str | None = None,
        use: str | None = None,
        key_ops: list[str] | None = None,
    ) -> HSMJWK:
        """Add an HSM key to the set.

        Args:
            key_id: PKCS#11 key ID
            key_label: PKCS#11 key label
            kid: JWK Key ID to assign
            use: Key use ('sig' or 'enc')
            key_ops: Allowed key operations

        Returns:
            The created HSMJWK

        Raises:
            ValueError: If kid is not unique
        """
        jwk = HSMJWK.from_hsm(
            self._session,
            key_id=key_id,
            key_label=key_label,
            kid=kid,
            use=use,
            key_ops=key_ops,
        )

        # Use provided kid or generate one
        actual_kid = kid or key_label or (key_id.hex() if key_id else None)
        if actual_kid is None:
            raise ValueError("Must provide kid, key_label, or key_id")

        if actual_kid in self._keys:
            raise ValueError(f"Key ID already exists: {actual_kid}")

        self._keys[actual_kid] = jwk
        return jwk

    def get_key(self, kid: str) -> HSMJWK | None:
        """Get key by Key ID.

        Args:
            kid: JWK Key ID

        Returns:
            HSMJWK if found, None otherwise
        """
        return self._keys.get(kid)

    def __iter__(self) -> Iterator[HSMJWK]:
        """Iterate over keys in the set."""
        return iter(self._keys.values())

    def __len__(self) -> int:
        """Return number of keys in the set."""
        return len(self._keys)


def jwk_from_hsm(
    session: Session,
    key_id: bytes | None = None,
    key_label: str | None = None,
    kid: str | None = None,
    use: str | None = None,
    key_ops: list[str] | None = None,
) -> HSMJWK:
    """Create a JWK from an HSM key.

    Convenience function that wraps HSMJWK.from_hsm().

    Args:
        session: PKCS#11 session
        key_id: Key ID (CKA_ID)
        key_label: Key label (CKA_LABEL)
        kid: JWK Key ID to assign
        use: Key use ('sig' or 'enc')
        key_ops: Allowed key operations

    Returns:
        HSMJWK instance backed by the HSM key

    Example:
        with pool.session() as session:
            key = jwk_from_hsm(session, key_label="rsa-2048")
    """
    return HSMJWK.from_hsm(
        session,
        key_id=key_id,
        key_label=key_label,
        kid=kid,
        use=use,
        key_ops=key_ops,
    )


@contextmanager
def hsm_session(
    module_path: str,
    token_label: str,
    pin: str,
) -> Iterator[Session]:
    """Context manager for HSM session.

    Convenience function for managing HSM sessions.

    Args:
        module_path: Path to PKCS#11 library
        token_label: Token label
        pin: User PIN

    Yields:
        PKCS#11 session

    Example:
        with hsm_session("/usr/lib/softhsm/libsofthsm2.so", "my-token", "1234") as session:
            key = jwk_from_hsm(session, key_label="my-key")
    """
    pool = SessionPool(
        module_path=module_path,
        token_label=token_label,
        user_pin=pin,
    )
    with pool.session() as session:
        yield session
