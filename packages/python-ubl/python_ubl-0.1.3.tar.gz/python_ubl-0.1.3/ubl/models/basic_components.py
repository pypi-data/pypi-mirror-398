"""
UBL Basic Components (CBC elements).

This module contains dataclasses for all UBL CommonBasicComponents
(primitive/scalar elements like Amount, Identifier, Code, Quantity).
"""

import re
from abc import ABC
from dataclasses import dataclass, field
from decimal import Decimal

from ..constants import DEFAULT_CURRENCY_CODE, DEFAULT_UNIT_CODE, UNIT_CODE_LIST_ID
from ..exceptions import ValidationError
from .common import BaseElement, CbcMixin, ValueStrMixin, WithAsMixin


def get_max_decimal_places(*values) -> int:
    """
    Get the maximum decimal places from a set of Decimal values.

    Ignores non-Decimal values.
    Returns 0 if no Decimal values found.

    Args:
        *values: Variable number of values (may include Decimal, int, float, etc.)

    Returns:
        Maximum decimal places among Decimal values
    """
    max_places = 0
    for value in values:
        if isinstance(value, Decimal):
            # Get the exponent (negative for decimal places)
            # e.g., Decimal('100.50') has exponent -2 (2 decimal places)
            exponent = value.as_tuple().exponent
            if exponent < 0:
                max_places = max(max_places, abs(exponent))
    return max_places


def quantize_to_max_precision(result: Decimal, *source_values, cap: int | None = 2) -> Decimal:
    """
    Quantize a Decimal result to the maximum precision of source values.

    Args:
        result: The Decimal result of a calculation
        *source_values: The source Decimal values used in the calculation
        cap: Maximum decimal places allowed (default: 2 for UBL/PEPPOL compliance)
             Set to None for unlimited precision

    Returns:
        Quantized Decimal with precision matching the most precise source value,
        capped at the specified maximum
    """
    max_places = get_max_decimal_places(*source_values)

    # Apply cap if specified
    if cap is not None:
        max_places = min(cap, max_places)
    elif max_places == 0:
        # No decimal places found and no cap specified, return as-is
        return result

    # Create quantization template (e.g., '0.01' for 2 places, '1' for 0 places)
    quantizer = Decimal(10) ** -max_places
    return result.quantize(quantizer)


@dataclass
class Amount(CbcMixin, WithAsMixin, BaseElement):
    """
    UBL cbc:Amount - Monetary amount with currency.

    This dataclass represents a monetary value. While not frozen at the
    dataclass level (due to inheritance constraints), it should be treated
    as immutable in practice.

    Automatically preserves decimal precision from the input value.

    Attributes:
        value: The numeric amount (must be >= 0)
        currencyID: ISO 4217 currency code (default: EUR)
        element_name: XML element name (e.g., "TaxAmount", "LineExtensionAmount")
    """

    value: Decimal
    currencyID: str = field(default=DEFAULT_CURRENCY_CODE, kw_only=True)

    def __post_init__(self) -> None:
        """Ensure value is quantized to preserve its decimal precision (capped at 2 decimals for UBL/PEPPOL)."""
        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Then: auto-quantize to preserve precision (with 2-decimal cap)
        if isinstance(self.value, Decimal):
            self.value = quantize_to_max_precision(self.value, self.value, cap=2)


@dataclass
class Quantity(CbcMixin, WithAsMixin, BaseElement):
    """
    UBL cbc:Quantity - Quantity with unit code.

    This dataclass represents a measured quantity. While not frozen at the
    dataclass level (due to inheritance constraints), it should be treated
    as immutable in practice.

    Attributes:
        value: The numeric quantity
        unitCode: Unit of measure code (default: EA = Each)
        unitCodeListID: Code list identifier (default: UNECERec20)
        element_name: XML element name (typically "InvoicedQuantity" or "CreditedQuantity")
    """

    value: Decimal
    unitCode: str = field(default=DEFAULT_UNIT_CODE, kw_only=True)
    unitCodeListID: str = field(default=UNIT_CODE_LIST_ID, kw_only=True)


