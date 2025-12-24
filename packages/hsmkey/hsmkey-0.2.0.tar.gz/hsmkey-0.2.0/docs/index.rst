hsmkey Documentation
====================

**hsmkey** is a Python library that provides HSM-backed cryptographic keys
compatible with the Python cryptography library and `jwcrypto
<https://jwcrypto.readthedocs.io/en/latest/>`_. It allows you to use Hardware
Security Module (HSM) keys for signing, verification, encryption, and
decryption operations while keeping private keys secure within the HSM.

Key Features
------------

- **JWCrypto Integration**: Seamless integration with jwcrypto for JWS, JWE, and JWT operations
- **Multiple Key Types**: Support for RSA, ECDSA (P-256, P-384, P-521), and EdDSA (Ed25519, Ed448)
- **PKCS#11 Compatible**: Works with any PKCS#11-compatible HSM (SoftHSM2, Kryoptic, etc.)
- **Thread-Safe**: Session pool for safe concurrent access
- **Private Key Protection**: Private keys never leave the HSM

Quick Example
-------------

.. code-block:: python

    from jwcrypto.jws import JWS
    from jwcrypto.common import json_encode
    from hsmkey import HSMJWK, hsm_session

    # Open HSM session and create JWS signature
    with hsm_session("/usr/lib/softhsm/libsofthsm2.so", "my-token", "1234") as session:
        key = HSMJWK.from_hsm(session, key_label="my-rsa-key")

        jws = JWS(b'{"user": "alice"}')
        jws.add_signature(key, alg="RS256", protected=json_encode({"alg": "RS256"}))
        token = jws.serialize(compact=True)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   keys
   jwcrypto
   session_management

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

.. toctree::
   :maxdepth: 2
   :caption: Development

   development


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
