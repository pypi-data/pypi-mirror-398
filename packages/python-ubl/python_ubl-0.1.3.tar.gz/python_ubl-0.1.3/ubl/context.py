"""
UBL Context Management

Provides context managers for controlling UBL behavior based on validation profiles.
"""

from contextvars import ContextVar
from contextlib import contextmanager
from typing import Literal

# Context variable for validation profile (thread-safe)
_validation_profile: ContextVar[str | None] = ContextVar('validation_profile', default=None)


@contextmanager
def peppol_context():
    """
    Context manager for PEPPOL BIS 3.0 compliance mode.

    When active, UBL elements apply PEPPOL-specific rules:
    - IBAN/BIC identifiers omit schemeID attribute (PEPPOL requirement)
    - Other PEPPOL-specific validations and formatting

    Usage:
        with peppol_context():
            xml = invoice_to_ubl(invoice)

    Example:
        >>> with peppol_context():
        ...     doc = Invoice(...)
        ...     xml = doc.to_xml_string()
        # <cbc:ID>BE123456789</cbc:ID>  (no schemeID for IBAN)
    """
    token = _validation_profile.set('peppol')
    try:
        yield
    finally:
        _validation_profile.reset(token)


@contextmanager
def validation_context(profile: Literal['peppol', 'standard'] = 'standard'):
    """
    Generic validation context manager.

    Args:
        profile: Validation profile to use ('peppol' or 'standard')

    Usage:
        with validation_context('peppol'):
            xml = invoice_to_ubl(invoice)
    """
    token = _validation_profile.set(profile)
    try:
        yield
    finally:
        _validation_profile.reset(token)


def get_validation_profile() -> str | None:
    """
    Get current validation profile.

    Returns:
        Current validation profile ('peppol', 'standard', or None)
    """
    return _validation_profile.get()


def is_peppol_mode() -> bool:
    """
    Check if PEPPOL validation mode is active.

    Returns:
        True if in PEPPOL context, False otherwise
    """
    return _validation_profile.get() == 'peppol'
