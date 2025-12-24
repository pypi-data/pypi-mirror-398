"""
Identifier Generation with PEPPOL Precedence Logic.

Generates all applicable party identifiers from VAT, registration,
and PEPPOL participant IDs with proper precedence handling.
"""

import warnings
from typing import TYPE_CHECKING

from .schemes_codes import get_scheme, get_schemes_for_country

if TYPE_CHECKING:
    from ..models.aggregate_components import PartyIdentification
    from .schemes_codes import IdentifierScheme


def generate_all_with_precedence(
    country_code: str,
    vat: str | None,
    registration: str | None,
    peppol_participant_ids: list[str],
    numeric_only: bool = True,
) -> list["PartyIdentification"]:
    """
    Generate all applicable party identifiers with precedence logic.

    Algorithm:
        1. Generate from VAT → both scheme_id and iso6523 formats
        2. Generate from registration → both formats
        3. Apply peppol_ids precedence:
           - For iso6523 format: peppol_ids take precedence
           - Compare generated vs peppol, warn if different
           - Keep peppol version regardless
           - For scheme_id format: always keep VAT/registration version
        4. Filter by numeric_only if enabled (PEPPOL requirement)
        5. Deduplicate and return

    Args:
        country_code: ISO 3166-1 alpha-2 country code
        vat: Validated VAT number (already extracted)
        registration: Validated registration number (already extracted)
        peppol_participant_ids: List of PEPPOL IDs in format "iso6523:value"
        numeric_only: If True, only return identifiers with numeric ISO 6523 scheme IDs
                     (filters out custom schemes like BE:VAT, BE:EN). Default: True (PEPPOL mode)

    Returns:
        List of PartyIdentification objects (deduplicated)

    Example (LevIT with numeric_only=True):
        vat="BE0597601756"
        registration="0597601756"
        peppol_ids=["9925:be0597601756", "0208:0597601756"]

        Generated:
        1. 9925:be0597601756 (from peppol, numeric ISO 6523)
        2. 0208:0597601756 (from peppol, numeric ISO 6523)

        Total: 2 identifiers (BE:VAT and BE:EN filtered out)

    Example (LevIT with numeric_only=False):
        Same input generates:
        1. BE:VAT:BE0597601756 (from VAT)
        2. 9925:be0597601756 (from peppol, replaces VAT-generated)
        3. BE:EN:0597601756 (from registration)
        4. 0208:0597601756 (from peppol, replaces registration-generated)

        Total: 4 identifiers
    """
    # Import here to avoid circular dependency
    from ..models.aggregate_components import PartyIdentification

    identifiers = []
    peppol_iso6523_map = {}  # iso6523 → value mapping from peppol_ids

    # Parse peppol_participant_ids into map
    for peppol_id in peppol_participant_ids:
        if ":" in peppol_id:
            iso6523, value = peppol_id.split(":", 1)
            peppol_iso6523_map[iso6523] = value

    # Generate from VAT
    if vat:
        vat_identifiers = _generate_from_source(
            value=vat,
            country_code=country_code,
            identifier_type="vat",
            peppol_iso6523_map=peppol_iso6523_map,
        )
        identifiers.extend(vat_identifiers)

    # Generate from registration
    if registration:
        reg_identifiers = _generate_from_source(
            value=registration,
            country_code=country_code,
            identifier_type="registration",
            peppol_iso6523_map=peppol_iso6523_map,
        )
        identifiers.extend(reg_identifiers)

    # Add peppol_ids (already in correct format)
    for iso6523, value in peppol_iso6523_map.items():
        scheme = get_scheme(iso6523)
        if scheme:
            identifiers.append(
                PartyIdentification(
                    value=value,
                    schemeID=iso6523,
                    iso6523=iso6523,
                ),
            )

    # Filter out invalid identifiers (schemeID cleared by extraction failure in child Identifier)
    # Note: This only affects PartyIdentification - other Identifiers (invoice numbers, etc.) are unaffected
    valid_identifiers = [
        pid for pid in identifiers
        if pid.id and pid.id.schemeID is not None
    ]

    # Filter by numeric_only (PEPPOL requirement: only ISO 6523 numeric codes)
    if numeric_only:
        valid_identifiers = [
            pid for pid in valid_identifiers
            if pid.id.schemeID and pid.id.schemeID.isdigit()
        ]

    # Deduplicate using dict.fromkeys (preserves order, uses __hash__)
    return list(dict.fromkeys(valid_identifiers))


def _generate_from_source(
    value: str,
    country_code: str,
    identifier_type: str,
    peppol_iso6523_map: dict[str, str],
) -> list["PartyIdentification"]:
    """
    Generate identifiers from a single source (VAT or registration).

    Returns both scheme_id and iso6523 formats.
    Applies peppol precedence for iso6523 format.

    Args:
        value: Validated identifier value
        country_code: Country code
        identifier_type: "vat" or "registration"
        peppol_iso6523_map: PEPPOL IDs mapped by iso6523 code

    Returns:
        List of PartyIdentification objects
    """
    from ..models.aggregate_components import PartyIdentification

    schemes = [
        s for s in get_schemes_for_country(country_code) if s.identifier_type == identifier_type and s.state == "active"
    ]

    identifiers = []

    for scheme in schemes:
        # Always generate scheme_id format (e.g., BE:VAT:BE0597601756)
        identifiers.append(
            PartyIdentification(
                value=value,
                schemeID=scheme.scheme_id,
                iso6523=scheme.iso6523,
            ),
        )

        # For iso6523 format: check peppol precedence
        if scheme.iso6523 in peppol_iso6523_map:
            peppol_value = peppol_iso6523_map[scheme.iso6523]

            # Compare values (suffix-aware)
            if not _compare_with_suffix_support(value, peppol_value, scheme):
                warnings.warn(
                    f"PEPPOL ID '{scheme.iso6523}:{peppol_value}' differs from "
                    f"{identifier_type}-generated '{scheme.iso6523}:{value}'. "
                    f"Using PEPPOL ID (takes precedence).",
                )

            # Don't add generated iso6523 - will be added from peppol_ids
        else:
            # No peppol precedence, add generated iso6523 format
            # Convert to lowercase for iso6523 format
            identifiers.append(
                PartyIdentification(
                    value=value.lower(),
                    schemeID=scheme.iso6523,
                    iso6523=scheme.iso6523,
                ),
            )

    return identifiers


def _compare_with_suffix_support(value1: str, value2: str, scheme: "IdentifierScheme") -> bool:
    """
    Compare two identifier values, accounting for possible suffixes.

    Returns True if they match (exactly or by root).

    Args:
        value1: First identifier value
        value2: Second identifier value
        scheme: Scheme definition (for suffix support check)

    Returns:
        True if values match, False otherwise
    """
    # Exact match (case-insensitive)
    if value1.lower() == value2.lower():
        return True

    # Try root extraction for schemes with suffix support
    if scheme.supports_suffix:
        root1 = scheme.extract_root_id(value1)
        root2 = scheme.extract_root_id(value2)
        if root1 and root2 and root1.lower() == root2.lower():
            return True

    return False
