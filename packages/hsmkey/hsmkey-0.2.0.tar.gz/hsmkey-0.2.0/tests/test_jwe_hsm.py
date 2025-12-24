"""JWE HSM integration tests.

Tests for encrypting and decrypting JSON Web Encryption using HSM-backed keys.
"""

from __future__ import annotations

import json

import pytest
from jwcrypto.jwe import JWE

from hsmkey.jwk_integration import HSMJWK

# Test plaintext
TEST_PLAINTEXT = b"This is a secret message that should be encrypted."


class TestJWERSAEncryption:
    """Test JWE encryption/decryption with RSA HSM keys."""

    def test_rsa_oaep_encrypt_decrypt(self, hsm_session):
        """Test RSA-OAEP encryption and decryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Encrypt
        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        assert token is not None
        assert len(token.split(".")) == 5

        # Decrypt
        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    @pytest.mark.skip(reason="RSA-OAEP-256 not supported by SoftHSM2")
    def test_rsa_oaep_256_encrypt_decrypt(self, hsm_session):
        """Test RSA-OAEP-256 encryption and decryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Encrypt
        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP-256", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        assert token is not None

        # Decrypt
        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    @pytest.mark.skip(reason="RSA1_5 not allowed by jwcrypto by default for security")
    def test_rsa1_5_encrypt_decrypt(self, hsm_session):
        """Test RSA1_5 encryption and decryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Encrypt
        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA1_5", "enc": "A128CBC-HS256"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        assert token is not None

        # Decrypt
        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    def test_rsa_oaep_with_a128gcm(self, hsm_session):
        """Test RSA-OAEP with A128GCM content encryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A128GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    def test_rsa_oaep_with_a192gcm(self, hsm_session):
        """Test RSA-OAEP with A192GCM content encryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A192GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    def test_rsa_oaep_with_a256cbc_hs512(self, hsm_session):
        """Test RSA-OAEP with A256CBC-HS512 content encryption."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256CBC-HS512"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    def test_larger_key_rsa_3072(self, hsm_session):
        """Test encryption with RSA-3072 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-3072")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT

    def test_larger_key_rsa_4096(self, hsm_session):
        """Test encryption with RSA-4096 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-4096")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == TEST_PLAINTEXT


class TestJWESerializationFormats:
    """Test different JWE serialization formats."""

    def test_compact_serialization(self, hsm_session):
        """Test compact JWE serialization."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        parts = token.split(".")
        assert len(parts) == 5
        # Header, Encrypted Key, IV, Ciphertext, Auth Tag

    def test_json_serialization(self, hsm_session):
        """Test JSON JWE serialization."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize()

        data = json.loads(token)
        assert "protected" in data or "recipients" in data


class TestJWELargePayload:
    """Test JWE with various payload sizes."""

    def test_small_payload(self, hsm_session):
        """Test encryption of small payload."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        payload = b"small"

        jwe = JWE(
            payload,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == payload

    def test_medium_payload(self, hsm_session):
        """Test encryption of medium payload (1KB)."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        payload = b"x" * 1024

        jwe = JWE(
            payload,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == payload

    def test_large_payload(self, hsm_session):
        """Test encryption of large payload (100KB)."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        payload = b"x" * 102400

        jwe = JWE(
            payload,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        jwe2 = JWE()
        jwe2.deserialize(token, key)
        assert jwe2.payload == payload


class TestJWEWithKid:
    """Test JWE with Key ID (kid) header."""

    def test_encrypt_with_kid(self, hsm_session):
        """Test encryption with kid in header."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048", kid="my-encrypt-key")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({
                "alg": "RSA-OAEP",
                "enc": "A256GCM",
                "kid": "my-encrypt-key"
            }),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        assert token is not None

        # Verify the header contains kid
        import base64

        header_b64 = token.split(".")[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        assert header.get("kid") == "my-encrypt-key"


class TestJWEDecryptionErrors:
    """Test JWE decryption error handling."""

    def test_wrong_key_fails(self, hsm_session):
        """Test that decryption with wrong key fails."""
        encrypt_key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        wrong_key = HSMJWK.from_hsm(hsm_session, key_label="rsa-3072")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(encrypt_key)
        token = jwe.serialize(compact=True)

        # Decryption with wrong key should fail
        jwe2 = JWE()
        with pytest.raises(Exception):  # JWE raises various exceptions
            jwe2.deserialize(token, wrong_key)

    def test_tampered_ciphertext_fails(self, hsm_session):
        """Test that tampered ciphertext fails verification."""
        import base64

        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jwe = JWE(
            TEST_PLAINTEXT,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(key)
        token = jwe.serialize(compact=True)

        # Tamper with the ciphertext by flipping bits in actual bytes
        parts = token.split(".")
        ciphertext_b64 = parts[3]
        # Add padding for proper base64 decoding
        padding = 4 - len(ciphertext_b64) % 4
        if padding != 4:
            ciphertext_b64_padded = ciphertext_b64 + "=" * padding
        else:
            ciphertext_b64_padded = ciphertext_b64
        ciphertext = base64.urlsafe_b64decode(ciphertext_b64_padded)
        # Flip bits in the middle of the ciphertext
        tampered = bytearray(ciphertext)
        if len(tampered) > 10:
            tampered[5] ^= 0xFF
            tampered[10] ^= 0xFF
        else:
            tampered[0] ^= 0xFF
        # Re-encode
        parts[3] = base64.urlsafe_b64encode(bytes(tampered)).rstrip(b"=").decode()
        tampered_token = ".".join(parts)

        jwe2 = JWE()
        with pytest.raises(Exception):
            jwe2.deserialize(tampered_token, key)
