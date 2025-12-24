"""RSA key implementations backed by HSM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from pkcs11 import Attribute, KeyType, Mechanism

from ..algorithms import get_rsa_encrypt_mechanism, get_rsa_sign_mechanism
from ..exceptions import HSMOperationError, HSMUnsupportedError
from .base import PKCS11PrivateKeyMixin

if TYPE_CHECKING:
    from pkcs11 import Session


class PKCS11RSAPrivateKey(PKCS11PrivateKeyMixin, rsa.RSAPrivateKey):
    """RSA private key backed by HSM.

    This class implements the cryptography library's RSAPrivateKey interface
    while performing all cryptographic operations on the HSM.
    """

    _key_type = KeyType.RSA

    def __init__(
        self,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> None:
        """Initialize HSM RSA private key.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
        """
        PKCS11PrivateKeyMixin.__init__(self, session, key_id, key_label)
        self._key_size: int | None = None

    @property
    def key_size(self) -> int:
        """Return key size in bits."""
        if self._key_size is None:
            # Get modulus bits from public key
            modulus = self.pkcs11_public_key[Attribute.MODULUS]
            self._key_size = len(modulus) * 8
        return self._key_size

    def public_key(self) -> "PKCS11RSAPublicKey":
        """Return the public key corresponding to this private key."""
        return PKCS11RSAPublicKey.from_pkcs11_key(
            self._session,
            self.pkcs11_public_key,
            self._key_id,
            self._key_label,
        )

    def sign(
        self,
        data: bytes,
        padding_instance: padding.AsymmetricPadding,
        algorithm: hashes.HashAlgorithm | Prehashed,
    ) -> bytes:
        """Sign data using this key.

        Args:
            data: Data to sign
            padding_instance: Padding scheme (PKCS1v15 or PSS)
            algorithm: Hash algorithm or Prehashed instance

        Returns:
            Signature bytes

        Raises:
            HSMOperationError: If signing fails
            ValueError: If unsupported padding or algorithm
        """
        # Handle prehashed data
        if isinstance(algorithm, Prehashed):
            # For prehashed, we need to use raw RSA mechanism
            # and the data is already the hash
            actual_algorithm = algorithm._algorithm
        else:
            actual_algorithm = algorithm

        mechanism, mechanism_param = get_rsa_sign_mechanism(
            padding_instance, actual_algorithm
        )

        try:
            if mechanism_param is not None:
                signature = self.pkcs11_private_key.sign(
                    data,
                    mechanism=mechanism,
                    mechanism_param=mechanism_param,
                )
            else:
                signature = self.pkcs11_private_key.sign(
                    data,
                    mechanism=mechanism,
                )
            return bytes(signature)
        except Exception as e:
            raise HSMOperationError(f"RSA signing failed: {e}") from e

    def decrypt(
        self,
        ciphertext: bytes,
        padding_instance: padding.AsymmetricPadding,
    ) -> bytes:
        """Decrypt data using this key.

        Args:
            ciphertext: Data to decrypt
            padding_instance: Padding scheme (PKCS1v15 or OAEP)

        Returns:
            Decrypted plaintext

        Raises:
            HSMOperationError: If decryption fails
            ValueError: If unsupported padding
        """
        mechanism, mechanism_param = get_rsa_encrypt_mechanism(padding_instance)

        try:
            if mechanism_param is not None:
                plaintext = self.pkcs11_private_key.decrypt(
                    ciphertext,
                    mechanism=mechanism,
                    mechanism_param=mechanism_param,
                )
            else:
                plaintext = self.pkcs11_private_key.decrypt(
                    ciphertext,
                    mechanism=mechanism,
                )
            return bytes(plaintext)
        except Exception as e:
            raise HSMOperationError(f"RSA decryption failed: {e}") from e

    def private_numbers(self) -> rsa.RSAPrivateNumbers:
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


class PKCS11RSAPublicKey(rsa.RSAPublicKey):
    """RSA public key from HSM.

    This class wraps the public key data extracted from HSM and provides
    the standard cryptography library interface.
    """

    def __init__(
        self,
        modulus: int,
        public_exponent: int,
        key_size: int,
    ) -> None:
        """Initialize RSA public key.

        Args:
            modulus: RSA modulus (n)
            public_exponent: Public exponent (e)
            key_size: Key size in bits
        """
        self._modulus = modulus
        self._public_exponent = public_exponent
        self._key_size = key_size
        # Create internal cryptography public key for operations
        self._crypto_key = rsa.RSAPublicNumbers(
            e=public_exponent,
            n=modulus,
        ).public_key()

    @classmethod
    def from_pkcs11_key(
        cls,
        session: "Session",
        pkcs11_key,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> "PKCS11RSAPublicKey":
        """Create public key from PKCS#11 public key object.

        Args:
            session: PKCS#11 session
            pkcs11_key: PKCS#11 public key object
            key_id: Key ID
            key_label: Key label

        Returns:
            PKCS11RSAPublicKey instance
        """
        modulus_bytes = pkcs11_key[Attribute.MODULUS]
        exponent_bytes = pkcs11_key[Attribute.PUBLIC_EXPONENT]

        modulus = int.from_bytes(modulus_bytes, "big")
        exponent = int.from_bytes(exponent_bytes, "big")
        key_size = len(modulus_bytes) * 8

        return cls(modulus, exponent, key_size)

    @property
    def key_size(self) -> int:
        """Return key size in bits."""
        return self._key_size

    def public_numbers(self) -> rsa.RSAPublicNumbers:
        """Return RSA public numbers."""
        return rsa.RSAPublicNumbers(
            e=self._public_exponent,
            n=self._modulus,
        )

    def public_bytes(
        self,
        encoding: serialization.Encoding,
        format: serialization.PublicFormat,
    ) -> bytes:
        """Serialize public key."""
        return self._crypto_key.public_bytes(encoding, format)

    def public_bytes_raw(self) -> bytes:
        """Not applicable for RSA keys."""
        raise TypeError("public_bytes_raw() not supported for RSA keys")

    def verify(
        self,
        signature: bytes,
        data: bytes,
        padding_instance: padding.AsymmetricPadding,
        algorithm: hashes.HashAlgorithm | Prehashed,
    ) -> None:
        """Verify a signature.

        Args:
            signature: Signature to verify
            data: Original data
            padding_instance: Padding scheme
            algorithm: Hash algorithm

        Raises:
            InvalidSignature: If verification fails
        """
        self._crypto_key.verify(signature, data, padding_instance, algorithm)

    def encrypt(
        self,
        plaintext: bytes,
        padding_instance: padding.AsymmetricPadding,
    ) -> bytes:
        """Encrypt data using this public key.

        Args:
            plaintext: Data to encrypt
            padding_instance: Padding scheme

        Returns:
            Ciphertext
        """
        return self._crypto_key.encrypt(plaintext, padding_instance)

    def recover_data_from_signature(
        self,
        signature: bytes,
        padding_instance: padding.AsymmetricPadding,
        algorithm: hashes.HashAlgorithm | None,
    ) -> bytes:
        """Recover data from a signature (signature recovery).

        Args:
            signature: The signature
            padding_instance: Padding scheme
            algorithm: Hash algorithm (or None for no hashing)

        Returns:
            Recovered data
        """
        return self._crypto_key.recover_data_from_signature(
            signature, padding_instance, algorithm
        )

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, (PKCS11RSAPublicKey, rsa.RSAPublicKey)):
            return False
        other_numbers = other.public_numbers()
        return (
            self._modulus == other_numbers.n
            and self._public_exponent == other_numbers.e
        )

    def __hash__(self) -> int:
        """Hash based on key parameters."""
        return hash((self._modulus, self._public_exponent))

    def __copy__(self) -> "PKCS11RSAPublicKey":
        """Create a copy."""
        return PKCS11RSAPublicKey(
            self._modulus,
            self._public_exponent,
            self._key_size,
        )

    def __deepcopy__(self, memo: dict) -> "PKCS11RSAPublicKey":
        """Create a deep copy."""
        return self.__copy__()
