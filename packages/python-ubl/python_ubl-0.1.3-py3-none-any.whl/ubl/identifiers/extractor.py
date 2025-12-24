"""
Identifier Extraction Logic.

Extracts clean identifier values from raw input strings using
country-specific PEPPOL schemes and regex patterns.
"""

import warnings

from .schemes_codes import get_schemes_for_country


def extract_identifier(value: str, country_code: str, identifier_type: str) -> str | None:
    """
    Extract identifier value using country-specific regex patterns.

    Args:
        value: Raw identifier value (e.g., "kvk: 64985636", "BE0867709540")
        country_code: ISO 3166-1 alpha-2 country code (e.g., "NL", "BE")
        identifier_type: Type of identifier: "vat" or "registration"

    Returns:
        Extracted clean identifier value or None if extraction fails

    Logic:
        1. Find applicable schemes for country + identifier_type
        2. If scheme has regex: extract using pattern
        3. If scheme has no regex: return value as-is (common for VAT)
        4. Return None if no applicable scheme or extraction fails

    Examples:
        >>> extract_identifier("kvk: 64985636", "NL", "registration")
        "64985636"

        >>> extract_identifier("BE0867709540", "BE", "vat")
        "BE0867709540"  # No regex, accepted as-is
    """
    # Find applicable schemes for this country and type
    schemes = [
        s for s in get_schemes_for_country(country_code) if s.identifier_type == identifier_type and s.state == "active"
    ]

    if not schemes:
        # No scheme found for this country + type
        return None

    # Try first applicable scheme
    scheme = schemes[0]

    extracted = scheme.extract_value(value)

    if extracted is None and scheme.regex:
        # Extraction failed with regex defined
        warnings.warn(
            f"Could not extract {identifier_type} from '{value}' using {scheme.scheme_id} regex: {scheme.regex}",
        )

    return extracted
