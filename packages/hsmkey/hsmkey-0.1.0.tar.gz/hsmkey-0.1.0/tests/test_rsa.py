"""Tests for RSA key implementations."""

from __future__ import annotations

import copy

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from hsmkey import (
    PKCS11RSAPrivateKey,
    PKCS11RSAPublicKey,
    HSMOperationError,
    HSMUnsupportedError,
)


class TestPKCS11RSAPrivateKey:
    """Tests for PKCS11RSAPrivateKey."""

    def test_key_size_2048(self, hsm_session, rsa_2048_key_id):
        """Test RSA 2048-bit key size property."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        assert key.key_size == 2048

    def test_key_size_3072(self, hsm_session, rsa_3072_key_id):
        """Test RSA 3072-bit key size property."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_3072_key_id)
        assert key.key_size == 3072

    def test_key_size_4096(self, hsm_session, rsa_4096_key_id):
        """Test RSA 4096-bit key size property."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_4096_key_id)
        assert key.key_size == 4096

    def test_public_key(self, hsm_session, rsa_2048_key_id):
        """Test public key extraction."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()
        assert isinstance(public_key, PKCS11RSAPublicKey)
        assert public_key.key_size == 2048

    def test_sign_pkcs1v15_sha256(self, hsm_session, rsa_2048_key_id):
        """Test RS256 signing (PKCS#1 v1.5 with SHA-256)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        data = b"test data for signing"

        signature = key.sign(data, padding.PKCS1v15(), hashes.SHA256())

        assert len(signature) == 2048 // 8  # 256 bytes
        assert isinstance(signature, bytes)

        # Verify signature
        public_key = key.public_key()
        public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())

    def test_sign_pkcs1v15_sha384(self, hsm_session, rsa_3072_key_id):
        """Test RS384 signing (PKCS#1 v1.5 with SHA-384)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_3072_key_id)
        data = b"test data for signing"

        signature = key.sign(data, padding.PKCS1v15(), hashes.SHA384())

        assert len(signature) == 3072 // 8  # 384 bytes
        public_key = key.public_key()
        public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA384())

    def test_sign_pkcs1v15_sha512(self, hsm_session, rsa_4096_key_id):
        """Test RS512 signing (PKCS#1 v1.5 with SHA-512)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_4096_key_id)
        data = b"test data for signing"

        signature = key.sign(data, padding.PKCS1v15(), hashes.SHA512())

        assert len(signature) == 4096 // 8  # 512 bytes
        public_key = key.public_key()
        public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA512())

    def test_sign_pss_sha256(self, hsm_session, rsa_2048_key_id):
        """Test PS256 signing (PSS with SHA-256)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        data = b"test data for PSS signing"

        pss_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.AUTO,
        )
        signature = key.sign(data, pss_padding, hashes.SHA256())

        assert len(signature) == 2048 // 8
        public_key = key.public_key()
        # Use MAX_LENGTH for verification as AUTO may differ
        verify_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        )
        public_key.verify(signature, data, verify_padding, hashes.SHA256())

    def test_sign_pss_sha384(self, hsm_session, rsa_3072_key_id):
        """Test PS384 signing (PSS with SHA-384)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_3072_key_id)
        data = b"test data for PSS signing"

        pss_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA384()),
            salt_length=padding.PSS.AUTO,
        )
        signature = key.sign(data, pss_padding, hashes.SHA384())

        assert len(signature) == 3072 // 8
        public_key = key.public_key()
        verify_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA384()),
            salt_length=padding.PSS.MAX_LENGTH,
        )
        public_key.verify(signature, data, verify_padding, hashes.SHA384())

    def test_sign_pss_sha512(self, hsm_session, rsa_4096_key_id):
        """Test PS512 signing (PSS with SHA-512)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_4096_key_id)
        data = b"test data for PSS signing"

        pss_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA512()),
            salt_length=padding.PSS.AUTO,
        )
        signature = key.sign(data, pss_padding, hashes.SHA512())

        assert len(signature) == 4096 // 8
        public_key = key.public_key()
        verify_padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA512()),
            salt_length=padding.PSS.MAX_LENGTH,
        )
        public_key.verify(signature, data, verify_padding, hashes.SHA512())

    def test_decrypt_oaep_sha1(self, hsm_session, rsa_2048_key_id):
        """Test RSA-OAEP decryption with SHA-1 (SoftHSM2 default)."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        plaintext = b"secret message"
        # Use SHA-1 for OAEP as SoftHSM2 uses SHA-1 as default
        oaep_padding = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        )

        # Encrypt with public key
        ciphertext = public_key.encrypt(plaintext, oaep_padding)
        assert len(ciphertext) == 2048 // 8

        # Decrypt with private key on HSM
        decrypted = key.decrypt(ciphertext, oaep_padding)
        assert decrypted == plaintext

    def test_decrypt_pkcs1v15(self, hsm_session, rsa_2048_key_id):
        """Test RSA PKCS#1 v1.5 decryption."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        plaintext = b"secret message for PKCS1v15"

        # Encrypt with public key
        ciphertext = public_key.encrypt(plaintext, padding.PKCS1v15())
        assert len(ciphertext) == 2048 // 8

        # Decrypt with private key on HSM
        decrypted = key.decrypt(ciphertext, padding.PKCS1v15())
        assert decrypted == plaintext

    def test_private_numbers_raises(self, hsm_session, rsa_2048_key_id):
        """Test that private_numbers() raises HSMUnsupportedError."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_numbers()

    def test_private_bytes_raises(self, hsm_session, rsa_2048_key_id):
        """Test that private_bytes() raises HSMUnsupportedError."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        with pytest.raises(HSMUnsupportedError):
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )

    def test_key_equality(self, hsm_session, rsa_2048_key_id, rsa_3072_key_id):
        """Test key equality."""
        key1 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        key2 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        key3 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_3072_key_id)

        assert key1 == key2
        assert key1 != key3
        assert key1 != "not a key"

    def test_key_hash(self, hsm_session, rsa_2048_key_id):
        """Test key hashing."""
        key1 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        key2 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)

        assert hash(key1) == hash(key2)

    def test_key_copy(self, hsm_session, rsa_2048_key_id):
        """Test key copying."""
        key1 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        key2 = copy.copy(key1)

        assert key1 == key2
        assert key1 is not key2


