Development Guide
=================

This guide covers setting up a development environment for hsmkey, running tests,
and understanding the test infrastructure.

Prerequisites
-------------

Before starting development, ensure you have the following installed:

- Python 3.10 or later
- `uv <https://docs.astral.sh/uv/>`_ - Fast Python package manager
- `just <https://github.com/casey/just>`_ - Command runner
- OpenSSL - For generating test keys
- One of the following HSM backends:
  - SoftHSM2 (recommended for development)
  - Kryoptic (Rust-based PKCS#11 token)

Installing Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^

**Ubuntu/Debian:**

.. code-block:: bash

    # Install system packages
    sudo apt-get update
    sudo apt-get install -y softhsm2 opensc openssl

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Install just
    cargo install just
    # Or use the package manager
    sudo apt-get install -y just

**Fedora/RHEL:**

.. code-block:: bash

    sudo dnf install softhsm opensc openssl
    curl -LsSf https://astral.sh/uv/install.sh | sh
    cargo install just

**macOS:**

.. code-block:: bash

    brew install softhsm openssl just
    curl -LsSf https://astral.sh/uv/install.sh | sh

Setting Up the Development Environment
--------------------------------------

1. Clone the Repository
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    git clone https://github.com/kushaldas/hsmkey
    cd hsmkey

2. Create Virtual Environment and Install Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using ``uv``, create a virtual environment and install all dependencies:

.. code-block:: bash

    # Sync all dependencies including dev extras
    uv sync --extra dev

This installs:

- Core dependencies (``cryptography``, ``python-pkcs11``)
- JWCrypto integration (``jwcrypto``)
- Development tools (``pytest``, ``pytest-cov``, ``ruff``, ``ty``)

3. Configure SoftHSM2
^^^^^^^^^^^^^^^^^^^^^

Create the SoftHSM2 configuration:

.. code-block:: bash

    # Create configuration directory
    mkdir -p ~/.config/softhsm
    mkdir -p ~/.local/share/softhsm/tokens

    # Create configuration file
    cat > ~/.config/softhsm/softhsm2.conf << EOF
    directories.tokendir = $HOME/.local/share/softhsm/tokens
    objectstore.backend = file
    log.level = INFO
    slots.removable = false
    EOF

    # Set environment variable (add to ~/.bashrc for persistence)
    export SOFTHSM2_CONF="$HOME/.config/softhsm/softhsm2.conf"

4. Generate Test Keys and Initialize HSM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the provided justfile commands:

.. code-block:: bash

    # Full setup: generate keys and import to HSM
    just setup

This runs:

- ``just recreate-keys`` - Generates RSA, EC, and EdDSA test keys
- ``just import-keys`` - Imports keys to SoftHSM2

Running Tests
-------------

Basic Test Commands
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Run all tests
    just test

    # Run tests with verbose output
    uv run pytest tests/ -v

    # Run specific test file
    uv run pytest tests/test_rsa.py -v

    # Run specific test class
    uv run pytest tests/test_jws_hsm.py::TestJWSRSASigning -v

    # Run specific test
    uv run pytest tests/test_jws_hsm.py::TestJWSRSASigning::test_rs256_sign -v

Test Coverage
^^^^^^^^^^^^^

.. code-block:: bash

    # Run tests with coverage report
    just test-cov

    # Or directly with pytest
    uv run pytest tests/ -v --cov=src/hsmkey --cov-report=term-missing

    # Generate HTML coverage report
    uv run pytest tests/ --cov=src/hsmkey --cov-report=html
    # Open htmlcov/index.html in browser

Test Structure
--------------

The test suite is organized as follows:

.. code-block:: text

    tests/
    ├── conftest.py          # Pytest fixtures and configuration
    ├── test_rsa.py          # RSA key tests
    ├── test_ec.py           # Elliptic curve key tests
    ├── test_ed25519.py      # Ed25519 key tests
    ├── test_ed448.py        # Ed448 key tests
    ├── test_jws_hsm.py      # JWS signing/verification tests
    ├── test_jwe_hsm.py      # JWE encryption/decryption tests
    ├── test_jwt_hsm.py      # JWT token tests
    └── test_integration.py  # Integration and interoperability tests

Test Fixtures
^^^^^^^^^^^^^

The ``conftest.py`` file provides shared fixtures:

.. code-block:: python

    # HSM session fixture - provides authenticated session
    def test_example(hsm_session):
        key = HSMJWK.from_hsm(hsm_session, key_label="rsa-2048")
        # ... use key

    # Session pool fixture - for connection management tests
    def test_pool(session_pool):
        with session_pool.session() as session:
            # ... use session

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

Tests can be configured via environment variables:

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Description
     - Default
   * - ``HSM_MODULE``
     - Path to PKCS#11 library
     - ``/usr/lib/softhsm/libsofthsm2.so``
   * - ``HSM_TOKEN_LABEL``
     - Token label
     - ``hsmkey-test``
   * - ``HSM_PIN``
     - User PIN
     - ``12345678``
   * - ``EDDSA_AVAILABLE``
     - Whether EdDSA keys are available
     - ``true``

Test Markers
^^^^^^^^^^^^

Custom pytest markers are used to conditionally skip tests:

.. code-block:: python

    @pytest.mark.requires_eddsa
    def test_ed25519_signing(hsm_session):
        """This test is skipped when EDDSA_AVAILABLE=false."""
        key = HSMJWK.from_hsm(hsm_session, key_label="ed25519")
        # ...

The ``requires_eddsa`` marker automatically skips tests when ``EDDSA_AVAILABLE=false``,
which is useful for testing with HSM backends that don't support EdDSA.

Testing with Kryoptic
---------------------

`Kryoptic <https://github.com/latchset/kryoptic>`_ is an alternative Rust-based
PKCS#11 software token. It requires additional setup.

Building Kryoptic
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Clone Kryoptic
    cd ~
    git clone https://github.com/latchset/kryoptic.git
    cd kryoptic

    # Check your OpenSSL version
    openssl version

**For systems with OpenSSL 3.2+ (Fedora 40+, etc.):**

.. code-block:: bash

    # Build with full EdDSA support
    cargo build --release --no-default-features \
        --features "sqlitedb,aes,ecdsa,ecdh,eddsa,ffdh,hash,hmac,hkdf,pbkdf2,rsa,sp800_108,dynamic"

With EdDSA support enabled, you can run the full test suite without skipping EdDSA tests.

**For systems with OpenSSL < 3.2 (Ubuntu 24.04, Ubuntu 22.04, RHEL 9, etc.):**

.. code-block:: bash

    # Build without EdDSA
    cargo build --release --no-default-features \
        --features "sqlitedb,aes,ecdsa,ecdh,ffdh,hash,hmac,hkdf,pbkdf2,rsa,sp800_108,dynamic"

Note: Ubuntu 24.04 ships with OpenSSL 3.0.x, which does not support EdDSA in Kryoptic.

Setting Up Kryoptic
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Create configuration
    just ensure-kryoptic-config

    # Initialize token and import keys
    just setup-kryoptic

Running Tests with Kryoptic
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**If you built Kryoptic with EdDSA support (OpenSSL 3.2+):**

.. code-block:: bash

    # Setup Kryoptic with RSA/EC keys
    just setup-kryoptic

    # Import EdDSA keys
    just import-eddsa-kryoptic

    # Run full test suite
    just test-kryoptic-full

**If you built Kryoptic without EdDSA support:**

.. code-block:: bash

    # Run tests against Kryoptic (skips EdDSA tests)
    just test-kryoptic

The ``just test-kryoptic`` command automatically:

- Sets ``HSM_MODULE`` to the Kryoptic library path
- Sets ``EDDSA_AVAILABLE=false`` to skip EdDSA tests
- Ignores standalone EdDSA test files

Kryoptic and EdDSA Support
^^^^^^^^^^^^^^^^^^^^^^^^^^

EdDSA (Ed25519/Ed448) support in Kryoptic depends on your OpenSSL version:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Distribution
     - OpenSSL Version
     - EdDSA Support
   * - Fedora 40+
     - 3.2+
     - Full support
   * - Ubuntu 24.04
     - 3.0.13
     - Not supported
   * - Ubuntu 22.04
     - 3.0.x
     - Not supported
   * - RHEL 9 / Rocky 9
     - 3.0.x
     - Not supported

To check your OpenSSL version:

.. code-block:: bash

    openssl version

If you have OpenSSL 3.2+, rebuild Kryoptic with the ``eddsa`` feature to enable
full EdDSA support.

Available Justfile Commands
---------------------------

Run ``just`` to see all available commands:

.. code-block:: bash

    just                    # List all commands

**Key Management:**

.. code-block:: bash

    just recreate-keys      # Generate test keys on disk
    just init-hsm           # Initialize SoftHSM2 token
    just import-keys        # Import keys to SoftHSM2
    just list-keys          # List keys in HSM
    just delete-hsm         # Delete the test token
    just setup              # Full setup (recreate-keys + import-keys)
    just reset              # Delete token and reimport keys

**Testing:**

.. code-block:: bash

    just test               # Run all tests
    just test-cov           # Run tests with coverage
    just lint               # Run type checker

**Kryoptic:**

.. code-block:: bash

    just ensure-kryoptic-config   # Create Kryoptic config
    just init-kryoptic            # Initialize Kryoptic token
    just import-keys-kryoptic     # Import RSA/EC keys to Kryoptic
    just import-eddsa-kryoptic    # Import EdDSA keys (requires OpenSSL 3.2+)
    just list-keys-kryoptic       # List keys in Kryoptic
    just setup-kryoptic           # Full Kryoptic setup (without EdDSA)
    just test-kryoptic            # Run tests without EdDSA
    just test-kryoptic-full       # Run full tests with EdDSA (OpenSSL 3.2+)
    just clean-kryoptic           # Clean Kryoptic storage

**Documentation:**

.. code-block:: bash

    just docs               # Build Sphinx documentation
    just docs-serve         # Build and serve docs locally

**Cleanup:**

.. code-block:: bash

    just clean              # Clean generated files

Code Style and Linting
----------------------

Type Checking
^^^^^^^^^^^^^

.. code-block:: bash

    # Run type checker
    just lint

    # Or directly
    uv run ty check src/

Note: The ``python-pkcs11`` library lacks type stubs, so some type errors are expected.

Code Formatting
^^^^^^^^^^^^^^^

The project uses ``ruff`` for linting and formatting:

.. code-block:: bash

    # Check formatting
    uv run ruff check src/ tests/

    # Auto-fix issues
    uv run ruff check --fix src/ tests/

    # Format code
    uv run ruff format src/ tests/

Building Documentation
----------------------

The documentation uses Sphinx with the Read the Docs theme:

.. code-block:: bash

    # Install docs dependencies
    uv sync --extra docs

    # Build HTML documentation
    just docs

    # Or manually
    cd docs && uv run make html

    # View locally
    open docs/_build/html/index.html

Building the Package
--------------------

To build the package for distribution:

.. code-block:: bash

    # Build wheel and sdist
    uv build

    # Output in dist/
    ls dist/

Continuous Integration
----------------------

The project uses GitHub Actions for CI. The workflow:

1. **Lint** - Runs type checking
2. **Test with SoftHSM2** - Full test suite with SoftHSM2
3. **Test with Kryoptic** - Test suite with Kryoptic (EdDSA tests skipped)
4. **Build** - Builds the package

CI Configuration
^^^^^^^^^^^^^^^^

The CI automatically handles:

- Installing SoftHSM2 or building Kryoptic
- Setting up HSM tokens
- Importing test keys
- Running tests with appropriate environment variables

For Kryoptic tests, ``EDDSA_AVAILABLE=false`` is set to skip EdDSA tests.

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**"HSM module not found"**

.. code-block:: bash

    # Check SoftHSM2 installation
    ls -la /usr/lib/softhsm/libsofthsm2.so
    # or
    ls -la /usr/lib64/softhsm/libsofthsm2.so

    # Set correct path
    export HSM_MODULE="/path/to/libsofthsm2.so"

**"Token not found"**

.. code-block:: bash

    # Ensure SOFTHSM2_CONF is set
    export SOFTHSM2_CONF="$HOME/.config/softhsm/softhsm2.conf"

    # List available tokens
    softhsm2-util --show-slots

    # Reinitialize if needed
    just reset

**"Key not found"**

.. code-block:: bash

    # List keys in token
    just list-keys

    # Reimport keys
    just import-keys

**"EdDSA tests failing with Kryoptic"**

EdDSA (Ed25519/Ed448) requires OpenSSL 3.2+ with Kryoptic. On older systems:

.. code-block:: bash

    # Run with EdDSA tests skipped
    EDDSA_AVAILABLE=false just test-kryoptic

Contributing
------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: ``just test``
5. Run linter: ``just lint``
6. Submit a pull request

Ensure all tests pass and code follows the project style before submitting.
