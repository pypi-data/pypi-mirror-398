"""JWS HSM integration tests.

Tests for signing and verifying JSON Web Signatures using HSM-backed keys.
"""

from __future__ import annotations

import json

import pytest
from jwcrypto.jws import JWS
from jwcrypto.common import json_encode

from hsmkey.jwk_integration import HSMJWK

# Test payload
TEST_PAYLOAD = b'{"sub": "user@example.com", "iss": "hsmkey-test"}'


class TestJWSRSASigning:
    """Test JWS signing with RSA HSM keys."""

    def test_rs256_sign(self, hsm_session):
        """Test RS256 signing with HSM RSA-2048 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))

        token = jws.serialize(compact=True)
        assert token is not None
        assert len(token.split(".")) == 3

    def test_rs384_sign(self, hsm_session):
        """Test RS384 signing with HSM RSA-3072 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-3072")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS384", protected=json_encode({"alg": "RS384"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_rs512_sign(self, hsm_session):
        """Test RS512 signing with HSM RSA-4096 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-4096")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS512", protected=json_encode({"alg": "RS512"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_ps256_sign(self, hsm_session):
        """Test PS256 (RSA-PSS) signing with HSM RSA-2048 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="PS256", protected=json_encode({"alg": "PS256"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_ps384_sign(self, hsm_session):
        """Test PS384 (RSA-PSS) signing with HSM RSA-3072 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-3072")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="PS384", protected=json_encode({"alg": "PS384"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_ps512_sign(self, hsm_session):
        """Test PS512 (RSA-PSS) signing with HSM RSA-4096 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-4096")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="PS512", protected=json_encode({"alg": "PS512"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_rs256_sign_verify_roundtrip(self, hsm_session):
        """Test RS256 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD

    def test_ps256_sign_verify_roundtrip(self, hsm_session):
        """Test PS256 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="PS256", protected=json_encode({"alg": "PS256"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD


class TestJWSECDSASigning:
    """Test JWS signing with ECDSA HSM keys."""

    def test_es256_sign(self, hsm_session):
        """Test ES256 signing with HSM P-256 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES256", protected=json_encode({"alg": "ES256"}))

        token = jws.serialize(compact=True)
        assert token is not None
        assert len(token.split(".")) == 3

    def test_es384_sign(self, hsm_session):
        """Test ES384 signing with HSM P-384 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p384")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES384", protected=json_encode({"alg": "ES384"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_es512_sign(self, hsm_session):
        """Test ES512 signing with HSM P-521 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p521")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES512", protected=json_encode({"alg": "ES512"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_es256_sign_verify_roundtrip(self, hsm_session):
        """Test ES256 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES256", protected=json_encode({"alg": "ES256"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD

    def test_es384_sign_verify_roundtrip(self, hsm_session):
        """Test ES384 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p384")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES384", protected=json_encode({"alg": "ES384"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD

    def test_es512_sign_verify_roundtrip(self, hsm_session):
        """Test ES512 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p521")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="ES512", protected=json_encode({"alg": "ES512"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD


@pytest.mark.requires_eddsa
class TestJWSEdDSASigning:
    """Test JWS signing with EdDSA HSM keys."""

    def test_eddsa_ed25519_sign(self, hsm_session):
        """Test EdDSA signing with HSM Ed25519 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="EdDSA", protected=json_encode({"alg": "EdDSA"}))

        token = jws.serialize(compact=True)
        assert token is not None
        assert len(token.split(".")) == 3

    def test_eddsa_ed448_sign(self, hsm_session):
        """Test EdDSA signing with HSM Ed448 key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed448")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="EdDSA", protected=json_encode({"alg": "EdDSA"}))

        token = jws.serialize(compact=True)
        assert token is not None

    def test_eddsa_ed25519_sign_verify_roundtrip(self, hsm_session):
        """Test EdDSA Ed25519 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="EdDSA", protected=json_encode({"alg": "EdDSA"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD

    def test_eddsa_ed448_sign_verify_roundtrip(self, hsm_session):
        """Test EdDSA Ed448 sign and verify roundtrip."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed448")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="EdDSA", protected=json_encode({"alg": "EdDSA"}))
        token = jws.serialize(compact=True)

        # Verify
        jws2 = JWS()
        jws2.deserialize(token, key)
        assert jws2.payload == TEST_PAYLOAD


class TestJWSSerializationFormats:
    """Test different JWS serialization formats."""

    def test_compact_serialization(self, hsm_session):
        """Test compact JWS serialization."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))

        token = jws.serialize(compact=True)
        parts = token.split(".")
        assert len(parts) == 3
        # Header, payload, signature

    def test_json_serialization(self, hsm_session):
        """Test JSON JWS serialization."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))

        token = jws.serialize()
        data = json.loads(token)
        assert "payload" in data
        # Flattened format uses "signature", general format uses "signatures"
        assert "signature" in data or "signatures" in data

    def test_flattened_json_serialization(self, hsm_session):
        """Test flattened JSON JWS serialization."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))

        token = jws.serialize()
        # With single signature, should have signatures array
        data = json.loads(token)
        assert "signatures" in data or "signature" in data


class TestJWSWithKid:
    """Test JWS with Key ID (kid) header."""

    def test_sign_with_kid(self, hsm_session):
        """Test signing with kid in header."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048", kid="my-rsa-key")

        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(
            key,
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "my-rsa-key"}),
        )

        token = jws.serialize(compact=True)
        assert token is not None

        # Verify the header contains kid
        import base64

        header_b64 = token.split(".")[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        assert header.get("kid") == "my-rsa-key"


class TestJWSPublicKeyExtraction:
    """Test extracting public keys from HSM JWKs for verification."""

    def test_export_public_key(self, hsm_session):
        """Test exporting public key from HSMJWK."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Export public key
        public_jwk = key.export_public(as_dict=True)

        assert public_jwk["kty"] == "RSA"
        assert "n" in public_jwk
        assert "e" in public_jwk
        assert "d" not in public_jwk  # Private key not exported

    def test_verify_with_exported_public_key(self, hsm_session):
        """Test verifying with exported public key."""
        from jwcrypto.jwk import JWK

        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Sign
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))
        token = jws.serialize(compact=True)

        # Create public-only JWK
        public_jwk = JWK(**key.export_public(as_dict=True))

        # Verify with public key
        jws2 = JWS()
        jws2.deserialize(token, public_jwk)
        assert jws2.payload == TEST_PAYLOAD