class TestPKCS11RSAPublicKey:
    """Tests for PKCS11RSAPublicKey."""

    def test_public_numbers(self, hsm_session, rsa_2048_key_id):
        """Test public numbers extraction."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        numbers = public_key.public_numbers()
        assert numbers.e == 65537  # Common public exponent
        assert numbers.n > 0

    def test_public_bytes_pem(self, hsm_session, rsa_2048_key_id):
        """Test public key PEM serialization."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert pem.startswith(b"-----BEGIN PUBLIC KEY-----")
        assert pem.endswith(b"-----END PUBLIC KEY-----\n")

    def test_public_bytes_der(self, hsm_session, rsa_2048_key_id):
        """Test public key DER serialization."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        der = public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert isinstance(der, bytes)
        assert len(der) > 0

    def test_encrypt_decrypt_roundtrip(self, hsm_session, rsa_2048_key_id):
        """Test encryption/decryption roundtrip."""
        key = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id)
        public_key = key.public_key()

        plaintext = b"roundtrip test message"
        # Use SHA-1 for OAEP as SoftHSM2 uses SHA-1 as default
        oaep_padding = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        )

        ciphertext = public_key.encrypt(plaintext, oaep_padding)
        decrypted = key.decrypt(ciphertext, oaep_padding)

        assert decrypted == plaintext

    def test_public_key_equality(self, hsm_session, rsa_2048_key_id, rsa_3072_key_id):
        """Test public key equality."""
        key1 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id).public_key()
        key2 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id).public_key()
        key3 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_3072_key_id).public_key()

        assert key1 == key2
        assert key1 != key3

    def test_public_key_copy(self, hsm_session, rsa_2048_key_id):
        """Test public key copying."""
        key1 = PKCS11RSAPrivateKey(hsm_session, key_id=rsa_2048_key_id).public_key()
        key2 = copy.copy(key1)
        key3 = copy.deepcopy(key1)

        assert key1 == key2
        assert key1 == key3