@dataclass
class Percent(CbcMixin, BaseElement):
    """
    UBL cbc:Percent - Percentage value.

    Used for tax rates and other percentage values in UBL documents.

    Attributes:
        value: The numeric percentage (e.g., 21 for 21%)

    Note: Smart casting automatically converts int/float/str to Decimal.
    No __post_init__ validation needed for type conversion.
    """

    value: Decimal


@dataclass(eq=False, unsafe_hash=False)
class BaseIdentifier(CbcMixin, BaseElement, ABC):
    """
    Abstract base class for UBL identifier elements.

    Provides common functionality for all identifier types (ID, EndpointID, etc.).
    Cannot be instantiated directly - use concrete subclasses.

    Handles multiple ID types through method dispatch:
    - PEPPOL participant IDs (BE:VAT, 9925, etc.) - with normalization
    - Codelist IDs (UNCL5305, UN/ECE 5153) - with validation where applicable
    - Financial IDs (IBAN, BIC) - no validation
    - Plain IDs (no scheme) - no processing

    Attributes:
        value: The identifier value (may be normalized in __post_init__)
        schemeID: Optional identifier scheme (e.g., "BE:VAT", "IBAN", "9925", "UNCL5305")
        schemeName: Optional scheme name (auto-populated for PEPPOL schemes)
        schemeAgencyID: Optional scheme agency (e.g., "6" for UN/ECE)
    """

    value: str | None
    schemeID: str | None = field(default=None, kw_only=True)
    schemeName: str | None = field(default=None, kw_only=True)
    schemeAgencyID: str | None = field(default=None, kw_only=True)

    lowercase_value = False

    def __post_init__(self) -> None:
        """
        Process identifier based on scheme type using method dispatch.

        Detects ID type from schemeID pattern and dispatches to appropriate handler:
        - UNCL codelist (UNCL5305, etc.)
        - UN/ECE codelist (UN/ECE 5153, etc.)
        - Financial (IBAN, BIC)
        - PEPPOL (BE:VAT, 9925, etc.)
        - Plain (no scheme)
        """
        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Then: dispatch to handler based on scheme type
        handler_name = self._detect_id_type()
        handler = getattr(self, f'_handle_{handler_name}_id')
        handler()

    def _detect_id_type(self) -> str:
        """
        Detect ID type from schemeID using regex patterns.

        Returns:
            Handler name suffix: 'plain', 'uncl_codelist', 'unece_codelist', 'financial', 'peppol'
        """
        if self.schemeID is None:
            return 'plain'

        # Regex mapping for ID type detection
        handler_map = {
            r'^UNCL\d+$': 'uncl_codelist',  # UNCL5305, UNCL4461, etc.
            r'^UN/ECE': 'unece_codelist',  # UN/ECE 5153
            r'^(IBAN|BIC)$': 'financial',  # Financial identifiers
            r'^[A-Z]{2}:[A-Z]+': 'peppol',  # BE:VAT, NL:KVK, etc.
            r'^[0-9]+$': 'peppol',  # ISO6523 codes: 9925, 0208, etc.
        }

        for pattern, handler in handler_map.items():
            if re.match(pattern, self.schemeID):
                return handler

        # Default: treat as plain ID
        return 'plain'

    def _handle_plain_id(self) -> None:
        """Handle plain ID without scheme - no normalization or validation."""
        pass  # Nothing to do

    def _handle_uncl_codelist_id(self) -> None:
        """
        Handle UNCL codelist ID (e.g., UNCL5305 for tax categories).

        Validates specific codelist values where applicable.
        Currently supports:
        - UNCL5305: Tax category codes (S, Z, E, AE, G, ZZ, K)

        TODO: Find official UNCL codelist references for comprehensive validation
        """
        # Tax category codes (UNCL5305)
        if self.schemeID == 'UNCL5305':
            # Known valid codes from PEPPOL BIS Billing 3.0
            # TODO: Find official UNCL5305 reference for complete list
            valid_codes = {'S', 'Z', 'E', 'AE', 'G', 'ZZ', 'K'}
            if self.value and self.value not in valid_codes:
                raise ValidationError(
                    f'Invalid tax category code: {self.value}. '
                    f'Must be one of: {", ".join(sorted(valid_codes))} '
                    f'(UNCL5305)'
                )

        # Other UNCL codelists accepted as-is (no validation yet)

    def _handle_unece_codelist_id(self) -> None:
        """Handle UN/ECE codelist ID (e.g., UN/ECE 5153 for tax schemes) - no normalization."""
        pass  # Accept as-is

    def _handle_financial_id(self) -> None:
        """
        Handle financial IDs (IBAN, BIC).

        PEPPOL BIS 3.0 format (per base-example.xml):
        - No schemeID attribute
        - Value prefixed with "IBAN" or "BIC"
        - No spaces in value

        Examples:
            Standard: <cbc:ID schemeID="IBAN">BE20 1030 8550 4356</cbc:ID>
            PEPPOL:   <cbc:ID>IBANBE20103085504356</cbc:ID>
        """
        from ..context import is_peppol_mode

        if is_peppol_mode() and self.schemeID in ('IBAN', 'BIC'):
            # Strip spaces from value
            cleaned_value = self.value.replace(' ', '')

            # Prefix with scheme type if not already prefixed
            if not cleaned_value.startswith(self.schemeID):
                self.value = f'{self.schemeID}{cleaned_value}'
            else:
                self.value = cleaned_value

            # Remove schemeID attribute (PEPPOL requirement)
            self.schemeID = None

    def _handle_peppol_id(self) -> None:
        """
        Handle PEPPOL participant ID - apply normalization and validation.

        Logic:
        1. Look up scheme in PEPPOL registry
        2. Extract value using scheme regex if defined
        3. If extraction fails (doesn't match regex), clear schemeID to prevent invalid output
        4. Lowercase value if schemeID is ISO6523 numeric code
        5. Auto-populate schemeName from scheme.name
        """
        from ..identifiers import get_scheme

        scheme = get_scheme(self.schemeID)
        if not scheme:
            # Unknown scheme - no normalization
            return

        # Step 1: Extract if regex defined
        if scheme.regex:
            extracted = scheme.extract_value(self.value)
            if extracted:
                self.value = extracted
            else:
                # Extraction failed - value doesn't match regex pattern
                # Clear schemeID to prevent generating invalid schemeID attribute in XML
                self.schemeID = None
                self.schemeName = None
                return

        # Step 2: Lowercase if ISO6523 code
        if self.schemeID.isdigit() and self.lowercase_value:
            self.value = self.value.lower()

        # Step 3: Auto-populate schemeName from scheme.name if not already set
        if self.schemeName is None and scheme.name:
            self.schemeName = scheme.name

    def __eq__(self, other: object) -> bool:
        """
        Compare identifiers with case-insensitive values and normalized schemes.

        Two identifiers are equal if:
        - Values match (case-insensitive)
        - Schemes match (normalized to ISO6523)

        Examples:
            Identifier("BE0597601756", schemeID="BE:VAT") == Identifier("be0597601756", schemeID="9925")  # True
            Identifier("BE0597601756", schemeID="BE:VAT") == Identifier("be0597601756", schemeID="BE:VAT")  # True

        Args:
            other: Object to compare with

        Returns:
            True if identifiers match (case-insensitive value, normalized scheme)
        """
        if not isinstance(other, BaseIdentifier):
            return False

        # Import here to avoid circular dependency
        from ..identifiers import to_iso6523

        # Normalize schemes to ISO6523 for comparison
        self_iso = to_iso6523(self.schemeID) if self.schemeID else None
        other_iso = to_iso6523(other.schemeID) if other.schemeID else None

        return self.value.lower() == other.value.lower() and self_iso == other_iso

    def __hash__(self) -> int:
        """
        Hash for use in sets and dicts.

        Uses normalized ISO6523 scheme for consistent hashing.

        Returns:
            Hash value based on lowercase value and normalized scheme
        """
        # Import here to avoid circular dependency
        from ..identifiers import to_iso6523

        iso_scheme = to_iso6523(self.schemeID) if self.schemeID else None
        return hash((self.value.lower(), iso_scheme))


@dataclass(eq=False, unsafe_hash=False)
class Identifier(BaseIdentifier):
    """
    UBL cbc:ID - Generic identifier with optional scheme.

    Standard identifier element used throughout UBL documents.

    Attributes:
        value: The identifier value
        schemeID: Optional identifier scheme (e.g., "BE:VAT", "IBAN")
        schemeName: Optional scheme name
    """

    @property
    def element_name(self) -> str:
        """Return 'ID' for standard identifier element."""
        return 'ID'


# Alias for XML parsing - parser looks for class named "ID"
ID = Identifier


@dataclass
class StrElement(CbcMixin, ValueStrMixin, BaseElement):
    """
    Base class for CBC elements with a single string value.

    Provides value field and string representation via ValueStrMixin.
    Subclasses only need to provide docstrings - no field declarations needed.

    Attributes:
        value: The string value of the element
    """

    value: str


@dataclass
class Name(StrElement):
    """
    UBL cbc:Name - Simple text name element.

    Used in various contexts like PartyName, ItemName, etc.
    """


@dataclass
class Description(StrElement):
    """
    UBL cbc:Description - Text description element.

    Used for item descriptions, additional details, etc.
    """


@dataclass(eq=False, unsafe_hash=False)
class EndpointID(BaseIdentifier):
    """
    UBL cbc:EndpointID - PEPPOL endpoint identifier.

    Specialized identifier used for party endpoint routing in PEPPOL.

    Attributes:
        value: The endpoint identifier value
        schemeID: PEPPOL scheme identifier (e.g., "9925", "0208")
        schemeName: Optional scheme name
    """

    lowercase_value = True

    def deserialize(self) -> dict:
        """
        Deserialize endpoint ID to Party attributes.

        Returns:
            dict with 'vat', 'registration', or 'peppol_participant_ids'
        """
        from ..identifiers import get_scheme

        if not self.schemeID:
            return {}

        scheme = get_scheme(self.schemeID)
        if not scheme:
            return {}

        # Return based on scheme type
        if scheme.identifier_type == "vat":
            return {'vat': self.value}
        elif scheme.identifier_type == "registration":
            return {'registration': self.value}
        else:
            # Other types go to peppol_participant_ids
            return {'peppol_participant_ids': [f"{self.schemeID}:{self.value.lower()}"]}


