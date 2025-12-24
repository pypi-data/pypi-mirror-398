"""
Custom exceptions for the UBL library.

This module defines all custom exception classes used throughout the library.
"""


class UBLError(Exception):
    """Base exception for all UBL library errors."""


class ValidationError(UBLError):
    """
    Raised when data validation fails.

    This is raised during dataclass construction (__post_init__) or
    when validating business rules.
    """


class ParsingError(UBLError):
    """
    Raised when XML parsing fails.

    This includes errors in XML structure, missing required elements,
    or invalid element values.
    """


class SerializationError(UBLError):
    """
    Raised when XML generation fails.

    This includes errors in converting dataclasses to XML elements.
    """


class UnsupportedElementError(UBLError):
    """
    Raised when encountering an unsupported UBL element.

    This can occur during parsing when the XML contains elements
    not yet supported by this library.
    """
