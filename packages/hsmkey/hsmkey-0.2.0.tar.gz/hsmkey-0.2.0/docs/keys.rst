HSM Key Classes
===============

The ``hsmkey.keys`` module provides HSM-backed key classes that implement
the Python cryptography library interfaces. These classes allow cryptographic
operations to be performed on the HSM while maintaining API compatibility with
standard cryptography library keys.

Key Architecture
----------------

All private key classes inherit from ``PKCS11PrivateKeyMixin`` which provides:

- Lazy loading of PKCS#11 key objects
- Session management
- Key lookup by ID or label
- Protection against private key extraction

.. code-block:: python

    from hsmkey import hsm_session
    from hsmkey.keys import PKCS11RSAPrivateKey

    with hsm_session("/usr/lib/softhsm/libsofthsm2.so", "my-token", "1234") as session:
        # Load key by label
        key = PKCS11RSAPrivateKey(session, key_label="my-rsa-key")

        # Or by ID
        key = PKCS11RSAPrivateKey(session, key_id=b'\x01')

Key Types
---------

RSA Keys
^^^^^^^^

**PKCS11RSAPrivateKey**

RSA private key backed by HSM. Implements ``cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey``.

.. code-block:: python

    from hsmkey.keys import PKCS11RSAPrivateKey
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # Create RSA private key reference
    rsa_key = PKCS11RSAPrivateKey(session, key_label="rsa-2048")

    # Get key size
    print(f"Key size: {rsa_key.key_size} bits")

    # Sign data
    signature = rsa_key.sign(
        b"data to sign",
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # Decrypt data
    plaintext = rsa_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Get public key
    public_key = rsa_key.public_key()

**Supported Operations:**

- ``sign(data, padding, algorithm)`` - Sign data with PKCS#1 v1.5 or PSS padding
- ``decrypt(ciphertext, padding)`` - Decrypt with PKCS#1 v1.5 or OAEP padding
- ``public_key()`` - Extract the public key
- ``key_size`` - Get key size in bits

**Unsupported Operations (private key never leaves HSM):**

- ``private_numbers()`` - Raises ``HSMUnsupportedError``
- ``private_bytes()`` - Raises ``HSMUnsupportedError``
- ``private_bytes_raw()`` - Raises ``HSMUnsupportedError``

**PKCS11RSAPublicKey**

RSA public key extracted from HSM. Implements ``cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey``.

.. code-block:: python

    # Get public key from private key
    public_key = rsa_key.public_key()

    # Verify signature
    public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())

    # Encrypt data
    ciphertext = public_key.encrypt(plaintext, padding.OAEP(...))

    # Serialize public key
    pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

Elliptic Curve Keys
^^^^^^^^^^^^^^^^^^^

**PKCS11EllipticCurvePrivateKey**

EC private key backed by HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey``.

Supported curves:

- P-256 (secp256r1)
- P-384 (secp384r1)
- P-521 (secp521r1)
- secp256k1
- Brainpool curves (P256r1, P384r1, P512r1)

.. code-block:: python

    from hsmkey.keys import PKCS11EllipticCurvePrivateKey
    from cryptography.hazmat.primitives.asymmetric import ec

    # Create EC private key reference
    ec_key = PKCS11EllipticCurvePrivateKey(session, key_label="ec-p256")

    # Get curve information
    print(f"Curve: {ec_key.curve.name}")
    print(f"Key size: {ec_key.key_size} bits")

    # Sign data with ECDSA
    signature = ec_key.sign(
        b"data to sign",
        ec.ECDSA(hashes.SHA256())
    )

    # ECDH key exchange
    shared_secret = ec_key.exchange(ec.ECDH(), peer_public_key)

    # Get public key
    public_key = ec_key.public_key()

**Supported Operations:**

- ``sign(data, signature_algorithm)`` - ECDSA signing (returns DER-encoded signature)
- ``exchange(algorithm, peer_public_key)`` - ECDH key exchange
- ``public_key()`` - Extract the public key
- ``curve`` - Get the elliptic curve
- ``key_size`` - Get key size in bits

**PKCS11EllipticCurvePublicKey**

EC public key extracted from HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePublicKey``.

.. code-block:: python

    # Get public key
    public_key = ec_key.public_key()

    # Verify signature
    public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))

    # Get public numbers (x, y coordinates)
    numbers = public_key.public_numbers()
    print(f"X: {numbers.x}")
    print(f"Y: {numbers.y}")

    # Serialize
    pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

Ed25519 Keys
^^^^^^^^^^^^

**PKCS11Ed25519PrivateKey**

Ed25519 private key backed by HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey``.

Ed25519 is a modern elliptic curve signature scheme known for:

- Fast signature generation and verification
- Small signatures (64 bytes)
- Strong security with 128-bit security level
- Deterministic signatures (no random number needed)