@dataclass(eq=False, unsafe_hash=False)
class CompanyID(BaseIdentifier):
    """
    UBL cbc:CompanyID - Company/enterprise identifier.

    Specialized identifier used in PartyTaxScheme and PartyLegalEntity.

    Attributes:
        value: The company identifier value
        schemeID: Scheme identifier (e.g., "BE:VAT", "BE:EN")
        schemeName: Optional scheme name
    """


@dataclass
class Code(CbcMixin, BaseElement):
    """
    UBL cbc:Code - Generic code with list metadata.

    This dataclass represents a coded value with optional list identification
    metadata. While not frozen at the dataclass level (due to inheritance
    constraints), it should be treated as immutable in practice.

    Attributes:
        value: The code value
        listID: Code list identifier (e.g., "UNCL5305" for tax categories)
        listAgencyID: Code list agency (typically "6" for UN/ECE)
        element_name: XML element name (e.g., "TaxCategoryCode", "PaymentMeansCode")
    """

    value: str
    listID: str | None = field(default=None, kw_only=True)
    listAgencyID: str | None = field(default=None, kw_only=True)


@dataclass
class IdentificationCode(CbcMixin, ValueStrMixin, BaseElement):
    """
    UBL cbc:IdentificationCode - Country identification code.

    Used within cac:Country to represent ISO country codes.

    Attributes:
        value: The country code (e.g., "BE", "NL", "FR")
        listID: Code list identifier (default: ISO3166-1:Alpha2)
        listAgencyID: Code list agency (default: "6" for UN/ECE)
    """

    value: str
    listID: str | None = field(default='ISO3166-1:Alpha2', kw_only=True)
    listAgencyID: str | None = field(default='6', kw_only=True)


