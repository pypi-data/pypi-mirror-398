#!/usr/bin/env python3
"""Example: JWT Creation and Validation with HSM Keys.

This example demonstrates how to create and validate JSON Web Tokens (JWT)
using HSM-backed keys with the hsmkey library.

Prerequisites:
    - SoftHSM2 installed and configured
    - Test keys imported (run: just setup)
    - jwcrypto installed (pip install jwcrypto)

Run with: just example-jwt
"""

from __future__ import annotations

import json
import os
import time

from jwcrypto.jwt import JWT

from hsmkey import HSMJWK, hsm_session


def main():
    # Configuration
    module_path = os.environ.get(
        "HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"
    )
    token_label = os.environ.get("HSM_TOKEN", "hsmkey-test")
    pin = os.environ.get("HSM_PIN", "12345678")

    print("=" * 60)
    print("JWT Example with HSM Keys")
    print("=" * 60)

    with hsm_session(module_path, token_label, pin) as session:
        # Example 1: Basic JWT with Standard Claims
        print("\n1. Basic JWT with Standard Claims (RS256)")
        print("-" * 40)

        rsa_key = HSMJWK.from_hsm(session, key_label="rsa-2048", kid="jwt-signing-key")

        now = int(time.time())
        claims = {
            "iss": "https://auth.example.com",
            "sub": "user123",
            "aud": "https://api.example.com",
            "iat": now,
            "exp": now + 3600,  # 1 hour expiration
            "nbf": now,
        }

        token = JWT(header={"alg": "RS256", "kid": "jwt-signing-key"}, claims=claims)
        token.make_signed_token(rsa_key)
        serialized = token.serialize()

        print(f"Claims: {json.dumps(claims, indent=2)}")
        print(f"Token: {serialized[:80]}...")

        # Verify the token
        verified = JWT(jwt=serialized, key=rsa_key)
        verified_claims = json.loads(verified.claims)
        print(f"Verified subject: {verified_claims['sub']}")

        # Example 2: JWT with Custom Claims
        print("\n2. JWT with Custom Claims (ES256)")
        print("-" * 40)

        ec_key = HSMJWK.from_hsm(session, key_label="ec-p256", kid="ec-jwt-key")

        custom_claims = {
            "sub": "service-account",
            "iss": "https://auth.example.com",
            "scope": "read write admin",
            "roles": ["admin", "operator"],
            "metadata": {"department": "engineering", "level": 5},
            "iat": now,
            "exp": now + 7200,
        }

        token2 = JWT(header={"alg": "ES256", "kid": "ec-jwt-key"}, claims=custom_claims)
        token2.make_signed_token(ec_key)
        serialized2 = token2.serialize()

        print(f"Token: {serialized2[:80]}...")

        verified2 = JWT(jwt=serialized2, key=ec_key)
        verified_claims2 = json.loads(verified2.claims)
        print(f"Roles: {verified_claims2['roles']}")
        print(f"Scope: {verified_claims2['scope']}")

        # Example 3: EdDSA JWT
        print("\n3. EdDSA JWT (Ed25519)")
        print("-" * 40)

        ed_key = HSMJWK.from_hsm(session, key_label="ed25519", kid="ed-jwt-key")

        ed_claims = {
            "sub": "user@example.com",
            "iss": "https://auth.example.com",
            "iat": now,
            "exp": now + 3600,
        }

        token3 = JWT(header={"alg": "EdDSA", "kid": "ed-jwt-key"}, claims=ed_claims)
        token3.make_signed_token(ed_key)
        serialized3 = token3.serialize()

        print(f"Token: {serialized3[:80]}...")

        verified3 = JWT(jwt=serialized3, key=ed_key)
        print(f"Verified: {json.loads(verified3.claims)['sub']}")

        # Example 4: Encrypted JWT (JWE)
        print("\n4. Encrypted JWT (RSA-OAEP)")
        print("-" * 40)

        encrypt_claims = {
            "sub": "confidential-user",
            "secret_data": "This information is encrypted",
            "credit_card": "4111-xxxx-xxxx-1111",
        }

        encrypted_token = JWT(
            header={"alg": "RSA-OAEP", "enc": "A256GCM"},
            claims=encrypt_claims,
        )
        encrypted_token.make_encrypted_token(rsa_key)
        encrypted_serialized = encrypted_token.serialize()

        print(f"Encrypted Token: {encrypted_serialized[:80]}...")
        print(f"Token parts: {len(encrypted_serialized.split('.'))}")

        # Decrypt
        decrypted = JWT(jwt=encrypted_serialized, key=rsa_key, expected_type="JWE")
        decrypted_claims = json.loads(decrypted.claims)
        print(f"Decrypted secret_data: {decrypted_claims['secret_data']}")

        # Example 5: Nested JWT (Signed then Encrypted)
        print("\n5. Nested JWT (Signed then Encrypted)")
        print("-" * 40)

        # First, sign the JWT
        inner_claims = {
            "sub": "protected-user",
            "iss": "https://auth.example.com",
            "iat": now,
            "exp": now + 3600,
            "sensitive": "This is both signed and encrypted",
        }

        inner_token = JWT(header={"alg": "ES256"}, claims=inner_claims)
        inner_token.make_signed_token(ec_key)
        signed_jwt = inner_token.serialize()

        print("Inner JWT signed with EC key")

        # Then, encrypt the signed JWT
        outer_token = JWT(
            header={"alg": "RSA-OAEP", "enc": "A256GCM", "cty": "JWT"},
            claims=signed_jwt,
        )
        outer_token.make_encrypted_token(rsa_key)
        nested_jwt = outer_token.serialize()

        print(f"Nested JWT: {nested_jwt[:80]}...")

        # Decrypt outer layer
        decrypted_outer = JWT(jwt=nested_jwt, key=rsa_key, expected_type="JWE")
        inner_jwt_str = decrypted_outer.claims

        # Verify inner signature
        verified_inner = JWT(jwt=inner_jwt_str, key=ec_key)
        final_claims = json.loads(verified_inner.claims)
        print(f"Final claims: sub={final_claims['sub']}")
        print(f"Sensitive data: {final_claims['sensitive']}")

        # Example 6: Access Token Pattern
        print("\n6. Access Token Pattern")
        print("-" * 40)

        access_token_claims = {
            "iss": "https://auth.example.com",
            "sub": "user-12345",
            "aud": ["https://api.example.com", "https://admin.example.com"],
            "iat": now,
            "exp": now + 900,  # 15 minutes
            "scope": "openid profile email",
            "client_id": "webapp-client",
            "token_type": "access_token",
        }

        access_token = JWT(
            header={"alg": "RS256", "kid": "jwt-signing-key", "typ": "at+jwt"},
            claims=access_token_claims,
        )
        access_token.make_signed_token(rsa_key)

        print(f"Access Token: {access_token.serialize()[:80]}...")
        print(f"Expires in: {access_token_claims['exp'] - now} seconds")

    print("\n" + "=" * 60)
    print("All JWT examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
