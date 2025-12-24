Session Management
==================

hsmkey provides session management utilities for PKCS#11 operations.
This guide covers the SessionPool class and best practices.

SessionPool Class
-----------------

The ``SessionPool`` class manages PKCS#11 library instances and sessions.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

    from hsmkey import SessionPool

    pool = SessionPool(
        module_path="/usr/lib/softhsm/libsofthsm2.so",
        token_label="my-token",
        user_pin="12345678"
    )

    # Use context manager for automatic session cleanup
    with pool.session() as session:
        # Work with session
        pass

    # Session is automatically closed

hsm_session Context Manager
---------------------------

For simple use cases, use the ``hsm_session`` context manager:

.. code-block:: python

    from hsmkey import hsm_session

    with hsm_session(module_path, token_label, pin) as session:
        # Work with session
        key = HSMJWK.from_hsm(session, key_label="my-key")

Session Lifecycle
-----------------

Opening Sessions
^^^^^^^^^^^^^^^^

Sessions are opened when you enter the context manager:

.. code-block:: python

    with pool.session() as session:
        # Session is now open and logged in
        pass
    # Session is closed and logged out

Read-Write Sessions
^^^^^^^^^^^^^^^^^^^

By default, sessions are read-only. For operations that modify the token,
use a read-write session:

.. code-block:: python

    with pool.session(rw=True) as session:
        # Can perform write operations
        pass

Best Practices
--------------

1. Keep Sessions Short
^^^^^^^^^^^^^^^^^^^^^^

Open sessions only when needed and close them promptly:

.. code-block:: python

    # Good: Short session
    def sign_data(data):
        with pool.session() as session:
            key = HSMJWK.from_hsm(session, key_label="my-key")
            jws = JWS(data)
            jws.add_signature(key, alg="RS256", protected=...)
            return jws.serialize(compact=True)

    # Bad: Long-lived session
    session = pool.open_session()  # Don't keep open
    # ... later ...
    session.close()

2. Cache Keys Within Sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Load keys once and reuse them within a session:

.. code-block:: python

    with pool.session() as session:
        # Load key once
        key = HSMJWK.from_hsm(session, key_label="my-key")

        # Reuse for multiple operations
        for data in items:
            jws = JWS(data)
            jws.add_signature(key, alg="RS256", protected=...)

3. Batch Operations
^^^^^^^^^^^^^^^^^^^

Keep related operations in the same session:

.. code-block:: python

    # Efficient: Single session for batch
    with pool.session() as session:
        key = HSMJWK.from_hsm(session, key_label="my-key")
        tokens = []
        for i in range(100):
            jws = JWS(f'{{"id": {i}}}'.encode())
            jws.add_signature(key, alg="RS256", protected=...)
            tokens.append(jws.serialize(compact=True))

    # Inefficient: New session for each operation
    tokens = []
    for i in range(100):
        with pool.session() as session:  # Unnecessary overhead
            key = HSMJWK.from_hsm(session, key_label="my-key")
            jws = JWS(f'{{"id": {i}}}'.encode())
            jws.add_signature(key, alg="RS256", protected=...)
            tokens.append(jws.serialize(compact=True))

4. Error Handling
^^^^^^^^^^^^^^^^^

Handle session errors gracefully:

.. code-block:: python

    from hsmkey.exceptions import HSMSessionError, HSMPinError

    try:
        with pool.session() as session:
            key = HSMJWK.from_hsm(session, key_label="my-key")
    except HSMPinError:
        print("Invalid PIN")
    except HSMSessionError as e:
        print(f"Session error: {e}")

PKCS#11 Considerations
----------------------

Session Limits
^^^^^^^^^^^^^^

Most PKCS#11 tokens have limits on concurrent sessions. Avoid opening
too many sessions simultaneously:

.. code-block:: python

    # Be careful with concurrent access
    # PKCS#11 tokens may not support multiple simultaneous logins

Login State
^^^^^^^^^^^

When a session is opened with a PIN, the user is logged in. Some tokens
only allow one login at a time per token:

.. code-block:: python

    # This may fail with "UserAlreadyLoggedIn" on some tokens
    with pool.session() as session1:
        with pool.session() as session2:  # May fail
            pass

For concurrent operations, use a single session with proper synchronization.

Module Caching
^^^^^^^^^^^^^^

The ``SessionPool`` caches PKCS#11 library instances by module path.
This is efficient when using multiple pools with the same module:

.. code-block:: python

    pool1 = SessionPool(module_path, "token1", "pin1")
    pool2 = SessionPool(module_path, "token2", "pin2")
    # Both pools share the same library instance

Environment Variables
---------------------

Common environment variables for HSM configuration:

.. code-block:: bash

    # SoftHSM2 configuration path
    export SOFTHSM2_CONF="$HOME/.config/softhsm/softhsm2.conf"

    # Custom module path
    export HSM_MODULE="/path/to/libpkcs11.so"

    # Token settings
    export HSM_TOKEN="my-token"
    export HSM_PIN="12345678"

Then in Python:

.. code-block:: python

    import os

    pool = SessionPool(
        module_path=os.environ.get("HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so"),
        token_label=os.environ.get("HSM_TOKEN", "default-token"),
        user_pin=os.environ.get("HSM_PIN")
    )
