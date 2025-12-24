Installation
============

Requirements
------------

- Python 3.10 or later
- A PKCS#11-compatible HSM or software token (SoftHSM2 recommended for development)

Installing hsmkey
-----------------

Install from PyPI:

.. code-block:: bash

    python3 -m pip install hsmkey

For JWCrypto integration (JWS, JWE, JWT support), install with the optional dependency:

.. code-block:: bash

    python3 -m pip install hsmkey[jwcrypto]

For development:

.. code-block:: bash

    python3 -m pip install hsmkey[dev]

Setting up SoftHSM2
-------------------

SoftHSM2 is a software-based HSM useful for development and testing.

Ubuntu/Debian
^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt-get install softhsm2 opensc

Fedora/RHEL
^^^^^^^^^^^

.. code-block:: bash

    sudo dnf install softhsm opensc

macOS
^^^^^

.. code-block:: bash

    brew install softhsm

Configuring SoftHSM2
--------------------

Create a configuration file:

.. code-block:: bash

    mkdir -p ~/.config/softhsm
    mkdir -p ~/.local/share/softhsm/tokens

    cat > ~/.config/softhsm/softhsm2.conf << EOF
    directories.tokendir = $HOME/.local/share/softhsm/tokens
    objectstore.backend = file
    log.level = INFO
    slots.removable = false
    EOF

Set the configuration path:

.. code-block:: bash

    export SOFTHSM2_CONF="$HOME/.config/softhsm/softhsm2.conf"

Initialize a token:

.. code-block:: bash

    softhsm2-util --init-token --free --label "my-token" --so-pin 12345678 --pin 12345678

Generating Test Keys
--------------------

Generate an RSA key pair:

.. code-block:: bash

    # Generate private key
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out rsa-key.pem

    # Extract public key
    openssl pkey -in rsa-key.pem -pubout -out rsa-key-pub.pem

Import to HSM:

.. code-block:: bash

    pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
        --token-label "my-token" --login --pin 12345678 \
        --write-object rsa-key.pem --type privkey \
        --label "my-rsa-key" --id 01

    pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
        --token-label "my-token" --login --pin 12345678 \
        --write-object rsa-key-pub.pem --type pubkey \
        --label "my-rsa-key" --id 01

Verify the key was imported:

.. code-block:: bash

    pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
        --token-label "my-token" --login --pin 12345678 -O

Using Kryoptic (Alternative)
----------------------------

Kryoptic is a Rust-based PKCS#11 software token with additional features.

See the `Kryoptic documentation <https://github.com/latchset/kryoptic>`_ for installation instructions.
