#!/usr/bin/env python3
"""Example: JWE Encryption and Decryption with HSM Keys.

This example demonstrates how to encrypt and decrypt JSON Web Encryption (JWE)
using HSM-backed keys with the hsmkey library.

Prerequisites:
    - SoftHSM2 installed and configured
    - Test keys imported (run: just setup)
    - jwcrypto installed (pip install jwcrypto)

Run with: just example-jwe
"""

from __future__ import annotations

import json
import os

from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK

from hsmkey import HSMJWK, hsm_session


def main():
    # Configuration
    module_path = os.environ.get(
        "HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"
    )
    token_label = os.environ.get("HSM_TOKEN", "hsmkey-test")
    pin = os.environ.get("HSM_PIN", "12345678")

    print("=" * 60)
    print("JWE Encryption Example with HSM Keys")
    print("=" * 60)

    with hsm_session(module_path, token_label, pin) as session:
        # Example 1: RSA-OAEP Encryption
        print("\n1. RSA-OAEP Encryption with A256GCM")
        print("-" * 40)

        rsa_key = HSMJWK.from_hsm(session, key_label="rsa-2048", kid="encrypt-key")
        plaintext = b"This is a secret message that needs encryption!"

        # Encrypt
        jwe = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe.add_recipient(rsa_key)
        token = jwe.serialize(compact=True)

        print(f"Plaintext: {plaintext.decode()}")
        print(f"Encrypted Token: {token[:80]}...")

        # Decrypt with HSM key
        jwe_decrypt = JWE()
        jwe_decrypt.deserialize(token, rsa_key)
        print(f"Decrypted: {jwe_decrypt.payload.decode()}")
        print(f"Match: {jwe_decrypt.payload == plaintext}")

        # Example 2: RSA-OAEP with A128GCM Content Encryption
        print("\n2. RSA-OAEP with A128GCM")
        print("-" * 40)

        jwe2 = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A128GCM"}),
        )
        jwe2.add_recipient(rsa_key)
        token2 = jwe2.serialize(compact=True)

        print(f"Encrypted Token: {token2[:80]}...")

        jwe2_decrypt = JWE()
        jwe2_decrypt.deserialize(token2, rsa_key)
        print(f"Decrypted: {jwe2_decrypt.payload.decode()}")

        # Example 3: Encrypt with Software Key, Decrypt with HSM
        print("\n3. Encrypt with Public Key, Decrypt with HSM")
        print("-" * 40)

        # Export public key and create software-only JWK
        public_params = rsa_key.export_public(as_dict=True)
        public_key = JWK(**public_params)

        # Encrypt with public key (software operation)
        jwe3 = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe3.add_recipient(public_key)
        token3 = jwe3.serialize(compact=True)

        print("Encrypted with software public key")

        # Decrypt with HSM (private key never leaves HSM)
        jwe3_decrypt = JWE()
        jwe3_decrypt.deserialize(token3, rsa_key)
        print(f"Decrypted with HSM: {jwe3_decrypt.payload.decode()}")

        # Example 4: Large Payload Encryption
        print("\n4. Large Payload Encryption (10KB)")
        print("-" * 40)

        large_payload = b"X" * 10240
        jwe4 = JWE(
            large_payload,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe4.add_recipient(rsa_key)
        token4 = jwe4.serialize(compact=True)

        print(f"Payload size: {len(large_payload)} bytes")
        print(f"Token size: {len(token4)} bytes")

        jwe4_decrypt = JWE()
        jwe4_decrypt.deserialize(token4, rsa_key)
        print(f"Decryption successful: {jwe4_decrypt.payload == large_payload}")

        # Example 5: Different RSA Key Sizes
        print("\n5. Encryption with RSA-4096 Key")
        print("-" * 40)

        rsa_4096 = HSMJWK.from_hsm(session, key_label="rsa-4096")
        jwe5 = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"}),
        )
        jwe5.add_recipient(rsa_4096)
        token5 = jwe5.serialize(compact=True)

        print(f"Encrypted with RSA-4096")
        print(f"Token: {token5[:80]}...")

        jwe5_decrypt = JWE()
        jwe5_decrypt.deserialize(token5, rsa_4096)
        print(f"Decrypted: {jwe5_decrypt.payload.decode()}")

    print("\n" + "=" * 60)
    print("All JWE examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
