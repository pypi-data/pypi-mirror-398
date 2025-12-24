"""Custom exceptions for hsmkey module."""

from __future__ import annotations


class HSMError(Exception):
    """Base exception for all HSM-related errors."""

    pass


class HSMSessionError(HSMError):
    """Error related to HSM session management."""

    pass


class HSMKeyNotFoundError(HSMError):
    """Requested key was not found in the HSM."""

    pass


class HSMPinError(HSMError):
    """PIN authentication failed."""

    pass


class HSMOperationError(HSMError):
    """Cryptographic operation failed on HSM."""

    pass


class HSMUnsupportedError(HSMError):
    """Operation is not supported for HSM-backed keys."""

    pass


class HSMConfigError(HSMError):
    """Configuration error for HSM."""

    pass
