"""
PEPPOL v9.4 Identifier Scheme Definitions.

Loads and indexes the 100 PEPPOL participant identifier schemes.
Source: https://docs.peppol.eu/edelivery/codelists/v9.4/
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IdentifierScheme:
    """
    Represents a PEPPOL participant identifier scheme.

    Attributes:
        scheme_id: Human-readable scheme identifier (e.g., "BE:VAT", "FR:SIRENE")
        iso6523: Numeric ICD code (e.g., "9925", "0002")
        country: ISO 3166-1 alpha-2 country code or "international"
        name: Full descriptive name of the scheme
        identifier_type: Classification: "vat", "registration", or "other"
        state: Scheme status: "active", "deprecated", or "removed"
        regex: Optional validation/extraction regex pattern (None = accept as-is)
        supports_suffix: Whether scheme supports organizational unit suffixes
        examples: List of sample valid identifiers
    """

    scheme_id: str
    iso6523: str
    country: str
    name: str
    identifier_type: str
    state: str
    regex: str | None
    supports_suffix: bool
    examples: list[str]

    def extract_value(self, raw_value: str) -> str | None:
        """
        Extract identifier value using regex pattern.

        Args:
            raw_value: Raw identifier string (may contain labels, formatting, etc.)

        Returns:
            Extracted identifier or None if extraction fails

        Logic:
            - If no regex defined: return raw_value as-is (typical for VAT schemes)
            - If regex defined: extract using pattern, return None if no match
        """
        if self.regex is None:
            return raw_value

        match = re.search(self.regex, raw_value)
        return match.group(0) if match else None

    def extract_root_id(self, value: str) -> str:
        """
        Extract root identifier (without suffix) for schemes that support suffixes.

        Currently only FI:OVT2 (0216) is documented to support suffixes.
        Pattern: 0037NNNNNNNN[XXXXX] → root is 0037NNNNNNNN

        Args:
            value: Full identifier value (may include suffix)

        Returns:
            Root identifier or original value if scheme doesn't support suffixes
        """
        if not self.supports_suffix:
            return value

        # FI:OVT2 specific: 0037 + 8 digits = root
        if self.iso6523 == "0216":
            match = re.match(r"(0037\d{8})", value)
            return match.group(1) if match else value

        return value


# Global registries - populated by load_schemes()
_SCHEMES: dict[str, IdentifierScheme] = {}
_SCHEMES_BY_ISO6523: dict[str, IdentifierScheme] = {}
_COUNTRY_SCHEMES: dict[str, list[IdentifierScheme]] = {}


def _parse_regex(validation_rules: str | None) -> str | None:
    """
    Parse regex pattern from validation-rules field.

    Args:
        validation_rules: Validation rules text from JSON

    Returns:
        Regex pattern or None if not found

    Example input:
        "RegEx: [0-9]{9}([0-9]{5})?\\nCheck digits: Luhn Algorithm"
    """
    if not validation_rules:
        return None

    # Look for "Pattern:" or "RegEx:" prefix
    for prefix in ["Pattern:", "RegEx:"]:
        if prefix in validation_rules:
            # Extract everything after prefix until newline
            match = re.search(rf"{prefix}\s*([^\n]+)", validation_rules)
            if match:
                pattern = match.group(1).strip()
                # Clean up any trailing text after the pattern
                # Pattern typically ends before explanatory text
                return pattern

    return None


def _classify_identifier_type(scheme_name: str) -> str:
    """
    Classify scheme as 'vat', 'registration', or 'other' based on name.

    Args:
        scheme_name: Full scheme name from JSON

    Returns:
        Classification: "vat", "registration", or "other"
    """
    name_lower = scheme_name.lower()

    if "vat" in name_lower:
        return "vat"

    # Registration keywords (multilingual)
    registration_keywords = [
        # English
        "registration",
        "chamber",
        "enterprise",
        "business",
        "company",
        "register",
        "organisation",
        "organization",
        "trade",
        "number",  # Often part of company/enterprise number
        # French
        "entreprise",  # enterprise
        "numero",  # number
        # Dutch
        "onderneming",  # enterprise/company
        "nummer",  # number
        # German
        "unternehmen",  # enterprise/company
        # Specific schemes
        "kvk",  # Netherlands Chamber of Commerce
        "kbo",  # Belgian Crossroad Bank
        "sirene",  # French business registry
        "siret",
        "cbe",  # Belgian Crossroad Bank (alt)
    ]

    if any(keyword in name_lower for keyword in registration_keywords):
        return "registration"

    return "other"


def load_schemes() -> None:
    """
    Load PEPPOL v9.4 schemes from bundled JSON file.

    Parses the JSON and builds three indexes:
    - _SCHEMES: scheme_id → IdentifierScheme
    - _SCHEMES_BY_ISO6523: iso6523 → IdentifierScheme
    - _COUNTRY_SCHEMES: country_code → [IdentifierScheme, ...]

    Called automatically on module import.
    """
    json_path = Path(__file__).parent / "peppol_schemes_v9.4.json"

    with open(json_path) as f:
        data = json.load(f)

    for entry in data["values"]:
        # Determine identifier type
        identifier_type = _classify_identifier_type(entry["scheme-name"])

        # Extract regex if present
        regex = _parse_regex(entry.get("validation-rules"))

        # Check for suffix support in structure field
        structure = entry.get("structure", "").lower()
        supports_suffix = "suffix" in structure

        # Parse examples
        examples = []
        if entry.get("examples"):
            # Examples may be newline-separated
            examples = [ex.strip() for ex in entry["examples"].split("\n") if ex.strip()]

        scheme = IdentifierScheme(
            scheme_id=entry["schemeid"],
            iso6523=entry["iso6523"],
            country=entry["country"],
            name=entry["scheme-name"],
            identifier_type=identifier_type,
            state=entry["state"],
            regex=regex,
            supports_suffix=supports_suffix,
            examples=examples,
        )

        # Register in all indexes
        _SCHEMES[scheme.scheme_id] = scheme
        _SCHEMES_BY_ISO6523[scheme.iso6523] = scheme

        # Index by country
        if scheme.country not in _COUNTRY_SCHEMES:
            _COUNTRY_SCHEMES[scheme.country] = []
        _COUNTRY_SCHEMES[scheme.country].append(scheme)


def get_scheme(scheme_id_or_iso6523: str) -> IdentifierScheme | None:
    """
    Get scheme by scheme_id (e.g., "BE:VAT") or iso6523 (e.g., "9925").

    Args:
        scheme_id_or_iso6523: Either scheme_id or iso6523 code

    Returns:
        IdentifierScheme or None if not found
    """
    return _SCHEMES.get(scheme_id_or_iso6523) or _SCHEMES_BY_ISO6523.get(scheme_id_or_iso6523)


def get_schemes_for_country(country_code: str) -> list[IdentifierScheme]:
    """
    Get all schemes applicable to a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "BE", "NL")

    Returns:
        List of applicable IdentifierScheme objects (may be empty)
    """
    return _COUNTRY_SCHEMES.get(country_code, [])


def to_iso6523(scheme_id: str) -> str | None:
    """
    Convert scheme_id to ISO6523 format for comparison.

    Normalizes scheme identifiers to their ISO6523 numeric codes
    for accurate comparison. Handles both formats:
    - "BE:VAT" → "9925"
    - "9925" → "9925"

    Args:
        scheme_id: Scheme identifier (e.g., "BE:VAT", "9925")

    Returns:
        ISO6523 code if found, None if unknown scheme

    Examples:
        >>> to_iso6523("BE:VAT")
        "9925"
        >>> to_iso6523("9925")
        "9925"
        >>> to_iso6523("0208")
        "0208"
    """
    # Already in ISO6523 format (numeric)
    if scheme_id.isdigit():
        return scheme_id

    # Look up by scheme_id
    scheme = _SCHEMES.get(scheme_id)
    if scheme:
        return scheme.iso6523

    # Unknown scheme
    return None


def to_scheme_id(iso6523: str) -> str | None:
    """
    Convert ISO6523 code to human-readable scheme_id format.

    Reverse of to_iso6523(). Converts numeric ICD codes to their
    human-readable scheme identifiers:
    - "9925" → "BE:VAT"
    - "0002" → "FR:SIRENE"

    Args:
        iso6523: ISO6523 numeric code (e.g., "9925", "0208")

    Returns:
        Scheme ID if found, None if unknown ISO6523 code

    Examples:
        >>> to_scheme_id("9925")
        "BE:VAT"
        >>> to_scheme_id("0002")
        "FR:SIRENE"
        >>> to_scheme_id("BE:VAT")
        "BE:VAT"
    """
    # Already in scheme_id format (non-numeric)
    if not iso6523.isdigit():
        return iso6523

    # Look up by ISO6523
    scheme = _SCHEMES_BY_ISO6523.get(iso6523)
    if scheme:
        return scheme.scheme_id

    # Unknown ISO6523 code
    return None


# Load schemes on module import
load_schemes()
