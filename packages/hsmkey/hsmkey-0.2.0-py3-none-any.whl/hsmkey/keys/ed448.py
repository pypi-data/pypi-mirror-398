"""Ed448 key implementations backed by HSM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed448
from pkcs11 import Attribute, KeyType, Mechanism

from ..exceptions import HSMOperationError, HSMUnsupportedError
from .base import PKCS11PrivateKeyMixin

if TYPE_CHECKING:
    from pkcs11 import Session


class PKCS11Ed448PrivateKey(PKCS11PrivateKeyMixin, ed448.Ed448PrivateKey):
    """Ed448 private key backed by HSM.

    This class implements the cryptography library's Ed448PrivateKey
    interface while performing all cryptographic operations on the HSM.
    """

    _key_type = KeyType.EC_EDWARDS

    def __init__(
        self,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> None:
        """Initialize HSM Ed448 private key.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
        """
        PKCS11PrivateKeyMixin.__init__(self, session, key_id, key_label)

    def public_key(self) -> "PKCS11Ed448PublicKey":
        """Return the public key corresponding to this private key."""
        return PKCS11Ed448PublicKey.from_pkcs11_key(
            self._session,
            self.pkcs11_public_key,
            self._key_id,
            self._key_label,
        )

    def sign(self, data: bytes) -> bytes:
        """Sign data using Ed448.

        Ed448 does not require pre-hashing; the algorithm handles
        hashing internally.

        Args:
            data: Data to sign

        Returns:
            114-byte signature

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
            raise HSMOperationError(f"Ed448 signing failed: {e}") from e

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


class PKCS11Ed448PublicKey(ed448.Ed448PublicKey):
    """Ed448 public key from HSM.

    This class wraps the public key data extracted from HSM and provides
    the standard cryptography library interface.
    """

    def __init__(self, public_key_bytes: bytes) -> None:
        """Initialize Ed448 public key.

        Args:
            public_key_bytes: 57-byte public key
        """
        if len(public_key_bytes) != 57:
            raise ValueError(f"Ed448 public key must be 57 bytes, got {len(public_key_bytes)}")
        self._public_key_bytes = public_key_bytes
        # Create internal cryptography public key for verification
        self._crypto_key = ed448.Ed448PublicKey.from_public_bytes(public_key_bytes)

    @classmethod
    def from_pkcs11_key(
        cls,
        session: "Session",
        pkcs11_key,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> "PKCS11Ed448PublicKey":
        """Create public key from PKCS#11 public key object.

        Args:
            session: PKCS#11 session
            pkcs11_key: PKCS#11 public key object
            key_id: Key ID
            key_label: Key label

        Returns:
            PKCS11Ed448PublicKey instance
        """
        # Get EC_POINT which contains the public key
        ec_point = bytes(pkcs11_key[Attribute.EC_POINT])

        # EC_POINT format varies by implementation
        # Could be: raw 57 bytes, or OCTET STRING wrapped (04 39 <57 bytes>)
        if len(ec_point) == 57:
            public_key_bytes = ec_point
        elif len(ec_point) == 59 and ec_point[0:2] == b'\x04\x39':
            # OCTET STRING with length 57
            public_key_bytes = ec_point[2:]
        elif len(ec_point) > 57:
            # Try extracting last 57 bytes
            public_key_bytes = ec_point[-57:]
        else:
            raise ValueError(f"Invalid Ed448 EC_POINT format: {ec_point.hex()}")

        return cls(public_key_bytes)

    def public_bytes(
        self,
        encoding: serialization.Encoding,
        format: serialization.PublicFormat,
    ) -> bytes:
        """Serialize public key."""
        return self._crypto_key.public_bytes(encoding, format)

    def public_bytes_raw(self) -> bytes:
        """Return raw 57-byte public key."""
        return self._public_key_bytes

    def verify(self, signature: bytes, data: bytes) -> None:
        """Verify a signature.

        Args:
            signature: 114-byte signature
            data: Original data

        Raises:
            InvalidSignature: If verification fails
        """
        self._crypto_key.verify(signature, data)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, (PKCS11Ed448PublicKey, ed448.Ed448PublicKey)):
            return False
        return self._public_key_bytes == other.public_bytes_raw()

    def __hash__(self) -> int:
        """Hash based on public key bytes."""
        return hash(self._public_key_bytes)

    def __copy__(self) -> "PKCS11Ed448PublicKey":
        """Create a copy."""
        return PKCS11Ed448PublicKey(self._public_key_bytes)

    def __deepcopy__(self, memo: dict) -> "PKCS11Ed448PublicKey":
        """Create a deep copy."""
        return self.__copy__()
