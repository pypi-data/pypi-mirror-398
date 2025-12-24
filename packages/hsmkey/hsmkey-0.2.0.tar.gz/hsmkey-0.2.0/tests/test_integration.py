"""Integration tests for hsmkey with jwcrypto.

Tests for interoperability between HSM keys and software keys,
concurrent operations, and error handling.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from jwcrypto.jwt import JWT
from jwcrypto.common import json_encode

from hsmkey import SessionPool
from hsmkey.exceptions import HSMKeyNotFoundError, HSMSessionError
from hsmkey.jwk_integration import HSMJWK, HSMJWKSet, hsm_session, jwk_from_hsm

# Test payload
TEST_PAYLOAD = b'{"sub": "user@example.com"}'


class TestInteroperability:
    """Test interoperability between HSM and software keys."""

    def test_sign_hsm_verify_software(self, hsm_session):
        """Test signing with HSM, verifying with software key."""
        # Get HSM key
        hsm_key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Sign with HSM
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(hsm_key, alg="RS256", protected=json_encode({"alg": "RS256"}))
        token = jws.serialize(compact=True)

        # Create software-only public key from HSM key's public parameters
        public_params = hsm_key.export_public(as_dict=True)
        software_key = JWK(**public_params)

        # Verify with software key
        jws2 = JWS()
        jws2.deserialize(token, software_key)
        assert jws2.payload == TEST_PAYLOAD

    def test_sign_software_verify_hsm(self, hsm_session):
        """Test signing with software key, verifying with HSM public key."""
        # Create software key
        software_key = JWK.generate(kty="RSA", size=2048)

        # Sign with software key
        jws = JWS(TEST_PAYLOAD)
        jws.add_signature(
            software_key, alg="RS256", protected=json_encode({"alg": "RS256"})
        )
        token = jws.serialize(compact=True)

        # Create public-only JWK for verification
        public_params = software_key.export_public(as_dict=True)
        public_key = JWK(**public_params)

        # Verify with public key (software)
        jws2 = JWS()
        jws2.deserialize(token, public_key)
        assert jws2.payload == TEST_PAYLOAD

    def test_encrypt_software_decrypt_hsm(self, hsm_session):
        """Test encrypting with software key, decrypting with HSM key."""
        # Get HSM key and its public parameters
        hsm_key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        public_params = hsm_key.export_public(as_dict=True)
        public_key = JWK(**public_params)

        # Encrypt with public key (software)
        jwe = JWE(
            TEST_PAYLOAD,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(public_key)
        token = jwe.serialize(compact=True)

        # Decrypt with HSM key
        jwe2 = JWE()
        jwe2.deserialize(token, hsm_key)
        assert jwe2.payload == TEST_PAYLOAD

    def test_cross_algorithm_verification(self, hsm_session):
        """Test that different algorithms produce valid signatures."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        # Test RS256
        jws_rs256 = JWS(TEST_PAYLOAD)
        jws_rs256.add_signature(
            key, alg="RS256", protected=json_encode({"alg": "RS256"})
        )
        token_rs256 = jws_rs256.serialize(compact=True)

        # Test PS256
        jws_ps256 = JWS(TEST_PAYLOAD)
        jws_ps256.add_signature(
            key, alg="PS256", protected=json_encode({"alg": "PS256"})
        )
        token_ps256 = jws_ps256.serialize(compact=True)

        # Verify both
        jws_verify_rs256 = JWS()
        jws_verify_rs256.deserialize(token_rs256, key)
        assert jws_verify_rs256.payload == TEST_PAYLOAD

        jws_verify_ps256 = JWS()
        jws_verify_ps256.deserialize(token_ps256, key)
        assert jws_verify_ps256.payload == TEST_PAYLOAD


