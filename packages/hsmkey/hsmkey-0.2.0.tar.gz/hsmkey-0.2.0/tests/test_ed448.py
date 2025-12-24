"""Tests for Ed448 key implementations."""

from __future__ import annotations

import copy

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from hsmkey import (
    PKCS11Ed448PrivateKey,
    PKCS11Ed448PublicKey,
    HSMUnsupportedError,
)


class TestPKCS11Ed448PrivateKey:
    """Tests for PKCS11Ed448PrivateKey."""

    def test_public_key(self, hsm_session, ed448_key_id):
        """Test public key extraction."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()
        assert isinstance(public_key, PKCS11Ed448PublicKey)

    def test_sign(self, hsm_session, ed448_key_id):
        """Test Ed448 signing."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        data = b"test data for Ed448 signing"

        signature = key.sign(data)

        assert isinstance(signature, bytes)
        assert len(signature) == 114  # Ed448 signatures are 114 bytes

    def test_sign_verify_roundtrip(self, hsm_session, ed448_key_id):
        """Test sign and verify roundtrip."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()

        data = b"test message"
        signature = key.sign(data)

        # Should not raise
        public_key.verify(signature, data)

    def test_sign_deterministic(self, hsm_session, ed448_key_id):
        """Test that Ed448 signatures are deterministic."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        data = b"deterministic test"

        sig1 = key.sign(data)
        sig2 = key.sign(data)

        assert sig1 == sig2

    def test_sign_different_messages(self, hsm_session, ed448_key_id):
        """Test signing different messages produces different signatures."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)

        sig1 = key.sign(b"message 1")
        sig2 = key.sign(b"message 2")

        assert sig1 != sig2

    def test_invalid_signature_fails(self, hsm_session, ed448_key_id):
        """Test that invalid signature verification fails."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()

        data = b"test data"
        signature = key.sign(data)

        # Verify with wrong data should fail
        with pytest.raises(InvalidSignature):
            public_key.verify(signature, b"wrong data")

        # Verify with corrupted signature should fail
        corrupted_sig = bytes([signature[0] ^ 0xFF]) + signature[1:]
        with pytest.raises(InvalidSignature):
            public_key.verify(corrupted_sig, data)

    def test_private_bytes_raises(self, hsm_session, ed448_key_id):
        """Test that private_bytes() raises HSMUnsupportedError."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )

    def test_private_bytes_raw_raises(self, hsm_session, ed448_key_id):
        """Test that private_bytes_raw() raises HSMUnsupportedError."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_bytes_raw()

    def test_key_equality(self, hsm_session, ed448_key_id):
        """Test key equality."""
        key1 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        key2 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)

        assert key1 == key2

    def test_key_copy(self, hsm_session, ed448_key_id):
        """Test key copying."""
        key1 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        key2 = copy.copy(key1)

        assert key1 == key2
        assert key1 is not key2


class TestPKCS11Ed448PublicKey:
    """Tests for PKCS11Ed448PublicKey."""

    def test_public_bytes_raw(self, hsm_session, ed448_key_id):
        """Test public key raw bytes."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()

        raw = public_key.public_bytes_raw()
        assert len(raw) == 57  # Ed448 public keys are 57 bytes

    def test_public_bytes_pem(self, hsm_session, ed448_key_id):
        """Test public key PEM serialization."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()

        pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")

    def test_public_bytes_der(self, hsm_session, ed448_key_id):
        """Test public key DER serialization."""
        key = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id)
        public_key = key.public_key()

        der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert isinstance(der, bytes)
        assert len(der) > 0

    def test_public_key_equality(self, hsm_session, ed448_key_id):
        """Test public key equality."""
        key1 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id).public_key()
        key2 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id).public_key()

        assert key1 == key2

    def test_public_key_hash(self, hsm_session, ed448_key_id):
        """Test public key hashing."""
        key1 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id).public_key()
        key2 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id).public_key()

        assert hash(key1) == hash(key2)

    def test_public_key_copy(self, hsm_session, ed448_key_id):
        """Test public key copying."""
        key1 = PKCS11Ed448PrivateKey(hsm_session, key_id=ed448_key_id).public_key()
        key2 = copy.copy(key1)
        key3 = copy.deepcopy(key1)

        assert key1 == key2
        assert key1 == key3
