API Reference
=============

This section provides detailed API documentation for all hsmkey modules.

JWCrypto Integration
--------------------

HSMJWK
^^^^^^

.. autoclass:: hsmkey.jwk_integration.HSMJWK
   :members:
   :undoc-members:
   :show-inheritance:

HSMJWKSet
^^^^^^^^^

.. autoclass:: hsmkey.jwk_integration.HSMJWKSet
   :members:
   :undoc-members:
   :show-inheritance:

hsm_session
^^^^^^^^^^^

.. autofunction:: hsmkey.jwk_integration.hsm_session

jwk_from_hsm
^^^^^^^^^^^^

.. autofunction:: hsmkey.jwk_integration.jwk_from_hsm

Session Management
------------------

SessionPool
^^^^^^^^^^^

.. autoclass:: hsmkey.session.SessionPool
   :members:
   :undoc-members:
   :show-inheritance:

Keys
----

PKCS11PrivateKeyMixin
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: hsmkey.keys.base.PKCS11PrivateKeyMixin
   :members:
   :undoc-members:
   :show-inheritance:

RSA Keys
^^^^^^^^

.. autoclass:: hsmkey.keys.rsa.PKCS11RSAPrivateKey
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hsmkey.keys.rsa.PKCS11RSAPublicKey
   :members:
   :undoc-members:
   :show-inheritance:

Elliptic Curve Keys
^^^^^^^^^^^^^^^^^^^

.. autoclass:: hsmkey.keys.ec.PKCS11EllipticCurvePrivateKey
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hsmkey.keys.ec.PKCS11EllipticCurvePublicKey
   :members:
   :undoc-members:
   :show-inheritance:

Ed25519 Keys
^^^^^^^^^^^^

.. autoclass:: hsmkey.keys.ed25519.PKCS11Ed25519PrivateKey
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hsmkey.keys.ed25519.PKCS11Ed25519PublicKey
   :members:
   :undoc-members:
   :show-inheritance:

Ed448 Keys
^^^^^^^^^^

.. autoclass:: hsmkey.keys.ed448.PKCS11Ed448PrivateKey
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hsmkey.keys.ed448.PKCS11Ed448PublicKey
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: hsmkey.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Module Contents
---------------

hsmkey
^^^^^^

.. automodule:: hsmkey
   :members:
   :undoc-members:
