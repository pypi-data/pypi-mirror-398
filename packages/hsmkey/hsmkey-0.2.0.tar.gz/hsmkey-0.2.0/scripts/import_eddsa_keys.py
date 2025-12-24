#!/usr/bin/env python3
"""Import EdDSA keys (Ed25519, Ed448) to SoftHSM2.

pkcs11-tool doesn't handle EdDSA key import well, so we use python-pkcs11.
"""

from __future__ import annotations

import os
from pathlib import Path

import pkcs11
from pkcs11 import Attribute, KeyType, Mechanism, ObjectClass
from cryptography.hazmat.primitives import serialization


# Configuration
HSM_MODULE = os.environ.get("HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so")
TOKEN_LABEL = os.environ.get("HSM_TOKEN_LABEL", "hsmkey-test")
PIN = os.environ.get("HSM_PIN", "12345678")

# Key directory
KEY_DIR = Path(__file__).parent.parent / "tests" / "data" / "privatekeys"

# Ed25519 OID: 1.3.101.112
ED25519_OID = bytes.fromhex("06032b6570")

# Ed448 OID: 1.3.101.113
ED448_OID = bytes.fromhex("06032b6571")


def load_ed25519_key(path: Path) -> tuple[bytes, bytes]:
    """Load Ed25519 key and return (private_bytes, public_bytes)."""
    with open(path, "rb") as f:
        pem_data = f.read()

    from cryptography.hazmat.primitives.asymmetric import ed25519

    private_key = serialization.load_pem_private_key(pem_data, password=None)
    assert isinstance(private_key, ed25519.Ed25519PrivateKey)

    # Get raw private and public key bytes
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()

    return private_bytes, public_bytes


def load_ed448_key(path: Path) -> tuple[bytes, bytes]:
    """Load Ed448 key and return (private_bytes, public_bytes)."""
    with open(path, "rb") as f:
        pem_data = f.read()

    from cryptography.hazmat.primitives.asymmetric import ed448

    private_key = serialization.load_pem_private_key(pem_data, password=None)
    assert isinstance(private_key, ed448.Ed448PrivateKey)

    # Get raw private and public key bytes
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()

    return private_bytes, public_bytes


def import_edwards_keypair(
    session: pkcs11.Session,
    private_bytes: bytes,
    public_bytes: bytes,
    ec_params: bytes,
    key_id: bytes,
    label: str,
) -> None:
    """Import an Edwards curve key pair to the HSM."""
    # Check if key already exists
    try:
        existing = session.get_key(
            key_type=KeyType.EC_EDWARDS,
            object_class=ObjectClass.PRIVATE_KEY,
            label=label,
        )
        print(f"  Key '{label}' already exists, skipping...")
        return
    except pkcs11.NoSuchKey:
        pass

    # Wrap public key in OCTET STRING for EC_POINT
    # Format: 04 <length> <public_key_bytes>
    if len(public_bytes) < 128:
        ec_point = bytes([0x04, len(public_bytes)]) + public_bytes
    else:
        # Length > 127, use long form
        ec_point = bytes([0x04, 0x81, len(public_bytes)]) + public_bytes

    # Create private key object
    private_template = {
        Attribute.CLASS: ObjectClass.PRIVATE_KEY,
        Attribute.KEY_TYPE: KeyType.EC_EDWARDS,
        Attribute.TOKEN: True,
        Attribute.PRIVATE: True,
        Attribute.SENSITIVE: True,
        Attribute.SIGN: True,
        Attribute.EXTRACTABLE: False,
        Attribute.ID: key_id,
        Attribute.LABEL: label,
        Attribute.EC_PARAMS: ec_params,
        Attribute.VALUE: private_bytes,
    }

    # Create public key object
    public_template = {
        Attribute.CLASS: ObjectClass.PUBLIC_KEY,
        Attribute.KEY_TYPE: KeyType.EC_EDWARDS,
        Attribute.TOKEN: True,
        Attribute.PRIVATE: False,
        Attribute.VERIFY: True,
        Attribute.ID: key_id,
        Attribute.LABEL: label,
        Attribute.EC_PARAMS: ec_params,
        Attribute.EC_POINT: ec_point,
    }

    session.create_object(private_template)
    session.create_object(public_template)
    print(f"  Imported '{label}' successfully")


def main() -> None:
    """Import EdDSA keys to SoftHSM2."""
    print(f"Loading PKCS#11 library: {HSM_MODULE}")
    lib = pkcs11.lib(HSM_MODULE)

    print(f"Opening token: {TOKEN_LABEL}")
    token = lib.get_token(token_label=TOKEN_LABEL)

    with token.open(rw=True, user_pin=PIN) as session:
        # Import Ed25519
        ed25519_path = KEY_DIR / "ed25519.pem"
        if ed25519_path.exists():
            print("Importing Ed25519 key...")
            private_bytes, public_bytes = load_ed25519_key(ed25519_path)
            import_edwards_keypair(
                session,
                private_bytes,
                public_bytes,
                ED25519_OID,
                key_id=bytes([0x08]),
                label="ed25519",
            )
        else:
            print(f"Ed25519 key not found at {ed25519_path}")

        # Import Ed448
        ed448_path = KEY_DIR / "ed448.pem"
        if ed448_path.exists():
            print("Importing Ed448 key...")
            private_bytes, public_bytes = load_ed448_key(ed448_path)
            import_edwards_keypair(
                session,
                private_bytes,
                public_bytes,
                ED448_OID,
                key_id=bytes([0x09]),
                label="ed448",
            )
        else:
            print(f"Ed448 key not found at {ed448_path}")

    print("EdDSA key import complete")


if __name__ == "__main__":
    main()