class TestHSMJWKSet:
    """Test HSMJWKSet functionality."""

    def test_add_and_get_key(self, hsm_session):
        """Test adding and retrieving keys from HSMJWKSet."""
        jwk_set = HSMJWKSet(hsm_session)

        # Add keys
        rsa_key = jwk_set.add_key(key_label="rsa-2048", kid="rsa-key-1")
        ec_key = jwk_set.add_key(key_label="ec-p256", kid="ec-key-1")

        # Retrieve keys
        assert jwk_set.get_key("rsa-key-1") is rsa_key
        assert jwk_set.get_key("ec-key-1") is ec_key
        assert jwk_set.get_key("nonexistent") is None

    def test_jwkset_iteration(self, hsm_session):
        """Test iterating over HSMJWKSet."""
        jwk_set = HSMJWKSet(hsm_session)
        jwk_set.add_key(key_label="rsa-2048", kid="key1")
        jwk_set.add_key(key_label="ec-p256", kid="key2")

        keys = list(jwk_set)
        assert len(keys) == 2

    def test_jwkset_length(self, hsm_session):
        """Test HSMJWKSet length."""
        jwk_set = HSMJWKSet(hsm_session)
        assert len(jwk_set) == 0

        jwk_set.add_key(key_label="rsa-2048", kid="key1")
        assert len(jwk_set) == 1

        jwk_set.add_key(key_label="ec-p256", kid="key2")
        assert len(jwk_set) == 2

    def test_duplicate_kid_raises(self, hsm_session):
        """Test that duplicate kid raises error."""
        jwk_set = HSMJWKSet(hsm_session)
        jwk_set.add_key(key_label="rsa-2048", kid="same-kid")

        with pytest.raises(ValueError, match="already exists"):
            jwk_set.add_key(key_label="ec-p256", kid="same-kid")


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_jwk_from_hsm_function(self, hsm_session):
        """Test jwk_from_hsm convenience function."""
        key = jwk_from_hsm(hsm_session, key_label="rsa-2048")
        assert isinstance(key, HSMJWK)
        assert key.has_private()

    def test_jwk_from_hsm_with_options(self, hsm_session):
        """Test jwk_from_hsm with optional parameters."""
        key = jwk_from_hsm(
            hsm_session,
            key_label="rsa-2048",
            kid="my-key-id",
            use="sig",
            key_ops=["sign", "verify"],
        )
        assert isinstance(key, HSMJWK)


