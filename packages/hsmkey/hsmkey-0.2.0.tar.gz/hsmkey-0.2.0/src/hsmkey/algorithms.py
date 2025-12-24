"""Algorithm mappings between cryptography library and PKCS#11."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from pkcs11 import MGF, KDF, Mechanism

if TYPE_CHECKING:
    pass


# Hash algorithm to PKCS#11 mechanism mapping
HASH_MECHANISMS: dict[type[hashes.HashAlgorithm], Mechanism] = {
    hashes.SHA224: Mechanism.SHA224,
    hashes.SHA256: Mechanism.SHA256,
    hashes.SHA384: Mechanism.SHA384,
    hashes.SHA512: Mechanism.SHA512,
}

# Hash algorithm to MGF mapping for RSA-OAEP and PSS
HASH_TO_MGF: dict[type[hashes.HashAlgorithm], MGF] = {
    hashes.SHA1: MGF.SHA1,
    hashes.SHA224: MGF.SHA224,
    hashes.SHA256: MGF.SHA256,
    hashes.SHA384: MGF.SHA384,
    hashes.SHA512: MGF.SHA512,
}

# RSA PKCS#1 v1.5 signing mechanisms
RSA_PKCS1_SIGN_MECHANISMS: dict[type[hashes.HashAlgorithm], Mechanism] = {
    hashes.SHA224: Mechanism.SHA224_RSA_PKCS,
    hashes.SHA256: Mechanism.SHA256_RSA_PKCS,
    hashes.SHA384: Mechanism.SHA384_RSA_PKCS,
    hashes.SHA512: Mechanism.SHA512_RSA_PKCS,
}

# RSA PSS signing mechanisms
RSA_PSS_SIGN_MECHANISMS: dict[type[hashes.HashAlgorithm], Mechanism] = {
    hashes.SHA224: Mechanism.SHA224_RSA_PKCS_PSS,
    hashes.SHA256: Mechanism.SHA256_RSA_PKCS_PSS,
    hashes.SHA384: Mechanism.SHA384_RSA_PKCS_PSS,
    hashes.SHA512: Mechanism.SHA512_RSA_PKCS_PSS,
}

# Hash algorithm digest sizes
HASH_DIGEST_SIZES: dict[type[hashes.HashAlgorithm], int] = {
    hashes.SHA1: 20,
    hashes.SHA224: 28,
    hashes.SHA256: 32,
    hashes.SHA384: 48,
    hashes.SHA512: 64,
}


def get_rsa_sign_mechanism(
    padding_instance: padding.AsymmetricPadding,
    algorithm: hashes.HashAlgorithm,
) -> tuple[Mechanism, Any]:
    """Get PKCS#11 mechanism for RSA signing.

    Args:
        padding_instance: RSA padding (PKCS1v15 or PSS)
        algorithm: Hash algorithm

    Returns:
        Tuple of (mechanism, mechanism_param)

    Raises:
        ValueError: If unsupported padding or algorithm
    """
    alg_type = type(algorithm)

    if isinstance(padding_instance, padding.PKCS1v15):
        if alg_type not in RSA_PKCS1_SIGN_MECHANISMS:
            raise ValueError(f"Unsupported hash algorithm: {algorithm.name}")
        return RSA_PKCS1_SIGN_MECHANISMS[alg_type], None

    elif isinstance(padding_instance, padding.PSS):
        if alg_type not in RSA_PSS_SIGN_MECHANISMS:
            raise ValueError(f"Unsupported hash algorithm for PSS: {algorithm.name}")

        mechanism = RSA_PSS_SIGN_MECHANISMS[alg_type]

        # Get MGF algorithm
        if isinstance(padding_instance._mgf, padding.MGF1):
            mgf_alg_type = type(padding_instance._mgf._algorithm)
            if mgf_alg_type not in HASH_TO_MGF:
                raise ValueError(
                    f"Unsupported MGF hash: {padding_instance._mgf._algorithm.name}"
                )
            mgf = HASH_TO_MGF[mgf_alg_type]
        else:
            raise ValueError("Only MGF1 is supported for PSS")

        # Get salt length
        salt_length = padding_instance._salt_length
        if salt_length == padding.PSS.AUTO:
            # Use hash digest size as default
            salt_length = HASH_DIGEST_SIZES.get(alg_type, 32)
        elif salt_length == padding.PSS.MAX_LENGTH:
            # Will be computed based on key size during signing
            # For now use digest size as approximation
            salt_length = HASH_DIGEST_SIZES.get(alg_type, 32)
        elif salt_length == padding.PSS.DIGEST_LENGTH:
            salt_length = HASH_DIGEST_SIZES.get(alg_type, 32)

        # PSS parameters: (hash_alg, mgf, salt_length)
        return mechanism, (HASH_MECHANISMS[alg_type], mgf, salt_length)

    else:
        raise ValueError(f"Unsupported padding: {type(padding_instance)}")


def get_rsa_encrypt_mechanism(
    padding_instance: padding.AsymmetricPadding,
) -> tuple[Mechanism, Any]:
    """Get PKCS#11 mechanism for RSA encryption.

    Args:
        padding_instance: RSA padding (PKCS1v15 or OAEP)

    Returns:
        Tuple of (mechanism, mechanism_param)

    Raises:
        ValueError: If unsupported padding
    """
    if isinstance(padding_instance, padding.PKCS1v15):
        return Mechanism.RSA_PKCS, None

    elif isinstance(padding_instance, padding.OAEP):
        # Get hash algorithm
        hash_alg = padding_instance._algorithm
        hash_alg_type = type(hash_alg)

        # Get MGF algorithm
        if isinstance(padding_instance._mgf, padding.MGF1):
            mgf_alg_type = type(padding_instance._mgf._algorithm)
        else:
            raise ValueError("Only MGF1 is supported for OAEP")

        # For SHA-1 with SHA-1 MGF and no label (the PKCS#11 default),
        # don't pass mechanism params as some HSMs (like SoftHSM2) don't
        # accept explicit params that match the defaults.
        label = padding_instance._label or b""
        if (
            hash_alg_type == hashes.SHA1
            and mgf_alg_type == hashes.SHA1
            and not label
        ):
            return Mechanism.RSA_PKCS_OAEP, None

        # For non-default params, validate and pass them
        if hash_alg_type not in HASH_MECHANISMS:
            raise ValueError(f"Unsupported OAEP hash: {hash_alg.name}")

        if mgf_alg_type not in HASH_TO_MGF:
            raise ValueError(
                f"Unsupported MGF hash: {padding_instance._mgf._algorithm.name}"
            )
        mgf = HASH_TO_MGF[mgf_alg_type]

        # OAEP parameters
        # Note: python-pkcs11 expects (hash_mechanism, mgf, label)
        return Mechanism.RSA_PKCS_OAEP, (
            HASH_MECHANISMS[hash_alg_type],
            mgf,
            label,
        )

    else:
        raise ValueError(f"Unsupported encryption padding: {type(padding_instance)}")


# Elliptic curve OID mappings
EC_CURVE_OIDS: dict[str, bytes] = {
    # NIST curves
    "secp256r1": bytes.fromhex("06082a8648ce3d030107"),
    "secp384r1": bytes.fromhex("06052b81040022"),
    "secp521r1": bytes.fromhex("06052b81040023"),
    # Brainpool curves
    "brainpoolP256r1": bytes.fromhex("06092b2403030208010107"),
    "brainpoolP320r1": bytes.fromhex("06092b2403030208010109"),
    "brainpoolP384r1": bytes.fromhex("06092b240303020801010b"),
    "brainpoolP512r1": bytes.fromhex("06092b240303020801010d"),
    # Bitcoin curve
    "secp256k1": bytes.fromhex("06052b8104000a"),
}

# Reverse mapping: OID bytes to curve name
OID_TO_CURVE: dict[bytes, str] = {v: k for k, v in EC_CURVE_OIDS.items()}

# EdDSA curve OIDs
EDDSA_CURVE_OIDS: dict[str, bytes] = {
    "Ed25519": bytes.fromhex("06032b6570"),  # 1.3.101.112
    "Ed448": bytes.fromhex("06032b6571"),  # 1.3.101.113
}

# Curve name aliases
CURVE_ALIASES: dict[str, str] = {
    "prime256v1": "secp256r1",
    "P-256": "secp256r1",
    "P-384": "secp384r1",
    "P-521": "secp521r1",
}


def normalize_curve_name(name: str) -> str:
    """Normalize curve name to standard form.

    Args:
        name: Curve name (may be alias)

    Returns:
        Normalized curve name
    """
    return CURVE_ALIASES.get(name, name)