@dataclass
class StreetName(StrElement):
    """UBL cbc:StreetName - Street name element."""


@dataclass
class AdditionalStreetName(StrElement):
    """UBL cbc:AdditionalStreetName - Additional street information."""


@dataclass
class CityName(StrElement):
    """UBL cbc:CityName - City name element."""


@dataclass
class PostalZone(StrElement):
    """UBL cbc:PostalZone - Postal/ZIP code element."""


@dataclass
class CountrySubentity(StrElement):
    """UBL cbc:CountrySubentity - State/province/region."""


# =============================================================================
# Amount Subclasses
# =============================================================================
# These subclasses inherit all behavior from Amount and only differ in their
# element name, which is automatically derived from the class name.


@dataclass
class TaxAmount(Amount):
    """UBL cbc:TaxAmount - Tax amount with currency."""



@dataclass
class TaxableAmount(Amount):
    """UBL cbc:TaxableAmount - Taxable amount (base for tax calculation)."""



@dataclass
class LineExtensionAmount(Amount):
    """UBL cbc:LineExtensionAmount - Line total amount."""



@dataclass
class TaxExclusiveAmount(Amount):
    """UBL cbc:TaxExclusiveAmount - Total before tax."""



@dataclass
class TaxInclusiveAmount(Amount):
    """UBL cbc:TaxInclusiveAmount - Total with tax."""



@dataclass
class PayableAmount(Amount):
    """UBL cbc:PayableAmount - Final payable amount."""



@dataclass
class PriceAmount(Amount):
    """UBL cbc:PriceAmount - Unit price."""



@dataclass
class AllowanceTotalAmount(Amount):
    """UBL cbc:AllowanceTotalAmount - Total of all allowances/discounts."""



@dataclass
class ChargeTotalAmount(Amount):
    """UBL cbc:ChargeTotalAmount - Total of all charges."""



# =============================================================================
# Quantity Subclasses
# =============================================================================


@dataclass
class InvoicedQuantity(Quantity):
    """UBL cbc:InvoicedQuantity - Invoiced quantity with unit."""



@dataclass
class CreditedQuantity(Quantity):
    """UBL cbc:CreditedQuantity - Credited quantity with unit."""


# =============================================================================
# Base Element for Constant Value Elements
# =============================================================================


@dataclass
class ConstantElement(CbcMixin, BaseElement):
    """
    Base class for constant CBC elements.

    These elements have a fixed value defined as a @property.
    Used for things like UBLVersionID which is always "2.1".
    """

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        """Return property attributes - just the value property."""
        return ['value']


# =============================================================================
# Document-level Constant Elements
# =============================================================================


@dataclass
class UBLVersionID(ConstantElement):
    """UBL cbc:UBLVersionID - UBL version identifier (always "2.1")."""

    @property
    def value(self) -> str:
        """Return UBL version 2.1."""
        return '2.1'


# =============================================================================
# Document-level Variable Elements
# =============================================================================


@dataclass
class CustomizationID(CbcMixin, BaseElement):
    """UBL cbc:CustomizationID - Customization profile identifier."""

    value: str


@dataclass
class ProfileID(CbcMixin, BaseElement):
    """UBL cbc:ProfileID - Business process profile identifier."""

    value: str


