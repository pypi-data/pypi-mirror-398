"""
PEPPOL Identifier System for UBL Party Identification.

This module provides automatic generation of party identifiers from
country, VAT, and registration data using PEPPOL v9.4 schemes.

Key components:
- schemes_codes: PEPPOL scheme definitions and lookups
- extractor: Extract identifiers using regex patterns
- generator: Generate all applicable identifiers with precedence logic
"""

from .extractor import extract_identifier
from .generator import generate_all_with_precedence
from .schemes_codes import get_scheme, get_schemes_for_country, to_iso6523, to_scheme_id

__all__ = [
    'extract_identifier',
    'generate_all_with_precedence',
    'get_scheme',
    'get_schemes_for_country',
    'to_iso6523',
    'to_scheme_id',
]
