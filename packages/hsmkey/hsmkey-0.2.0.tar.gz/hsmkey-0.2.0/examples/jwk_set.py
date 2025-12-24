#!/usr/bin/env python3
"""Example: Managing HSM Keys with HSMJWKSet.

This example demonstrates how to manage multiple HSM keys using HSMJWKSet
for key management scenarios like key rotation and JWKS endpoints.

Prerequisites:
    - SoftHSM2 installed and configured
    - Test keys imported (run: just setup)
    - jwcrypto installed (pip install jwcrypto)

Run with: just example-jwkset
"""

from __future__ import annotations

import json
import os

from jwcrypto.jws import JWS
from jwcrypto.common import json_encode

from hsmkey import HSMJWKSet, hsm_session


def main():
    # Configuration
    module_path = os.environ.get(
        "HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"
    )
    token_label = os.environ.get("HSM_TOKEN", "hsmkey-test")
    pin = os.environ.get("HSM_PIN", "12345678")

    print("=" * 60)
    print("HSMJWKSet Example - Key Management")
    print("=" * 60)

    with hsm_session(module_path, token_label, pin) as session:
        # Example 1: Create JWKSet with Multiple Keys
        print("\n1. Create HSMJWKSet with Multiple Keys")
        print("-" * 40)

        jwk_set = HSMJWKSet(session)

        # Add keys with specific key IDs
        rsa_key = jwk_set.add_key(key_label="rsa-2048", kid="rsa-signing-key")
        ec_key = jwk_set.add_key(key_label="ec-p256", kid="ec-signing-key")
        ed_key = jwk_set.add_key(key_label="ed25519", kid="ed-signing-key")

        print(f"Keys in set: {len(jwk_set)}")
        for key in jwk_set:
            public = key.export_public(as_dict=True)
            print(f"  - {public.get('kid', 'no-kid')}: {public['kty']}")

        # Example 2: Retrieve Keys by ID
        print("\n2. Retrieve Keys by ID")
        print("-" * 40)

        key1 = jwk_set.get_key("rsa-signing-key")
        key2 = jwk_set.get_key("ec-signing-key")
        key3 = jwk_set.get_key("nonexistent-key")

        print(f"rsa-signing-key found: {key1 is not None}")
        print(f"ec-signing-key found: {key2 is not None}")
        print(f"nonexistent-key found: {key3 is not None}")

        # Example 3: Export Public JWKS
        print("\n3. Export Public JWKS (for /.well-known/jwks.json)")
        print("-" * 40)

        public_keys = []
        for key in jwk_set:
            public_jwk = key.export_public(as_dict=True)
            public_keys.append(public_jwk)

        jwks = {"keys": public_keys}
        print(json.dumps(jwks, indent=2)[:500] + "...")

        # Example 4: Sign with Different Keys from Set
        print("\n4. Sign with Different Keys from Set")
        print("-" * 40)

        payload = b'{"data": "important message"}'

        # Sign with RSA key
        rsa_key = jwk_set.get_key("rsa-signing-key")
        jws_rsa = JWS(payload)
        jws_rsa.add_signature(
            rsa_key,
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "rsa-signing-key"}),
        )
        token_rsa = jws_rsa.serialize(compact=True)
        print(f"RSA Token: {token_rsa[:60]}...")

        # Sign with EC key
        ec_key = jwk_set.get_key("ec-signing-key")
        jws_ec = JWS(payload)
        jws_ec.add_signature(
            ec_key,
            alg="ES256",
            protected=json_encode({"alg": "ES256", "kid": "ec-signing-key"}),
        )
        token_ec = jws_ec.serialize(compact=True)
        print(f"EC Token: {token_ec[:60]}...")

        # Example 5: Key Rotation Scenario
        print("\n5. Key Rotation Scenario")
        print("-" * 40)

        # Create a new set for rotation
        rotation_set = HSMJWKSet(session)

        # Old key (still valid for verification)
        old_key = rotation_set.add_key(key_label="rsa-2048", kid="key-v1")

        # New key (for new signatures)
        new_key = rotation_set.add_key(key_label="rsa-3072", kid="key-v2")

        print(f"Keys for rotation: {len(rotation_set)}")

        # Sign new tokens with new key
        new_token = JWS(b'{"user": "new-user"}')
        new_token.add_signature(
            new_key,
            alg="RS384",
            protected=json_encode({"alg": "RS384", "kid": "key-v2"}),
        )
        print(f"New signature (key-v2): {new_token.serialize(compact=True)[:60]}...")

        # Old tokens can still be verified with old key
        old_token = JWS(b'{"user": "old-user"}')
        old_token.add_signature(
            old_key,
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "key-v1"}),
        )
        print(f"Old signature (key-v1): {old_token.serialize(compact=True)[:60]}...")

        # Verify: Both keys are in the set for verification
        for kid in ["key-v1", "key-v2"]:
            key = rotation_set.get_key(kid)
            print(f"  {kid} available: {key is not None}")

        # Example 6: Key Usage Tracking
        print("\n6. Keys with Different Purposes")
        print("-" * 40)

        purpose_set = HSMJWKSet(session)

        # Add keys with specific purposes (using different HSM keys as example)
        sign_key = purpose_set.add_key(
            key_label="ec-p256",
            kid="signing-key",
            use="sig",
            key_ops=["sign", "verify"],
        )
        encrypt_key = purpose_set.add_key(
            key_label="rsa-2048",
            kid="encryption-key",
            use="enc",
            key_ops=["encrypt", "decrypt", "wrapKey", "unwrapKey"],
        )

        print("Keys by purpose:")
        for key in purpose_set:
            public = key.export_public(as_dict=True)
            kid = public.get("kid", "no-kid")
            use = public.get("use", "not-specified")
            ops = public.get("key_ops", [])
            print(f"  {kid}: use={use}, ops={ops}")

        # Example 7: Iterate and Filter Keys
        print("\n7. Filter Keys by Type")
        print("-" * 40)

        all_keys_set = HSMJWKSet(session)
        all_keys_set.add_key(key_label="rsa-2048", kid="rsa-1")
        all_keys_set.add_key(key_label="rsa-3072", kid="rsa-2")
        all_keys_set.add_key(key_label="ec-p256", kid="ec-1")
        all_keys_set.add_key(key_label="ed25519", kid="ed-1")

        # Filter by key type
        rsa_keys = [
            k for k in all_keys_set if k.export_public(as_dict=True)["kty"] == "RSA"
        ]
        ec_keys = [
            k for k in all_keys_set if k.export_public(as_dict=True)["kty"] == "EC"
        ]
        okp_keys = [
            k for k in all_keys_set if k.export_public(as_dict=True)["kty"] == "OKP"
        ]

        print(f"RSA keys: {len(rsa_keys)}")
        print(f"EC keys: {len(ec_keys)}")
        print(f"OKP keys: {len(okp_keys)}")

    print("\n" + "=" * 60)
    print("HSMJWKSet examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
