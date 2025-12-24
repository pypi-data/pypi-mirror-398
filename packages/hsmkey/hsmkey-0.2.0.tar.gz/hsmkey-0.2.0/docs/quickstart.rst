Quick Start
===========

This guide will help you get started with hsmkey for common cryptographic operations.

Prerequisites
-------------

Before starting, ensure you have:

1. Installed hsmkey with jwcrypto support: ``pip install hsmkey[jwcrypto]``
2. A configured PKCS#11 token (see :doc:`installation`)
3. Keys imported to your HSM

Basic Session Management
------------------------

Use the ``hsm_session`` context manager for automatic session handling:

.. code-block:: python

    from hsmkey import hsm_session, HSMJWK

    # Configuration
    module_path = "/usr/lib/softhsm/libsofthsm2.so"
    token_label = "my-token"
    pin = "12345678"

    with hsm_session(module_path, token_label, pin) as session:
        # Work with HSM keys here
        key = HSMJWK.from_hsm(session, key_label="my-rsa-key")
        print(f"Key type: {key.export_public(as_dict=True)['kty']}")

Signing a JWS Token
-------------------

Create a signed JSON Web Signature:

.. code-block:: python

    from jwcrypto.jws import JWS
    from jwcrypto.common import json_encode
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        # Load RSA key from HSM
        key = HSMJWK.from_hsm(session, key_label="rsa-2048", kid="signing-key")

        # Create and sign
        payload = b'{"user": "alice", "role": "admin"}'
        jws = JWS(payload)
        jws.add_signature(
            key,
            alg="RS256",
            protected=json_encode({"alg": "RS256", "kid": "signing-key"})
        )

        # Get the compact serialization
        token = jws.serialize(compact=True)
        print(f"Signed token: {token}")

Verifying a JWS Token
---------------------

Verify a signed token:

.. code-block:: python

    from jwcrypto.jws import JWS
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Verify
        jws = JWS()
        jws.deserialize(token, key)

        print(f"Verified payload: {jws.payload.decode()}")

Encrypting with JWE
-------------------

Encrypt data with RSA-OAEP:

.. code-block:: python

    import json
    from jwcrypto.jwe import JWE
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Encrypt
        plaintext = b"Secret message"
        jwe = JWE(
            plaintext,
            protected=json.dumps({"alg": "RSA-OAEP", "enc": "A256GCM"})
        )
        jwe.add_recipient(key)

        encrypted = jwe.serialize(compact=True)
        print(f"Encrypted: {encrypted}")

Decrypting with JWE
-------------------

Decrypt data:

.. code-block:: python

    from jwcrypto.jwe import JWE
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Decrypt
        jwe = JWE()
        jwe.deserialize(encrypted, key)

        print(f"Decrypted: {jwe.payload.decode()}")

Creating a JWT
--------------

Create a signed JWT with claims:

.. code-block:: python

    import time
    from jwcrypto.jwt import JWT
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="rsa-2048")

        claims = {
            "sub": "user@example.com",
            "iss": "https://auth.example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour
        }

        token = JWT(header={"alg": "RS256"}, claims=claims)
        token.make_signed_token(key)

        print(f"JWT: {token.serialize()}")

Working with EC Keys
--------------------

ECDSA signing with P-256:

.. code-block:: python

    from jwcrypto.jws import JWS
    from jwcrypto.common import json_encode
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="ec-p256")

        jws = JWS(b'{"data": "value"}')
        jws.add_signature(
            key,
            alg="ES256",
            protected=json_encode({"alg": "ES256"})
        )

        token = jws.serialize(compact=True)

Working with EdDSA Keys
-----------------------

EdDSA signing with Ed25519:

.. code-block:: python

    from jwcrypto.jws import JWS
    from jwcrypto.common import json_encode
    from hsmkey import HSMJWK, hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        key = HSMJWK.from_hsm(session, key_label="ed25519")

        jws = JWS(b'{"data": "value"}')
        jws.add_signature(
            key,
            alg="EdDSA",
            protected=json_encode({"alg": "EdDSA"})
        )

        token = jws.serialize(compact=True)

Next Steps
----------

- See :doc:`jwcrypto` for detailed JWCrypto integration guide
- See :doc:`session_management` for session pool usage
- See :doc:`api` for API reference
