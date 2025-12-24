JWCrypto Integration
====================

hsmkey provides seamless integration with jwcrypto for JSON Web operations.
This guide covers JWS (signing), JWE (encryption), and JWT (tokens).

Overview
--------

The ``HSMJWK`` class extends jwcrypto's ``JWK`` class, allowing HSM-backed keys
to be used anywhere a regular JWK is expected. The private key operations
(signing, decryption) are performed inside the HSM, while public key
operations use the exported public key material.

HSMJWK Class
------------

Creating an HSMJWK
^^^^^^^^^^^^^^^^^^

Load a key from the HSM:

.. code-block:: python

    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        # Load by label
        key = HSMJWK.from_hsm(session, key_label="my-key")

        # Load by ID
        key = HSMJWK.from_hsm(session, key_id=b'\x01')

        # With additional JWK parameters
        key = HSMJWK.from_hsm(
            session,
            key_label="my-key",
            kid="unique-key-id",
            use="sig",
            key_ops=["sign", "verify"]
        )

Exporting Public Keys
^^^^^^^^^^^^^^^^^^^^^

Export the public key (private key export is blocked):

.. code-block:: python

    # Export as dict
    public_jwk = key.export_public(as_dict=True)
    print(public_jwk)
    # {'kty': 'RSA', 'n': '...', 'e': 'AQAB', 'kid': 'my-key'}

    # Export as JSON string
    public_json = key.export_public()

    # Private key export raises an error
    try:
        key.export_private()  # Raises HSMSessionError
    except HSMSessionError:
        print("Private key cannot be exported from HSM")

JWS Signing
-----------

Supported Algorithms
^^^^^^^^^^^^^^^^^^^^

**RSA:**

- RS256, RS384, RS512 (RSASSA-PKCS1-v1_5)
- PS256, PS384, PS512 (RSASSA-PSS)

**ECDSA:**

- ES256 (P-256)
- ES384 (P-384)
- ES512 (P-521)

**EdDSA:**

- EdDSA (Ed25519, Ed448)

Basic Signing
^^^^^^^^^^^^^

.. code-block:: python

    from jwcrypto.jws import JWS
    from jwcrypto.common import json_encode
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        payload = b'{"sub": "user@example.com"}'
        jws = JWS(payload)
        jws.add_signature(
            key,
            alg="RS256",
            protected=json_encode({"alg": "RS256"})
        )

        # Compact serialization (3 parts)
        token = jws.serialize(compact=True)

        # JSON serialization
        json_token = jws.serialize()

Signing with Multiple Keys
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    jws = JWS(payload)

    # Add signature with RSA key
    jws.add_signature(
        rsa_key,
        alg="RS256",
        protected=json_encode({"alg": "RS256", "kid": "rsa-key"})
    )

    # Add signature with EC key
    jws.add_signature(
        ec_key,
        alg="ES256",
        protected=json_encode({"alg": "ES256", "kid": "ec-key"})
    )

    # JSON serialization supports multiple signatures
    multi_sig_token = jws.serialize()

Verification
^^^^^^^^^^^^

.. code-block:: python

    # Verify with HSM key
    jws = JWS()
    jws.deserialize(token, key)
    verified_payload = jws.payload

    # Verify with exported public key (software verification)
    from jwcrypto.jwk import JWK

    public_jwk = JWK(**hsm_key.export_public(as_dict=True))
    jws = JWS()
    jws.deserialize(token, public_jwk)

JWE Encryption
--------------

Supported Algorithms
^^^^^^^^^^^^^^^^^^^^

**Key Encryption:**

- RSA-OAEP (RSA with OAEP padding using SHA-1)

**Content Encryption:**

- A128GCM, A192GCM, A256GCM
- A128CBC-HS256, A192CBC-HS384, A256CBC-HS512

Encryption
^^^^^^^^^^

.. code-block:: python

    import json
    from jwcrypto.jwe import JWE
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        plaintext = b"Confidential data"
        jwe = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"})
        )
        jwe.add_recipient(key)

        # Compact serialization (5 parts)
        encrypted = jwe.serialize(compact=True)

Decryption
^^^^^^^^^^

.. code-block:: python

    jwe = JWE()
    jwe.deserialize(encrypted, key)
    decrypted = jwe.payload

Hybrid Encryption Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^

Encrypt with public key (software), decrypt with HSM:

.. code-block:: python

    from jwcrypto.jwk import JWK

    with hsm_session(module_path, token_label, pin) as session:
        hsm_key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Get public key for encryption (can be distributed)
        public_jwk = JWK(**hsm_key.export_public(as_dict=True))

        # Encrypt with public key (no HSM needed)
        jwe = JWE(
            b"Secret message",
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"})
        )
        jwe.add_recipient(public_jwk)
        encrypted = jwe.serialize(compact=True)

        # Decrypt with HSM (private key never exported)
        jwe2 = JWE()
        jwe2.deserialize(encrypted, hsm_key)
        plaintext = jwe2.payload

