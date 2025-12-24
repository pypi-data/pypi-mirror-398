"""PKCS#11 session management for hsmkey module."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import pkcs11
from pkcs11 import KeyType, Mechanism, ObjectClass

from .exceptions import (
    HSMKeyNotFoundError,
    HSMPinError,
    HSMSessionError,
)

if TYPE_CHECKING:
    from pkcs11 import Session, Token


class SessionPool:
    """Thread-safe pool for PKCS#11 sessions.

    This class manages PKCS#11 library instances and sessions,
    providing thread-safe access with reference counting.
    """

    _lib_cache: dict[str, pkcs11.lib] = {}
    _lib_lock = threading.Lock()

    def __init__(
        self,
        module_path: str,
        token_label: str,
        user_pin: str | None = None,
        so_pin: str | None = None,
    ) -> None:
        """Initialize session pool.

        Args:
            module_path: Path to PKCS#11 library
            token_label: Label of token to use
            user_pin: User PIN for authentication
            so_pin: Security Officer PIN for admin operations
        """
        self.module_path = module_path
        self.token_label = token_label
        self.user_pin = user_pin
        self.so_pin = so_pin
        self._session: Session | None = None
        self._lock = threading.Lock()

    def _get_lib(self) -> pkcs11.lib:
        """Get or create PKCS#11 library instance."""
        with self._lib_lock:
            if self.module_path not in self._lib_cache:
                try:
                    self._lib_cache[self.module_path] = pkcs11.lib(self.module_path)
                except Exception as e:
                    raise HSMSessionError(
                        f"Failed to load PKCS#11 library: {e}"
                    ) from e
            return self._lib_cache[self.module_path]

    def _get_token(self) -> Token:
        """Get token by label."""
        lib = self._get_lib()
        try:
            return lib.get_token(token_label=self.token_label)
        except pkcs11.NoSuchToken as e:
            raise HSMSessionError(
                f"Token not found: {self.token_label}"
            ) from e

    def open_session(self, rw: bool = False) -> Session:
        """Open a new PKCS#11 session.

        Args:
            rw: Whether to open read-write session

        Returns:
            PKCS#11 session

        Raises:
            HSMPinError: If PIN authentication fails
            HSMSessionError: If session cannot be opened
        """
        token = self._get_token()

        try:
            # Login is done via token.open() with user_pin or so_pin
            if self.so_pin:
                session = token.open(rw=rw, so_pin=self.so_pin)
            elif self.user_pin:
                session = token.open(rw=rw, user_pin=self.user_pin)
            else:
                session = token.open(rw=rw)

            return session

        except pkcs11.PinIncorrect as e:
            raise HSMPinError("PIN incorrect") from e
        except pkcs11.PKCS11Error as e:
            raise HSMSessionError(f"Failed to open session: {e}") from e

    @contextmanager
    def session(self, rw: bool = False) -> Iterator[Session]:
        """Context manager for PKCS#11 session.

        Args:
            rw: Whether to open read-write session

        Yields:
            PKCS#11 session

        Example:
            with pool.session() as session:
                key = session.get_key(...)
        """
        session = self.open_session(rw=rw)
        try:
            yield session
        finally:
            # python-pkcs11 handles logout automatically when closing
            # the session that was opened with user_pin/so_pin
            session.close()

    def get_private_key(
        self,
        session: Session,
        key_type: KeyType,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> pkcs11.PrivateKey:
        """Get private key from HSM.

        Args:
            session: PKCS#11 session
            key_type: Type of key (RSA, EC, EC_EDWARDS)
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)

        Returns:
            PKCS#11 private key object

        Raises:
            HSMKeyNotFoundError: If key not found
        """
        try:
            return session.get_key(
                key_type=key_type,
                object_class=ObjectClass.PRIVATE_KEY,
                id=key_id,
                label=key_label,
            )
        except pkcs11.NoSuchKey as e:
            raise HSMKeyNotFoundError(
                f"Private key not found: id={key_id}, label={key_label}"
            ) from e

    def get_public_key(
        self,
        session: Session,
        key_type: KeyType,
        key_id: bytes | None = None,
        key_label: str | None = None,
    ) -> pkcs11.PublicKey:
        """Get public key from HSM.

        Args:
            session: PKCS#11 session
            key_type: Type of key (RSA, EC, EC_EDWARDS)
            key_id: Key ID (CKA_ID)
            key_label: Key label (CKA_LABEL)

        Returns:
            PKCS#11 public key object

        Raises:
            HSMKeyNotFoundError: If key not found
        """
        try:
            return session.get_key(
                key_type=key_type,
                object_class=ObjectClass.PUBLIC_KEY,
                id=key_id,
                label=key_label,
            )
        except pkcs11.NoSuchKey as e:
            raise HSMKeyNotFoundError(
                f"Public key not found: id={key_id}, label={key_label}"
            ) from e
