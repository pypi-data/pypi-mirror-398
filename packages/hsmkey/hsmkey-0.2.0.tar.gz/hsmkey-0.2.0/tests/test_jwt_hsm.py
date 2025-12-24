"""JWT HSM integration tests.

Tests for signing, verifying, encrypting, and decrypting JSON Web Tokens
using HSM-backed keys.
"""

from __future__ import annotations

import json
import time

import pytest
from jwcrypto.jwt import JWT
from jwcrypto.common import json_encode

from hsmkey.jwk_integration import HSMJWK


class TestJWTSigning:
    """Test JWT signing with HSM keys."""

    def test_jwt_rs256_sign(self, hsm_session):
        """Test JWT signing with RS256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
            "aud": "test-audience",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)

        serialized = token.serialize()
        assert serialized is not None
        assert len(serialized.split(".")) == 3

    def test_jwt_ps256_sign(self, hsm_session):
        """Test JWT signing with PS256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
        }

        token = JWT(header={"alg": "PS256"}, claims=claims)
        token.make_signed_token(key)

        serialized = token.serialize()
        assert serialized is not None

    def test_jwt_es256_sign(self, hsm_session):
        """Test JWT signing with ES256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
        }

        token = JWT(header={"alg": "ES256"}, claims=claims)
        token.make_signed_token(key)

        serialized = token.serialize()
        assert serialized is not None

    @pytest.mark.requires_eddsa
    def test_jwt_eddsa_sign(self, hsm_session):
        """Test JWT signing with EdDSA (Ed25519)."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
        }

        token = JWT(header={"alg": "EdDSA"}, claims=claims)
        token.make_signed_token(key)

        serialized = token.serialize()
        assert serialized is not None


