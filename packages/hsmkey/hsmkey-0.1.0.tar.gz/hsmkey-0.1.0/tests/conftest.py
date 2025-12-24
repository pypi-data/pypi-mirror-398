"""Pytest fixtures for hsmkey tests."""

from __future__ import annotations

import os
from typing import Iterator

import pytest

from hsmkey import SessionPool

# HSM Configuration from environment or defaults
HSM_MODULE = os.environ.get("HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so")
HSM_TOKEN_LABEL = os.environ.get("HSM_TOKEN_LABEL", "hsmkey-test")
HSM_PIN = os.environ.get("HSM_PIN", "12345678")

# Key labels matching justfile import
RSA_2048_LABEL = "rsa-2048"
RSA_3072_LABEL = "rsa-3072"
RSA_4096_LABEL = "rsa-4096"

EC_P256_LABEL = "ec-p256"
EC_P384_LABEL = "ec-p384"
EC_P521_LABEL = "ec-p521"

ED25519_LABEL = "ed25519"
ED448_LABEL = "ed448"


@pytest.fixture(scope="session")
def hsm_module() -> str:
    """Return path to HSM PKCS#11 module."""
    if not os.path.exists(HSM_MODULE):
        pytest.skip(f"HSM module not found: {HSM_MODULE}")
    return HSM_MODULE


@pytest.fixture(scope="session")
def hsm_token_label() -> str:
    """Return HSM token label."""
    return HSM_TOKEN_LABEL


@pytest.fixture(scope="session")
def hsm_pin() -> str:
    """Return HSM PIN."""
    return HSM_PIN


@pytest.fixture(scope="session")
def session_pool(hsm_module: str, hsm_token_label: str, hsm_pin: str) -> SessionPool:
    """Create session pool for tests."""
    return SessionPool(
        module_path=hsm_module,
        token_label=hsm_token_label,
        user_pin=hsm_pin,
    )


@pytest.fixture
def hsm_session(session_pool: SessionPool) -> Iterator:
    """Provide HSM session for tests."""
    with session_pool.session() as session:
        yield session


# Key ID fixtures
@pytest.fixture
def rsa_2048_key_id() -> bytes:
    """RSA 2048 key ID."""
    return bytes([0x10])


@pytest.fixture
def rsa_3072_key_id() -> bytes:
    """RSA 3072 key ID."""
    return bytes([0x11])


@pytest.fixture
def rsa_4096_key_id() -> bytes:
    """RSA 4096 key ID."""
    return bytes([0x12])


@pytest.fixture
def ec_p256_key_id() -> bytes:
    """EC P-256 key ID."""
    return bytes([0x01])


@pytest.fixture
def ec_p384_key_id() -> bytes:
    """EC P-384 key ID."""
    return bytes([0x02])


@pytest.fixture
def ec_p521_key_id() -> bytes:
    """EC P-521 key ID."""
    return bytes([0x03])


@pytest.fixture
def ed25519_key_id() -> bytes:
    """Ed25519 key ID."""
    return bytes([0x08])


@pytest.fixture
def ed448_key_id() -> bytes:
    """Ed448 key ID."""
    return bytes([0x09])