class TestHSMSessionContextManager:
    """Test hsm_session context manager."""

    def test_hsm_session_context_manager(
        self, hsm_module, hsm_token_label, hsm_pin
    ):
        """Test hsm_session context manager."""
        with hsm_session(hsm_module, hsm_token_label, hsm_pin) as session:
            key = jwk_from_hsm(session, key_label="rsa-2048")
            assert isinstance(key, HSMJWK)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_key_not_found(self, hsm_session):
        """Test error when key not found."""
        with pytest.raises(HSMKeyNotFoundError):
            HSMJWK.from_hsm(hsm_session, key_label="nonexistent-key")

    def test_export_private_raises(self, hsm_session):
        """Test that exporting private key raises error."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")

        with pytest.raises(HSMSessionError, match="Cannot export private key"):
            key.export_private()

    def test_key_id_or_label_required(self, hsm_session):
        """Test that key_id or key_label is required."""
        with pytest.raises(ValueError, match="Either key_id or key_label"):
            HSMJWK.from_hsm(hsm_session)


class TestConcurrentOperations:
    """Test concurrent HSM operations."""

    @pytest.mark.skip(reason="PKCS#11 sessions cannot be used concurrently with same login")
    def test_concurrent_signing(self, session_pool):
        """Test concurrent signing operations."""
        results = []
        errors = []

        def sign_message(msg_id: int) -> str:
            try:
                with session_pool.session() as session:
                    key = HSMJWK.from_hsm(session, key_label="rsa-2048")
                    payload = f'{{"id": {msg_id}}}'.encode()

                    jws = JWS(payload)
                    jws.add_signature(
                        key, alg="RS256", protected=json_encode({"alg": "RS256"})
                    )
                    return jws.serialize(compact=True)
            except Exception as e:
                errors.append(str(e))
                return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sign_message, i) for i in range(10)]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10

    @pytest.mark.skip(reason="PKCS#11 sessions cannot be used concurrently with same login")
    def test_concurrent_verification(self, session_pool):
        """Test concurrent verification operations."""
        # First create some tokens
        tokens = []
        with session_pool.session() as session:
            key = HSMJWK.from_hsm(session, key_label="rsa-2048")
            for i in range(10):
                payload = f'{{"id": {i}}}'.encode()
                jws = JWS(payload)
                jws.add_signature(
                    key, alg="RS256", protected=json_encode({"alg": "RS256"})
                )
                tokens.append(jws.serialize(compact=True))

        # Verify concurrently
        results = []
        errors = []

        def verify_token(token: str) -> bytes:
            try:
                with session_pool.session() as session:
                    key = HSMJWK.from_hsm(session, key_label="rsa-2048")
                    jws = JWS()
                    jws.deserialize(token, key)
                    return jws.payload
            except Exception as e:
                errors.append(str(e))
                return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(verify_token, t) for t in tokens]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10


class TestKeyTypes:
    """Test all supported key types work correctly."""

    def test_all_rsa_key_sizes(self, hsm_session):
        """Test all RSA key sizes."""
        for label in ["rsa-2048", "rsa-3072", "rsa-4096"]:
            key = HSMJWK.from_hsm(hsm_session, key_label=label)
            public = key.export_public(as_dict=True)
            assert public["kty"] == "RSA"

    def test_all_ec_curves(self, hsm_session):
        """Test all EC curves."""
        curves = {
            "ec-p256": "P-256",
            "ec-p384": "P-384",
            "ec-p521": "P-521",
        }
        for label, expected_crv in curves.items():
            key = HSMJWK.from_hsm(hsm_session, key_label=label)
            public = key.export_public(as_dict=True)
            assert public["kty"] == "EC"
            assert public["crv"] == expected_crv

    @pytest.mark.requires_eddsa
    def test_all_eddsa_curves(self, hsm_session):
        """Test all EdDSA curves."""
        curves = {
            "ed25519": "Ed25519",
            "ed448": "Ed448",
        }
        for label, expected_crv in curves.items():
            key = HSMJWK.from_hsm(hsm_session, key_label=label)
            public = key.export_public(as_dict=True)
            assert public["kty"] == "OKP"
            assert public["crv"] == expected_crv


class TestKeyRotation:
    """Test key rotation scenarios."""

    def test_sign_with_multiple_keys(self, hsm_session):
        """Test signing with multiple different keys."""
        keys = {
            "old": HSMJWK.from_hsm(hsm_session, key_label="rsa-2048", kid="old-key"),
            "new": HSMJWK.from_hsm(hsm_session, key_label="rsa-3072", kid="new-key"),
        }

        # Sign with old key
        jws_old = JWS(TEST_PAYLOAD)
        jws_old.add_signature(
            keys["old"],
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "old-key"}),
        )
        token_old = jws_old.serialize(compact=True)

        # Sign with new key
        jws_new = JWS(TEST_PAYLOAD)
        jws_new.add_signature(
            keys["new"],
            alg="RS384",
            protected=json_encode({"alg": "RS384", "kid": "new-key"}),
        )
        token_new = jws_new.serialize(compact=True)

        # Verify both
        jws_verify_old = JWS()
        jws_verify_old.deserialize(token_old, keys["old"])
        assert jws_verify_old.payload == TEST_PAYLOAD

        jws_verify_new = JWS()
        jws_verify_new.deserialize(token_new, keys["new"])
        assert jws_verify_new.payload == TEST_PAYLOAD


class TestPublicKeyExport:
    """Test public key export formats."""

    def test_export_rsa_public_key(self, hsm_session):
        """Test exporting RSA public key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        public = key.export_public(as_dict=True)

        assert "kty" in public
        assert "n" in public
        assert "e" in public
        assert "d" not in public
        assert "p" not in public
        assert "q" not in public

    def test_export_ec_public_key(self, hsm_session):
        """Test exporting EC public key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ec-p256")
        public = key.export_public(as_dict=True)

        assert public["kty"] == "EC"
        assert "crv" in public
        assert "x" in public
        assert "y" in public
        assert "d" not in public

    @pytest.mark.requires_eddsa
    def test_export_okp_public_key(self, hsm_session):
        """Test exporting OKP (Ed25519) public key."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")
        public = key.export_public(as_dict=True)

        assert public["kty"] == "OKP"
        assert public["crv"] == "Ed25519"
        assert "x" in public
        assert "d" not in public