class TestJWTVerification:
    """Test JWT verification with HSM keys."""

    def test_jwt_rs256_verify(self, hsm_session):
        """Test JWT verification with RS256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
        }

        # Sign
        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        # Verify
        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["sub"] == "user@example.com"
        assert verified_claims["iss"] == "hsmkey-test"

    def test_jwt_es256_verify(self, hsm_session):
        """Test JWT verification with ES256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")

        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "ES256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["sub"] == "user@example.com"

    @pytest.mark.requires_eddsa
    def test_jwt_eddsa_verify(self, hsm_session):
        """Test JWT verification with EdDSA."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")

        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "EdDSA"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["sub"] == "user@example.com"


class TestJWTEncryption:
    """Test JWT encryption with HSM keys."""

    def test_jwt_encrypt_rsa_oaep(self, hsm_session):
        """Test JWT encryption with RSA-OAEP."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "secret_data": "confidential",
        }

        token = JWT(header={"alg": "RSA-OAEP", "enc": "A256GCM"}, claims=claims)
        token.make_encrypted_token(key)

        serialized = token.serialize()
        assert serialized is not None
        assert len(serialized.split(".")) == 5

    def test_jwt_encrypt_rsa_oaep_256(self, hsm_session):
        """Test JWT encryption with RSA-OAEP-256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RSA-OAEP-256", "enc": "A256GCM"}, claims=claims)
        token.make_encrypted_token(key)

        serialized = token.serialize()
        assert serialized is not None


class TestJWTDecryption:
    """Test JWT decryption with HSM keys."""

    def test_jwt_decrypt_rsa_oaep(self, hsm_session):
        """Test JWT decryption with RSA-OAEP."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "secret_data": "confidential",
        }

        # Encrypt
        token = JWT(header={"alg": "RSA-OAEP", "enc": "A256GCM"}, claims=claims)
        token.make_encrypted_token(key)
        serialized = token.serialize()

        # Decrypt
        token2 = JWT(jwt=serialized, key=key, expected_type="JWE")
        decrypted_claims = json.loads(token2.claims)
        assert decrypted_claims["sub"] == "user@example.com"
        assert decrypted_claims["secret_data"] == "confidential"

    @pytest.mark.skip(reason="RSA-OAEP-256 not supported by SoftHSM2")
    def test_jwt_decrypt_rsa_oaep_256(self, hsm_session):
        """Test JWT decryption with RSA-OAEP-256."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RSA-OAEP-256", "enc": "A256GCM"}, claims=claims)
        token.make_encrypted_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        decrypted_claims = json.loads(token2.claims)
        assert decrypted_claims["sub"] == "user@example.com"


class TestJWTClaimsValidation:
    """Test JWT claims validation."""

    def test_valid_expiration(self, hsm_session):
        """Test JWT with valid expiration claim."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "exp": int(time.time()) + 3600,  # 1 hour from now
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        # Should not raise
        token2 = JWT(jwt=serialized, key=key, check_claims={"exp": None})
        verified_claims = json.loads(token2.claims)
        assert verified_claims["sub"] == "user@example.com"

    def test_issuer_claim(self, hsm_session):
        """Test JWT with issuer claim."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "https://issuer.example.com",
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["iss"] == "https://issuer.example.com"

    def test_audience_claim(self, hsm_session):
        """Test JWT with audience claim."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "aud": "https://api.example.com",
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["aud"] == "https://api.example.com"

    def test_custom_claims(self, hsm_session):
        """Test JWT with custom claims."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "role": "admin",
            "permissions": ["read", "write", "delete"],
            "metadata": {"department": "engineering"},
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        verified_claims = json.loads(token2.claims)
        assert verified_claims["role"] == "admin"
        assert verified_claims["permissions"] == ["read", "write", "delete"]
        assert verified_claims["metadata"]["department"] == "engineering"


class TestJWTNestedTokens:
    """Test nested JWT (signed then encrypted)."""

    def test_nested_jwt_sign_then_encrypt(self, hsm_session):
        """Test creating a nested JWT (signed then encrypted)."""
        sign_key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")
        encrypt_key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "hsmkey-test",
        }

        # First sign
        inner_token = JWT(header={"alg": "ES256"}, claims=claims)
        inner_token.make_signed_token(sign_key)
        signed_jwt = inner_token.serialize()

        # Then encrypt
        outer_token = JWT(
            header={"alg": "RSA-OAEP", "enc": "A256GCM", "cty": "JWT"},
            claims=signed_jwt,
        )
        outer_token.make_encrypted_token(encrypt_key)
        nested_jwt = outer_token.serialize()

        assert nested_jwt is not None
        assert len(nested_jwt.split(".")) == 5

        # Decrypt
        decrypted_outer = JWT(jwt=nested_jwt, key=encrypt_key, expected_type="JWE")
        inner_jwt = decrypted_outer.claims

        # Verify inner token
        verified_inner = JWT(jwt=inner_jwt, key=sign_key)
        final_claims = json.loads(verified_inner.claims)
        assert final_claims["sub"] == "user@example.com"


class TestJWTWithKid:
    """Test JWT with Key ID (kid) header."""

    def test_jwt_with_kid_header(self, hsm_session):
        """Test JWT with kid in header."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048", kid="my-signing-key")

        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RS256", "kid": "my-signing-key"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        # Verify kid is in header
        import base64

        header_b64 = serialized.split(".")[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        assert header.get("kid") == "my-signing-key"


class TestJWTDifferentKeySizes:
    """Test JWT with different RSA key sizes."""

    def test_jwt_rsa_2048(self, hsm_session):
        """Test JWT with RSA-2048."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        assert json.loads(token2.claims)["sub"] == "user@example.com"

    def test_jwt_rsa_3072(self, hsm_session):
        """Test JWT with RSA-3072."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-3072")
        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RS384"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        assert json.loads(token2.claims)["sub"] == "user@example.com"

    def test_jwt_rsa_4096(self, hsm_session):
        """Test JWT with RSA-4096."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-4096")
        claims = {"sub": "user@example.com"}

        token = JWT(header={"alg": "RS512"}, claims=claims)
        token.make_signed_token(key)
        serialized = token.serialize()

        token2 = JWT(jwt=serialized, key=key)
        assert json.loads(token2.claims)["sub"] == "user@example.com"