.. code-block:: python

    from hsmkey.keys import PKCS11Ed25519PrivateKey

    # Create Ed25519 private key reference
    ed_key = PKCS11Ed25519PrivateKey(session, key_label="ed25519")

    # Sign data (Ed25519 handles hashing internally)
    signature = ed_key.sign(b"data to sign")
    assert len(signature) == 64  # Ed25519 signatures are 64 bytes

    # Get public key
    public_key = ed_key.public_key()

**PKCS11Ed25519PublicKey**

Ed25519 public key extracted from HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey``.

.. code-block:: python

    # Get public key
    public_key = ed_key.public_key()

    # Verify signature
    public_key.verify(signature, data)

    # Get raw public key bytes (32 bytes)
    raw_bytes = public_key.public_bytes_raw()

Ed448 Keys
^^^^^^^^^^

**PKCS11Ed448PrivateKey**

Ed448 private key backed by HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ed448.Ed448PrivateKey``.

Ed448 provides stronger security than Ed25519:

- 224-bit security level
- Larger signatures (114 bytes)
- 57-byte public keys

.. code-block:: python

    from hsmkey.keys import PKCS11Ed448PrivateKey

    # Create Ed448 private key reference
    ed_key = PKCS11Ed448PrivateKey(session, key_label="ed448")

    # Sign data
    signature = ed_key.sign(b"data to sign")
    assert len(signature) == 114  # Ed448 signatures are 114 bytes

    # Get public key
    public_key = ed_key.public_key()

**PKCS11Ed448PublicKey**

Ed448 public key extracted from HSM. Implements ``cryptography.hazmat.primitives.asymmetric.ed448.Ed448PublicKey``.

.. code-block:: python

    # Get public key
    public_key = ed_key.public_key()

    # Verify signature
    public_key.verify(signature, data)

    # Get raw public key bytes (57 bytes)
    raw_bytes = public_key.public_bytes_raw()

Base Class
----------

**PKCS11PrivateKeyMixin**

Base mixin class providing common functionality for all HSM-backed private keys.

.. code-block:: python

    from hsmkey.keys import PKCS11PrivateKeyMixin

Key features:

- **Lazy loading**: PKCS#11 key objects are loaded on first use
- **Key lookup**: Find keys by ID (``CKA_ID``) or label (``CKA_LABEL``)
- **Session management**: Maintains reference to PKCS#11 session
- **Private key protection**: Operations that would export private key material raise ``HSMUnsupportedError``

Properties:

- ``pkcs11_private_key`` - Get the underlying PKCS#11 private key object
- ``pkcs11_public_key`` - Get the underlying PKCS#11 public key object

Using Keys with JWCrypto
------------------------

For JWCrypto integration, use the ``HSMJWK`` class instead of raw key classes:

.. code-block:: python

    from hsmkey import HSMJWK, hsm_session
    from jwcrypto.jws import JWS

    with hsm_session("/usr/lib/softhsm/libsofthsm2.so", "my-token", "1234") as session:
        # HSMJWK wraps the key classes for JWCrypto compatibility
        jwk = HSMJWK.from_hsm(session, key_label="rsa-2048")

        # Use with JWS
        jws = JWS(b"payload")
        jws.add_signature(jwk, alg="RS256", protected='{"alg":"RS256"}')

See :doc:`jwcrypto` for complete JWCrypto integration documentation.

Error Handling
--------------

Key operations may raise the following exceptions:

.. code-block:: python

    from hsmkey.exceptions import (
        HSMKeyNotFoundError,
        HSMOperationError,
        HSMUnsupportedError,
    )

    try:
        key = PKCS11RSAPrivateKey(session, key_label="nonexistent")
        key.sign(data, padding, algorithm)
    except HSMKeyNotFoundError:
        print("Key not found in HSM")
    except HSMOperationError as e:
        print(f"HSM operation failed: {e}")

    try:
        # Attempting to extract private key material
        key.private_bytes(...)
    except HSMUnsupportedError:
        print("Private key cannot be extracted from HSM")

Algorithm Support
-----------------

The following table summarizes algorithm support for each key type:

+------------------------+----------------------------------+---------------------------+
| Key Type               | Signing Algorithms               | Encryption/Key Exchange   |
+========================+==================================+===========================+
| RSA                    | PKCS#1 v1.5, PSS                 | PKCS#1 v1.5, OAEP         |
|                        | (SHA-256, SHA-384, SHA-512)      |                           |
+------------------------+----------------------------------+---------------------------+
| EC (P-256, P-384,      | ECDSA                            | ECDH                      |
| P-521)                 | (SHA-256, SHA-384, SHA-512)      |                           |
+------------------------+----------------------------------+---------------------------+
| Ed25519                | EdDSA (built-in hashing)         | N/A                       |
+------------------------+----------------------------------+---------------------------+
| Ed448                  | EdDSA (built-in hashing)         | N/A                       |
+------------------------+----------------------------------+---------------------------+
