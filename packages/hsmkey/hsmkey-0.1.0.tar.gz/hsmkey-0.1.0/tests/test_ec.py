"""Tests for Elliptic Curve key implementations."""

from __future__ import annotations

import copy

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from hsmkey import (
    PKCS11EllipticCurvePrivateKey,
    PKCS11EllipticCurvePublicKey,
    HSMUnsupportedError,
)


class TestPKCS11EllipticCurvePrivateKey:
    """Tests for PKCS11EllipticCurvePrivateKey."""

    def test_curve_p256(self, hsm_session, ec_p256_key_id):
        """Test P-256 curve detection."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        assert isinstance(key.curve, ec.SECP256R1)
        assert key.key_size == 256

    def test_curve_p384(self, hsm_session, ec_p384_key_id):
        """Test P-384 curve detection."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p384_key_id)
        assert isinstance(key.curve, ec.SECP384R1)
        assert key.key_size == 384

    def test_curve_p521(self, hsm_session, ec_p521_key_id):
        """Test P-521 curve detection."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p521_key_id)
        assert isinstance(key.curve, ec.SECP521R1)
        assert key.key_size == 521

    def test_public_key(self, hsm_session, ec_p256_key_id):
        """Test public key extraction."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()
        assert isinstance(public_key, PKCS11EllipticCurvePublicKey)
        assert isinstance(public_key.curve, ec.SECP256R1)

    def test_sign_es256(self, hsm_session, ec_p256_key_id):
        """Test ES256 signing (ECDSA P-256 with SHA-256)."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        data = b"test data for ECDSA signing"

        signature = key.sign(data, ec.ECDSA(hashes.SHA256()))

        assert isinstance(signature, bytes)
        assert len(signature) > 0  # DER-encoded, variable length

        # Verify signature
        public_key = key.public_key()
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))

    def test_sign_es384(self, hsm_session, ec_p384_key_id):
        """Test ES384 signing (ECDSA P-384 with SHA-384)."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p384_key_id)
        data = b"test data for ECDSA signing"

        signature = key.sign(data, ec.ECDSA(hashes.SHA384()))

        public_key = key.public_key()
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA384()))

    def test_sign_es512(self, hsm_session, ec_p521_key_id):
        """Test ES512 signing (ECDSA P-521 with SHA-512)."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p521_key_id)
        data = b"test data for ECDSA signing"

        signature = key.sign(data, ec.ECDSA(hashes.SHA512()))

        public_key = key.public_key()
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA512()))

    def test_sign_verify_roundtrip(self, hsm_session, ec_p256_key_id):
        """Test sign and verify roundtrip."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        messages = [
            b"short",
            b"a" * 1000,
            b"\x00\x01\x02\x03",
            b"unicode: \xc3\xa9\xc3\xa0\xc3\xbc",
        ]

        for msg in messages:
            signature = key.sign(msg, ec.ECDSA(hashes.SHA256()))
            public_key.verify(signature, msg, ec.ECDSA(hashes.SHA256()))

    def test_invalid_signature_fails(self, hsm_session, ec_p256_key_id):
        """Test that invalid signature verification fails."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        data = b"test data"
        signature = key.sign(data, ec.ECDSA(hashes.SHA256()))

        # Verify with wrong data should fail
        with pytest.raises(InvalidSignature):
            public_key.verify(signature, b"wrong data", ec.ECDSA(hashes.SHA256()))

    def test_private_numbers_raises(self, hsm_session, ec_p256_key_id):
        """Test that private_numbers() raises HSMUnsupportedError."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_numbers()

    def test_private_bytes_raises(self, hsm_session, ec_p256_key_id):
        """Test that private_bytes() raises HSMUnsupportedError."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )

    def test_key_equality(self, hsm_session, ec_p256_key_id, ec_p384_key_id):
        """Test key equality."""
        key1 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        key2 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        key3 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p384_key_id)

        assert key1 == key2
        assert key1 != key3

    def test_key_copy(self, hsm_session, ec_p256_key_id):
        """Test key copying."""
        key1 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        key2 = copy.copy(key1)

        assert key1 == key2
        assert key1 is not key2


class TestPKCS11EllipticCurvePublicKey:
    """Tests for PKCS11EllipticCurvePublicKey."""

    def test_public_numbers(self, hsm_session, ec_p256_key_id):
        """Test public numbers extraction."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        numbers = public_key.public_numbers()
        assert isinstance(numbers.curve, ec.SECP256R1)
        assert numbers.x > 0
        assert numbers.y > 0

    def test_public_bytes_pem(self, hsm_session, ec_p256_key_id):
        """Test public key PEM serialization."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")

    def test_public_bytes_der(self, hsm_session, ec_p256_key_id):
        """Test public key DER serialization."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert isinstance(der, bytes)
        assert len(der) > 0

    def test_public_bytes_raw(self, hsm_session, ec_p256_key_id):
        """Test public key raw bytes."""
        key = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id)
        public_key = key.public_key()

        raw = public_key.public_bytes_raw()
        # P-256: 32 bytes x + 32 bytes y = 64 bytes
        assert len(raw) == 64

    def test_public_key_equality(self, hsm_session, ec_p256_key_id, ec_p384_key_id):
        """Test public key equality."""
        key1 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id).public_key()
        key2 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id).public_key()
        key3 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p384_key_id).public_key()

        assert key1 == key2
        assert key1 != key3

    def test_public_key_copy(self, hsm_session, ec_p256_key_id):
        """Test public key copying."""
        key1 = PKCS11EllipticCurvePrivateKey(hsm_session, key_id=ec_p256_key_id).public_key()
        key2 = copy.copy(key1)
        key3 = copy.deepcopy(key1)

        assert key1 == key2
        assert key1 == key3
