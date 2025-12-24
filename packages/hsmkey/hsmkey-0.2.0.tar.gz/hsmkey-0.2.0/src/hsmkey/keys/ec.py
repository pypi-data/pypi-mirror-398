"""Elliptic Curve key implementations backed by HSM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    decode_dss_signature,
    encode_dss_signature,
)
from pkcs11 import Attribute, KeyType, Mechanism

from ..algorithms import OID_TO_CURVE, normalize_curve_name
from ..exceptions import HSMOperationError, HSMUnsupportedError
from .base import PKCS11PrivateKeyMixin

if TYPE_CHECKING:
    from pkcs11 import Session


# Mapping of curve names to cryptography curve classes
CURVE_CLASSES: dict[str, type[ec.EllipticCurve]] = {
    "secp256r1": ec.SECP256R1,
    "secp384r1": ec.SECP384R1,
    "secp521r1": ec.SECP521R1,
    "secp256k1": ec.SECP256K1,
    "brainpoolP256r1": ec.BrainpoolP256R1,
    "brainpoolP384r1": ec.BrainpoolP384R1,
    "brainpoolP512r1": ec.BrainpoolP512R1,
}

# Key sizes for each curve (in bytes for signature components)
CURVE_KEY_SIZES: dict[str, int] = {
    "secp256r1": 32,
    "secp384r1": 48,
    "secp521r1": 66,
    "secp256k1": 32,
    "brainpoolP256r1": 32,
    "brainpoolP320r1": 40,
    "brainpoolP384r1": 48,
    "brainpoolP512r1": 64,
}


def _int_to_bytes(value: int, length: int) -> bytes:
    """Convert integer to fixed-length big-endian bytes."""
    return value.to_bytes(length, "big")


def _bytes_to_int(data: bytes) -> int:
    """Convert big-endian bytes to integer."""
    return int.from_bytes(data, "big")


class PKCS11EllipticCurvePrivateKey(PKCS11PrivateKeyMixin, ec.EllipticCurvePrivateKey):
    """Elliptic Curve private key backed by HSM.

    This class implements the cryptography library's EllipticCurvePrivateKey
    interface while performing all cryptographic operations on the HSM.
    """

    _key_type = KeyType.EC

    def __init__(
        self,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> None:
        """Initialize HSM EC private key.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
        """
        PKCS11PrivateKeyMixin.__init__(self, session, key_id, key_label)
        self._curve: ec.EllipticCurve | None = None

    @property
    def curve(self) -> ec.EllipticCurve:
        """Return the curve used by this key."""
        if self._curve is None:
            ec_params = bytes(self.pkcs11_public_key[Attribute.EC_PARAMS])
            curve_name = OID_TO_CURVE.get(ec_params)
            if curve_name is None:
                # Try to find by substring match for some HSM implementations
                for oid, name in OID_TO_CURVE.items():
                    if oid in ec_params or ec_params in oid:
                        curve_name = name
                        break

            if curve_name is None:
                raise ValueError(f"Unknown curve OID: {ec_params.hex()}")

            curve_class = CURVE_CLASSES.get(curve_name)
            if curve_class is None:
                raise ValueError(f"Unsupported curve: {curve_name}")

            self._curve = curve_class()
        return self._curve

    @property
    def key_size(self) -> int:
        """Return key size in bits."""
        return self.curve.key_size

    def public_key(self) -> "PKCS11EllipticCurvePublicKey":
        """Return the public key corresponding to this private key."""
        return PKCS11EllipticCurvePublicKey.from_pkcs11_key(
            self._session,
            self.pkcs11_public_key,
            self._key_id,
            self._key_label,
        )

    def sign(
        self,
        data: bytes,
        signature_algorithm: ec.EllipticCurveSignatureAlgorithm,
    ) -> bytes:
        """Sign data using ECDSA.

        Args:
            data: Data to sign
            signature_algorithm: Signature algorithm (ECDSA with hash)

        Returns:
            DER-encoded signature

        Raises:
            HSMOperationError: If signing fails
        """
        if not isinstance(signature_algorithm, ec.ECDSA):
            raise ValueError(f"Unsupported signature algorithm: {type(signature_algorithm)}")

        algorithm = signature_algorithm.algorithm

        # Pre-hash the data if not already prehashed
        if isinstance(algorithm, Prehashed):
            hash_data = data
        else:
            from cryptography.hazmat.primitives.hashes import Hash
            from cryptography.hazmat.backends import default_backend

            h = Hash(algorithm, backend=default_backend())
            h.update(data)
            hash_data = h.finalize()

        try:
            # PKCS#11 ECDSA returns raw signature (r || s)
            raw_signature = self.pkcs11_private_key.sign(
                hash_data,
                mechanism=Mechanism.ECDSA,
            )
            raw_signature = bytes(raw_signature)

            # Convert raw signature to DER format
            # Raw signature is r || s, each component is curve key size bytes
            curve_name = normalize_curve_name(self.curve.name)
            component_size = CURVE_KEY_SIZES.get(curve_name, len(raw_signature) // 2)

            r = _bytes_to_int(raw_signature[:component_size])
            s = _bytes_to_int(raw_signature[component_size:])

            return encode_dss_signature(r, s)

        except Exception as e:
            raise HSMOperationError(f"ECDSA signing failed: {e}") from e

    def exchange(
        self,
        algorithm: ec.ECDH,
        peer_public_key: ec.EllipticCurvePublicKey,
    ) -> bytes:
        """Perform ECDH key exchange.

        Args:
            algorithm: ECDH algorithm
            peer_public_key: Peer's public key

        Returns:
            Shared secret

        Raises:
            HSMOperationError: If key exchange fails
        """
        try:
            # Get peer public key in uncompressed point format
            peer_bytes = peer_public_key.public_bytes(
                serialization.Encoding.X962,
                serialization.PublicFormat.UncompressedPoint,
            )

            # Perform ECDH on HSM
            shared_secret = self.pkcs11_private_key.derive_key(
                KeyType.GENERIC_SECRET,
                self.key_size // 8,
                mechanism=Mechanism.ECDH1_DERIVE,
                mechanism_param=peer_bytes,
            )

            # Extract the key value
            return bytes(shared_secret[Attribute.VALUE])

        except Exception as e:
            raise HSMOperationError(f"ECDH key exchange failed: {e}") from e

    def private_numbers(self) -> ec.EllipticCurvePrivateNumbers:
        """Not supported for HSM keys."""
        self._raise_unsupported("private_numbers()")

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


class PKCS11EllipticCurvePublicKey(ec.EllipticCurvePublicKey):
    """Elliptic Curve public key from HSM.

    This class wraps the public key data extracted from HSM and provides
    the standard cryptography library interface.
    """

    def __init__(
        self,
        curve: ec.EllipticCurve,
        x: int,
        y: int,
    ) -> None:
        """Initialize EC public key.

        Args:
            curve: Elliptic curve
            x: X coordinate
            y: Y coordinate
        """
        self._curve = curve
        self._x = x
        self._y = y
        # Create internal cryptography public key for operations
        self._crypto_key = ec.EllipticCurvePublicNumbers(
            x=x,
            y=y,
            curve=curve,
        ).public_key()

    @classmethod
    def from_pkcs11_key(
        cls,
        session: "Session",
        pkcs11_key,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> "PKCS11EllipticCurvePublicKey":
        """Create public key from PKCS#11 public key object.

        Args:
            session: PKCS#11 session
            pkcs11_key: PKCS#11 public key object
            key_id: Key ID
            key_label: Key label

        Returns:
            PKCS11EllipticCurvePublicKey instance
        """
        # Get curve from EC_PARAMS
        ec_params = bytes(pkcs11_key[Attribute.EC_PARAMS])
        curve_name = OID_TO_CURVE.get(ec_params)

        if curve_name is None:
            # Try substring match
            for oid, name in OID_TO_CURVE.items():
                if oid in ec_params or ec_params in oid:
                    curve_name = name
                    break

        if curve_name is None:
            raise ValueError(f"Unknown curve OID: {ec_params.hex()}")

        curve_class = CURVE_CLASSES.get(curve_name)
        if curve_class is None:
            raise ValueError(f"Unsupported curve: {curve_name}")

        curve = curve_class()

        # Get EC_POINT (uncompressed point format: 04 || x || y)
        ec_point = bytes(pkcs11_key[Attribute.EC_POINT])

        # EC_POINT in PKCS#11 is typically wrapped in a DER OCTET STRING
        # Format: 04 <length> 04 <x> <y>
        # where 04 is OCTET STRING tag, <length> is the length byte(s),
        # and the content is the uncompressed point (04 || x || y)
        point_data = ec_point

        # Check if wrapped in OCTET STRING (tag 0x04)
        if point_data[0] == 0x04 and len(point_data) > 2:
            # Parse DER length
            length_byte = point_data[1]
            if length_byte < 0x80:
                # Short form length
                content_start = 2
            elif length_byte == 0x81:
                # Long form, 1 length byte
                content_start = 3
            elif length_byte == 0x82:
                # Long form, 2 length bytes
                content_start = 4
            else:
                content_start = 0  # Assume no wrapping

            if content_start > 0:
                inner_data = point_data[content_start:]
                # Check if inner data starts with uncompressed point marker
                if inner_data[0] == 0x04:
                    point_data = inner_data

        # Now point_data should be: 04 || x || y
        if point_data[0] != 0x04:
            raise ValueError(f"Expected uncompressed point format, got: {point_data[:5].hex()}")

        # Remove the 0x04 marker
        coord_bytes = point_data[1:]

        # Split into x and y coordinates
        coord_size = len(coord_bytes) // 2
        x = _bytes_to_int(coord_bytes[:coord_size])
        y = _bytes_to_int(coord_bytes[coord_size:])

        return cls(curve, x, y)

    @property
    def curve(self) -> ec.EllipticCurve:
        """Return the curve."""
        return self._curve

    @property
    def key_size(self) -> int:
        """Return key size in bits."""
        return self._curve.key_size

    def public_numbers(self) -> ec.EllipticCurvePublicNumbers:
        """Return EC public numbers."""
        return ec.EllipticCurvePublicNumbers(
            x=self._x,
            y=self._y,
            curve=self._curve,
        )

    def public_bytes(
        self,
        encoding: serialization.Encoding,
        format: serialization.PublicFormat,
    ) -> bytes:
        """Serialize public key."""
        return self._crypto_key.public_bytes(encoding, format)

    def public_bytes_raw(self) -> bytes:
        """Return raw public key bytes (uncompressed point without 0x04 prefix)."""
        return self._crypto_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )[1:]  # Remove 0x04 prefix

    def verify(
        self,
        signature: bytes,
        data: bytes,
        signature_algorithm: ec.EllipticCurveSignatureAlgorithm,
    ) -> None:
        """Verify a signature.

        Args:
            signature: DER-encoded signature
            data: Original data
            signature_algorithm: Signature algorithm

        Raises:
            InvalidSignature: If verification fails
        """
        self._crypto_key.verify(signature, data, signature_algorithm)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, (PKCS11EllipticCurvePublicKey, ec.EllipticCurvePublicKey)):
            return False
        other_numbers = other.public_numbers()
        return (
            self._x == other_numbers.x
            and self._y == other_numbers.y
            and self._curve.name == other_numbers.curve.name
        )

    def __hash__(self) -> int:
        """Hash based on key parameters."""
        return hash((self._x, self._y, self._curve.name))

    def __copy__(self) -> "PKCS11EllipticCurvePublicKey":
        """Create a copy."""
        return PKCS11EllipticCurvePublicKey(self._curve, self._x, self._y)

    def __deepcopy__(self, memo: dict) -> "PKCS11EllipticCurvePublicKey":
        """Create a deep copy."""
        return self.__copy__()