JWT Tokens
----------

Signed JWT
^^^^^^^^^^

.. code-block:: python

    import time
    from jwcrypto.jwt import JWT
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048", kid="jwt-key")

        claims = {
            "iss": "https://auth.example.com",
            "sub": "user123",
            "aud": "https://api.example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }

        token = JWT(
            header={"alg": "RS256", "kid": "jwt-key"},
            claims=claims
        )
        token.make_signed_token(key)

        jwt_string = token.serialize()

JWT Verification
^^^^^^^^^^^^^^^^

.. code-block:: python

    verified = JWT(jwt=jwt_string, key=key)
    claims = json.loads(verified.claims)

Encrypted JWT
^^^^^^^^^^^^^

.. code-block:: python

    claims = {
        "sub": "user123",
        "sensitive_data": "confidential"
    }

    token = JWT(
        header={"alg": "RSA-OAEP", "enc": "A256GCM"},
        claims=claims
    )
    token.make_encrypted_token(key)

    encrypted_jwt = token.serialize()

    # Decrypt
    decrypted = JWT(jwt=encrypted_jwt, key=key, expected_type="JWE")
    claims = json.loads(decrypted.claims)

Nested JWT (Signed then Encrypted)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # First, sign with one key
    inner = JWT(header={"alg": "ES256"}, claims=claims)
    inner.make_signed_token(signing_key)
    signed_jwt = inner.serialize()

    # Then, encrypt with another key
    outer = JWT(
        header={"alg": "RSA-OAEP", "enc": "A256GCM", "cty": "JWT"},
        claims=signed_jwt
    )
    outer.make_encrypted_token(encryption_key)
    nested_jwt = outer.serialize()

    # To verify: decrypt then verify
    decrypted_outer = JWT(jwt=nested_jwt, key=encryption_key, expected_type="JWE")
    inner_jwt = decrypted_outer.claims

    verified_inner = JWT(jwt=inner_jwt, key=signing_key)
    final_claims = json.loads(verified_inner.claims)

HSMJWKSet for Key Management
----------------------------

Manage multiple HSM keys:

.. code-block:: python

    from hsmkey import HSMJWKSet, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        jwk_set = HSMJWKSet(session)

        # Add keys
        rsa_key = jwk_set.add_key(key_label="rsa-2048", kid="rsa-signing")
        ec_key = jwk_set.add_key(key_label="ec-p256", kid="ec-signing")

        # Get key by ID
        key = jwk_set.get_key("rsa-signing")

        # Iterate over keys
        for key in jwk_set:
            print(key.export_public(as_dict=True))

        # Export public JWKS for .well-known/jwks.json
        public_keys = [k.export_public(as_dict=True) for k in jwk_set]
        jwks = {"keys": public_keys}

Key Rotation Pattern
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    with hsm_session(module_path, token_label, pin) as session:
        jwk_set = HSMJWKSet(session)

        # Old key for verification of existing tokens
        old_key = jwk_set.add_key(key_label="rsa-2048", kid="key-v1")

        # New key for signing new tokens
        new_key = jwk_set.add_key(key_label="rsa-3072", kid="key-v2")

        # Sign new tokens with new key
        jws = JWS(payload)
        jws.add_signature(
            new_key,
            alg="RS384",
            protected=json_encode({"alg": "RS384", "kid": "key-v2"})
        )

        # Old tokens can still be verified
        old_token = "..."
        old_key = jwk_set.get_key("key-v1")
        if old_key:
            jws = JWS()
            jws.deserialize(old_token, old_key)

Error Handling
--------------

.. code-block:: python

    from hsmkey import HSMJWK, hsm_session
    from hsmkey.exceptions import HSMKeyNotFoundError, HSMSessionError

    with hsm_session(module_path, token_label, pin) as session:
        try:
            key = HSMJWK.from_hsm(session, key_label="nonexistent")
        except HSMKeyNotFoundError as e:
            print(f"Key not found: {e}")

        try:
            key = HSMJWK.from_hsm(session, key_label="rsa-2048")
            key.export_private()  # Attempt to export private key
        except HSMSessionError as e:
            print(f"Operation not allowed: {e}")

Best Practices
--------------

1. **Use Context Managers**: Always use ``hsm_session`` for automatic cleanup
2. **Cache Keys**: Load keys once and reuse within a session
3. **Use Key IDs**: Always specify ``kid`` for key identification
4. **Limit Session Scope**: Keep sessions short to release HSM resources
5. **Handle Errors**: Catch specific exceptions for better error handling