@dataclass
class UUID(CbcMixin, BaseElement):
    """UBL cbc:UUID - Document UUID for tracking."""

    value: str


@dataclass
class InvoiceTypeCode(CbcMixin, BaseElement):
    """UBL cbc:InvoiceTypeCode - Invoice type code (380=invoice, 381=credit note)."""

    value: str
    listID: str = field(default='UNCL1001', kw_only=True)
    listAgencyID: str = field(default='6', kw_only=True)


@dataclass
class DocumentCurrencyCode(CbcMixin, BaseElement):
    """UBL cbc:DocumentCurrencyCode - Document currency code (ISO 4217)."""

    value: str
    listID: str = field(default='ISO4217', kw_only=True)
    listAgencyID: str = field(default='6', kw_only=True)


@dataclass
class TaxCurrencyCode(CbcMixin, BaseElement):
    """UBL cbc:TaxCurrencyCode - Tax currency code (ISO 4217)."""

    value: str


# =============================================================================
# Date Elements
# =============================================================================


@dataclass
class Date(CbcMixin, WithAsMixin, BaseElement):
    """
    Base class for date elements.

    Handles conversion from various date formats to ISO string format.
    Accepts datetime.date, datetime.datetime, or ISO string.
    """

    value: str

    def __post_init__(self):
        """Convert date value to ISO format string."""
        from datetime import date, datetime

        # If already a string, validate and use as-is
        if isinstance(self.value, str):
            # Validate it's a valid ISO date
            try:
                date.fromisoformat(self.value)
            except ValueError as e:
                raise ValueError(f'Invalid date string: {self.value}') from e
        # Convert date/datetime to ISO string
        elif isinstance(self.value, datetime):
            self.value = self.value.date().isoformat()
        elif isinstance(self.value, date):
            self.value = self.value.isoformat()
        else:
            raise TypeError(f'Date value must be date, datetime, or ISO string, got {type(self.value)}')


@dataclass
class IssueDate(Date):
    """UBL cbc:IssueDate - Document issue date."""


@dataclass
class DueDate(Date):
    """UBL cbc:DueDate - Payment due date."""


# =============================================================================
# Numeric Elements
# =============================================================================


@dataclass
class LineCountNumeric(CbcMixin, BaseElement):
    """UBL cbc:LineCountNumeric - Number of document lines."""

    auto_cast = False  # Disable auto-casting (value must remain string)
    value: str

    def __post_init__(self):
        """Convert numeric value to string."""
        if isinstance(self.value, int):
            self.value = str(self.value)
        elif not isinstance(self.value, str):
            raise TypeError(f'LineCountNumeric value must be int or str, got {type(self.value)}')


# =============================================================================
# New String Elements for Fixing XML Generation Issues
# =============================================================================


@dataclass
class Note(StrElement):
    """UBL cbc:Note - Line-level note or document note."""


@dataclass
class RegistrationName(StrElement):
    """UBL cbc:RegistrationName - Legal registration name of a party."""


@dataclass
class PaymentID(StrElement):
    """UBL cbc:PaymentID - Payment reference or structured communication."""


@dataclass
class Telephone(StrElement):
    """UBL cbc:Telephone - Contact telephone number."""


@dataclass
class ElectronicMail(StrElement):
    """UBL cbc:ElectronicMail - Contact email address."""


# =============================================================================
# Payment-Related Elements
# =============================================================================


@dataclass
class PaymentMeansCode(Code):
    """
    UBL cbc:PaymentMeansCode - Payment method code.

    Common codes (UNCL4461):
    - 30: Credit transfer
    - 31: Debit transfer
    - 42: Payment to bank account
    - 48: Bank card
    - 49: Direct debit
    """

    value: str
    listID: str = field(default='UNCL4461', kw_only=True)
    listAgencyID: str = field(default='6', kw_only=True)


@dataclass
class PaymentDueDate(Date):
    """UBL cbc:PaymentDueDate - Payment due date."""
