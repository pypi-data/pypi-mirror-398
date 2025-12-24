"""Base classes for HSM-backed keys."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from pkcs11 import KeyType, ObjectClass

from ..exceptions import HSMKeyNotFoundError, HSMUnsupportedError

if TYPE_CHECKING:
    from pkcs11 import PrivateKey, PublicKey, Session


class PKCS11PrivateKeyMixin:
    """Mixin class for PKCS#11-backed private keys.

    This mixin provides common functionality for all HSM-backed private keys,
    including lazy loading of PKCS#11 key objects and session management.
    """

    # Subclasses should set this
    _key_type: KeyType

    def __init__(
        self,
        session: Session,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> None:
        """Initialize HSM private key.

        Args:
            session: PKCS#11 session
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)
        """
        self._session = session
        self._key_id = key_id
        self._key_label = key_label
        self._pkcs11_private_key: PrivateKey | None = None
        self._pkcs11_public_key: PublicKey | None = None

    @property
    def pkcs11_private_key(self) -> PrivateKey:
        """Get PKCS#11 private key object (lazy-loaded)."""
        if self._pkcs11_private_key is None:
            try:
                self._pkcs11_private_key = self._session.get_key(
                    key_type=self._key_type,
                    object_class=ObjectClass.PRIVATE_KEY,
                    id=self._key_id,
                    label=self._key_label,
                )
            except Exception as e:
                raise HSMKeyNotFoundError(
                    f"Private key not found: id={self._key_id}, label={self._key_label}"
                ) from e
        return self._pkcs11_private_key

    @property
    def pkcs11_public_key(self) -> PublicKey:
        """Get PKCS#11 public key object (lazy-loaded)."""
        if self._pkcs11_public_key is None:
            try:
                self._pkcs11_public_key = self._session.get_key(
                    key_type=self._key_type,
                    object_class=ObjectClass.PUBLIC_KEY,
                    id=self._key_id,
                    label=self._key_label,
                )
            except Exception as e:
                raise HSMKeyNotFoundError(
                    f"Public key not found: id={self._key_id}, label={self._key_label}"
                ) from e
        return self._pkcs11_public_key

    def __copy__(self) -> "PKCS11PrivateKeyMixin":
        """Create a shallow copy of the key."""
        new_key = self.__class__.__new__(self.__class__)
        new_key._session = self._session
        new_key._key_id = self._key_id
        new_key._key_label = self._key_label
        new_key._pkcs11_private_key = None
        new_key._pkcs11_public_key = None
        return new_key

    def __deepcopy__(self, memo: dict) -> "PKCS11PrivateKeyMixin":
        """Create a deep copy of the key (same as shallow for HSM keys)."""
        return self.__copy__()

    def __eq__(self, other: object) -> bool:
        """Check equality based on key identifiers."""
        if not isinstance(other, PKCS11PrivateKeyMixin):
            return False
        return (
            self._key_type == other._key_type
            and self._key_id == other._key_id
            and self._key_label == other._key_label
        )

    def __hash__(self) -> int:
        """Hash based on key identifiers."""
        return hash((self._key_type, self._key_id, self._key_label))

    def _raise_unsupported(self, operation: str) -> None:
        """Raise HSMUnsupportedError for unsupported operations."""
        raise HSMUnsupportedError(
            f"{operation} is not supported for HSM-backed keys. "
            "Private key material cannot be extracted from the HSM."
        )
