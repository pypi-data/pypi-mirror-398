#!/usr/bin/env python3
"""Example: Session Management with SessionPool.

This example demonstrates how to use the SessionPool for HSM session
management. Note: PKCS#11 has limitations on concurrent sessions with
the same login, so operations should typically be serialized.

Prerequisites:
    - SoftHSM2 installed and configured
    - Test keys imported (run: just setup)
    - jwcrypto installed (pip install jwcrypto)

Run with: just example-pool
"""

from __future__ import annotations

import os
import time

from jwcrypto.jws import JWS
from jwcrypto.common import json_encode

from hsmkey import SessionPool
from hsmkey.jwk_integration import HSMJWK


def main():
    # Configuration
    module_path = os.environ.get(
        "HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"
    )
    token_label = os.environ.get("HSM_TOKEN", "hsmkey-test")
    pin = os.environ.get("HSM_PIN", "12345678")

    print("=" * 60)
    print("Session Pool Example - HSM Session Management")
    print("=" * 60)

    # Create a session pool
    pool = SessionPool(
        module_path=module_path,
        token_label=token_label,
        user_pin=pin,
    )

    print("\nPool created")

    # Example 1: Basic Session Usage
    print("\n1. Basic Session Usage")
    print("-" * 40)

    with pool.session() as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")
        payload = b'{"message": "Hello from HSM!"}'

        jws = JWS(payload)
        jws.add_signature(
            key, alg="RS256", protected=json_encode({"alg": "RS256"})
        )
        token = jws.serialize(compact=True)
        print(f"Signed token: {token[:60]}...")

    # Session is automatically closed here
    print("Session closed automatically")

    # Example 2: Multiple Sequential Operations
    print("\n2. Multiple Sequential Operations")
    print("-" * 40)

    tokens = []
    start = time.time()

    for i in range(10):
        with pool.session() as session:
            key = HSMJWK.from_hsm(session, key_label="rsa-2048")
            payload = f'{{"id": {i}}}'.encode()

            jws = JWS(payload)
            jws.add_signature(
                key, alg="RS256", protected=json_encode({"alg": "RS256"})
            )
            tokens.append(jws.serialize(compact=True))

    elapsed = time.time() - start
    print(f"Signed {len(tokens)} tokens in {elapsed:.3f}s")
    print(f"Average: {elapsed / len(tokens) * 1000:.1f}ms per signature")

    # Example 3: Different Key Types
    print("\n3. Using Different Key Types")
    print("-" * 40)

    key_configs = [
        ("rsa-2048", "RS256"),
        ("rsa-3072", "RS384"),
        ("ec-p256", "ES256"),
        ("ec-p384", "ES384"),
        ("ed25519", "EdDSA"),
    ]

    for key_label, alg in key_configs:
        with pool.session() as session:
            key = HSMJWK.from_hsm(session, key_label=key_label)
            payload = b'{"test": "message"}'

            jws = JWS(payload)
            jws.add_signature(
                key, alg=alg, protected=json_encode({"alg": alg})
            )
            token = jws.serialize(compact=True)
            print(f"  {key_label} ({alg}): {token[:40]}...")

    # Example 4: Sign and Verify in Same Session
    print("\n4. Sign and Verify in Same Session")
    print("-" * 40)

    with pool.session() as session:
        key = HSMJWK.from_hsm(session, key_label="ec-p256", kid="my-key")
        payload = b'{"user": "admin", "action": "login"}'

        # Sign
        jws = JWS(payload)
        jws.add_signature(
            key, alg="ES256", protected=json_encode({"alg": "ES256", "kid": "my-key"})
        )
        token = jws.serialize(compact=True)
        print(f"Signed: {token[:60]}...")

        # Verify in same session
        jws_verify = JWS()
        jws_verify.deserialize(token, key)
        print(f"Verified payload: {jws_verify.payload.decode()}")

    # Example 5: Batch Signing with Single Session
    print("\n5. Batch Signing with Single Session (More Efficient)")
    print("-" * 40)

    batch_tokens = []
    start = time.time()

    with pool.session() as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        for i in range(10):
            payload = f'{{"batch_id": {i}}}'.encode()
            jws = JWS(payload)
            jws.add_signature(
                key, alg="RS256", protected=json_encode({"alg": "RS256"})
            )
            batch_tokens.append(jws.serialize(compact=True))

    elapsed = time.time() - start
    print(f"Batch signed {len(batch_tokens)} tokens in {elapsed:.3f}s")
    print(f"Average: {elapsed / len(batch_tokens) * 1000:.1f}ms per signature")

    # Example 6: Key Caching Pattern
    print("\n6. Key Caching Pattern")
    print("-" * 40)

    with pool.session() as session:
        # Load multiple keys once
        keys = {
            "rsa": HSMJWK.from_hsm(session, key_label="rsa-2048", kid="rsa"),
            "ec": HSMJWK.from_hsm(session, key_label="ec-p256", kid="ec"),
            "ed": HSMJWK.from_hsm(session, key_label="ed25519", kid="ed"),
        }

        # Use cached keys for multiple operations
        for name, key in keys.items():
            payload = f'{{"key_type": "{name}"}}'.encode()
            alg = {"rsa": "RS256", "ec": "ES256", "ed": "EdDSA"}[name]

            jws = JWS(payload)
            jws.add_signature(
                key, alg=alg, protected=json_encode({"alg": alg, "kid": name})
            )
            print(f"  {name}: signed with {alg}")

    # Example 7: Error Handling
    print("\n7. Error Handling")
    print("-" * 40)

    try:
        with pool.session() as session:
            # Try to load a non-existent key
            HSMJWK.from_hsm(session, key_label="nonexistent-key")
    except Exception as e:
        print(f"Caught expected error: {type(e).__name__}")
        print(f"Message: {e}")

    print("\n" + "=" * 60)
    print("Session Pool examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
