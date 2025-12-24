"""Ed25519 key implementations backed by HSM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pkcs11 import Attribute, KeyType, Mechanism

from ..exceptions import HSMOperationError, HSMUnsupportedError
from .base import PKCS11PrivateKeyMixin

if TYPE_CHECKING:
    from pkcs11 import Session


class PKCS11Ed25519PrivateKey(PKCS11PrivateKeyMixin, ed25519.Ed25519PrivateKey):
    """Ed25519 private key backed by HSM.

    This class implements the cryptography library's Ed25519PrivateKey
    interface while performing all cryptographic operations on the HSM.
    """

    _key_type = KeyType.EC_EDWARDS

    def __init__(
        self,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> None:
        """Initialize HSM Ed25519 private key.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
        """
        PKCS11PrivateKeyMixin.__init__(self, session, key_id, key_label)

    def public_key(self) -> "PKCS11Ed25519PublicKey":
        """Return the public key corresponding to this private key."""
        return PKCS11Ed25519PublicKey.from_pkcs11_key(
            self._session,
            self.pkcs11_public_key,
            self._key_id,
            self._key_label,
        )

    def sign(self, data: bytes) -> bytes:
        """Sign data using Ed25519.

        Ed25519 does not require pre-hashing; the algorithm handles
        hashing internally.

        Args:
            data: Data to sign

        Returns:
            64-byte signature

        Raises:
            HSMOperationError: If signing fails
        """
        try:
            signature = self.pkcs11_private_key.sign(
                data,
                mechanism=Mechanism.EDDSA,
            )
            return bytes(signature)
        except Exception as e:
            raise HSMOperationError(f"Ed25519 signing failed: {e}") from e

    def private_bytes(
        self,
        encoding: serialization.Encoding,
        format: serialization.PrivateFormat,
        encryption_algorithm: serialization.KeySerializationEncryption,
    ) -> bytes:
        """Not supported for HSM keys."""
        self._raise_unsupported("private_bytes()")

    def private_bytes_raw(self) -> bytes:
        """Not supported for HSM keys."""
        self._raise_unsupported("private_bytes_raw()")


class PKCS11Ed25519PublicKey(ed25519.Ed25519PublicKey):
    """Ed25519 public key from HSM.

    This class wraps the public key data extracted from HSM and provides
    the standard cryptography library interface.
    """

    def __init__(self, public_key_bytes: bytes) -> None:
        """Initialize Ed25519 public key.

        Args:
            public_key_bytes: 32-byte public key
        """
        if len(public_key_bytes) != 32:
            raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(public_key_bytes)}")
        self._public_key_bytes = public_key_bytes
        # Create internal cryptography public key for verification
        self._crypto_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

    @classmethod
    def from_pkcs11_key(
        cls,
        session: "Session",
        pkcs11_key,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> "PKCS11Ed25519PublicKey":
        """Create public key from PKCS#11 public key object.

        Args:
            session: PKCS#11 session
            pkcs11_key: PKCS#11 public key object
            key_id: Key ID
            key_label: Key label

        Returns:
            PKCS11Ed25519PublicKey instance
        """
        # Get EC_POINT which contains the public key
        ec_point = bytes(pkcs11_key[Attribute.EC_POINT])

        # EC_POINT format varies by implementation
        # Could be: raw 32 bytes, or OCTET STRING wrapped (04 20 <32 bytes>)
        if len(ec_point) == 32:
            public_key_bytes = ec_point
        elif len(ec_point) == 34 and ec_point[0:2] == b'\x04\x20':
            # OCTET STRING with length 32
            public_key_bytes = ec_point[2:]
        elif len(ec_point) > 32:
            # Try extracting last 32 bytes
            public_key_bytes = ec_point[-32:]
        else:
            raise ValueError(f"Invalid Ed25519 EC_POINT format: {ec_point.hex()}")

        return cls(public_key_bytes)

    def public_bytes(
        self,
        encoding: serialization.Encoding,
        format: serialization.PublicFormat,
    ) -> bytes:
        """Serialize public key."""
        return self._crypto_key.public_bytes(encoding, format)

    def public_bytes_raw(self) -> bytes:
        """Return raw 32-byte public key."""
        return self._public_key_bytes

    def verify(self, signature: bytes, data: bytes) -> None:
        """Verify a signature.

        Args:
            signature: 64-byte signature
            data: Original data

        Raises:
            InvalidSignature: If verification fails
        """
        self._crypto_key.verify(signature, data)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, (PKCS11Ed25519PublicKey, ed25519.Ed25519PublicKey)):
            return False
        return self._public_key_bytes == other.public_bytes_raw()

    def __hash__(self) -> int:
        """Hash based on public key bytes."""
        return hash(self._public_key_bytes)

    def __copy__(self) -> "PKCS11Ed25519PublicKey":
        """Create a copy."""
        return PKCS11Ed25519PublicKey(self._public_key_bytes)

    def __deepcopy__(self, memo: dict) -> "PKCS11Ed25519PublicKey":
        """Create a deep copy."""
        return self.__copy__()
