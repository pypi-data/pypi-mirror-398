"""Configuration management for hsmkey module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# Common HSM library paths
DEFAULT_SOFTHSM_PATHS = [
    "/usr/lib/softhsm/libsofthsm2.so",
    "/usr/lib64/softhsm/libsofthsm2.so",
    "/usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so",
    "/usr/local/lib/softhsm/libsofthsm2.so",
    "/opt/homebrew/lib/softhsm/libsofthsm2.so",  # macOS ARM
    "/usr/local/opt/softhsm/lib/softhsm/libsofthsm2.so",  # macOS Intel
]


@dataclass
class HSMConfig:
    """Configuration for HSM connection.

    Attributes:
        module_path: Path to PKCS#11 library
        token_label: Label of the token to use
        user_pin: User PIN for authentication
        so_pin: Security Officer PIN (optional, for admin operations)
    """

    module_path: str
    token_label: str
    user_pin: str | None = None
    so_pin: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not Path(self.module_path).exists():
            from .exceptions import HSMConfigError

            raise HSMConfigError(f"PKCS#11 module not found: {self.module_path}")

        if self.user_pin is None and self.so_pin is None:
            from .exceptions import HSMConfigError

            raise HSMConfigError("Either user_pin or so_pin must be provided")


def find_softhsm_module() -> str | None:
    """Find SoftHSM2 module path.

    Returns:
        Path to SoftHSM2 library if found, None otherwise.
    """
    for path in DEFAULT_SOFTHSM_PATHS:
        if Path(path).exists():
            return path
    return None


def get_softhsm_conf() -> str | None:
    """Get SoftHSM2 configuration file path.

    Returns:
        Path from SOFTHSM2_CONF environment variable or None.
    """
    return os.environ.get("SOFTHSM2_CONF")
