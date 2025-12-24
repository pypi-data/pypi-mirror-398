#!/usr/bin/env python3
"""Example: JWS Signing and Verification with HSM Keys.

This example demonstrates how to sign and verify JSON Web Signatures (JWS)
using HSM-backed keys with the hsmkey library.

Prerequisites:
    - SoftHSM2 installed and configured
    - Test keys imported (run: just setup)
    - jwcrypto installed (pip install jwcrypto)

Run with: just example-jws
"""

from __future__ import annotations

import json
import os

from jwcrypto.jws import JWS
from jwcrypto.common import json_encode

from hsmkey import HSMJWK, hsm_session


def main():
    # Configuration - adjust these for your environment
    module_path = os.environ.get(
        "HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"
    )
    token_label = os.environ.get("HSM_TOKEN", "hsmkey-test")
    pin = os.environ.get("HSM_PIN", "12345678")

    print("=" * 60)
    print("JWS Signing Example with HSM Keys")
    print("=" * 60)

    # Use context manager for automatic session cleanup
    with hsm_session(module_path, token_label, pin) as session:
        # Example 1: RSA Signing with RS256
        print("\n1. RSA Signing (RS256)")
        print("-" * 40)

        rsa_key = HSMJWK.from_hsm(session, key_label="rsa-2048", kid="rsa-key-1")
        payload = b'{"sub": "user@example.com", "role": "admin"}'

        jws = JWS(payload)
        jws.add_signature(
            rsa_key,
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "rsa-key-1"}),
        )
        token = jws.serialize(compact=True)

        print(f"Payload: {payload.decode()}")
        print(f"Signed Token: {token[:80]}...")

        # Verify the signature
        jws_verify = JWS()
        jws_verify.deserialize(token, rsa_key)
        print(f"Verified: {jws_verify.payload == payload}")

        # Example 2: ECDSA Signing with ES256
        print("\n2. ECDSA Signing (ES256)")
        print("-" * 40)

        ec_key = HSMJWK.from_hsm(session, key_label="ec-p256", kid="ec-key-1")

        jws_ec = JWS(payload)
        jws_ec.add_signature(
            ec_key,
            alg="ES256",
            protected=json_encode({"alg": "ES256", "kid": "ec-key-1"}),
        )
        token_ec = jws_ec.serialize(compact=True)

        print(f"Signed Token (EC): {token_ec[:80]}...")

        # Verify
        jws_ec_verify = JWS()
        jws_ec_verify.deserialize(token_ec, ec_key)
        print(f"Verified: {jws_ec_verify.payload == payload}")

        # Example 3: EdDSA Signing with Ed25519
        print("\n3. EdDSA Signing (Ed25519)")
        print("-" * 40)

        ed_key = HSMJWK.from_hsm(session, key_label="ed25519", kid="ed-key-1")

        jws_ed = JWS(payload)
        jws_ed.add_signature(
            ed_key,
            alg="EdDSA",
            protected=json_encode({"alg": "EdDSA", "kid": "ed-key-1"}),
        )
        token_ed = jws_ed.serialize(compact=True)

        print(f"Signed Token (EdDSA): {token_ed[:80]}...")

        # Verify
        jws_ed_verify = JWS()
        jws_ed_verify.deserialize(token_ed, ed_key)
        print(f"Verified: {jws_ed_verify.payload == payload}")

        # Example 4: RSA-PSS Signing
        print("\n4. RSA-PSS Signing (PS256)")
        print("-" * 40)

        jws_pss = JWS(payload)
        jws_pss.add_signature(
            rsa_key,
            alg="PS256",
            protected=json_encode({"alg": "PS256", "kid": "rsa-key-1"}),
        )
        token_pss = jws_pss.serialize(compact=True)

        print(f"Signed Token (PSS): {token_pss[:80]}...")

        # Verify
        jws_pss_verify = JWS()
        jws_pss_verify.deserialize(token_pss, rsa_key)
        print(f"Verified: {jws_pss_verify.payload == payload}")

        # Example 5: Export Public Key for External Verification
        print("\n5. Export Public Key")
        print("-" * 40)

        public_jwk = rsa_key.export_public(as_dict=True)
        print(f"Public JWK (kty): {public_jwk['kty']}")
        print(f"Public JWK (n): {public_jwk['n'][:40]}...")
        print(f"Private key (d) exported: {'d' in public_jwk}")

    print("\n" + "=" * 60)
    print("All JWS examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
