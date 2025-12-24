"""
UBL Aggregate Components (CAC elements).

This module contains dataclasses for all UBL CommonAggregateComponents
(complex nested structures like Party, Address, Tax, Payment details).
"""

from dataclasses import InitVar, dataclass, field
from datetime import date
from decimal import Decimal
from typing import ClassVar, List

from ..constants import TAX_CATEGORY_CODES
from ..exceptions import ValidationError
from .basic_components import (
    AdditionalStreetName,
    AllowanceTotalAmount,
    Amount,
    ChargeTotalAmount,
    CityName,
    CompanyID,
    CountrySubentity,
    Description,
    ElectronicMail,
    EndpointID,
    ID,
    Identifier,
    IdentificationCode,
    InvoicedQuantity,
    LineExtensionAmount,
    Name,
    Note,
    PayableAmount,
    PaymentDueDate,
    PaymentID,
    PaymentMeansCode,
    Percent,
    PostalZone,
    PriceAmount,
    RegistrationName,
    StreetName,
    TaxableAmount,
    TaxAmount,
    TaxExclusiveAmount,
    TaxInclusiveAmount,
    Telephone,
    UUID,
)
from .common import BaseElement, CacMixin, WithAsMixin

# =============================================================================
# Group 1: Foundation Components
# =============================================================================


@dataclass
class Country(CacMixin, BaseElement):
    """
    UBL cac:Country - Country identification.

    Uses smart type casting to support both building and parsing:
    - Building: Pass string → auto-casts to IdentificationCode
    - Parsing: Parser creates IdentificationCode from XML

    Attributes:
        identification_code: IdentificationCode element containing country code
    """

    identification_code: IdentificationCode

    class_name_to_attr: ClassVar[dict[str, str]] = {'IdentificationCode': 'identification_code'}


@dataclass
class Contact(CacMixin, BaseElement):
    """
    UBL cac:Contact - Contact information.

    Attributes:
        electronic_mail: Email address (CBC element)
        telephone: Phone number (CBC element)
        name: Contact person name (CBC element)
    """

    electronic_mail: ElectronicMail | None = field(default=None, kw_only=True)
    telephone: Telephone | None = field(default=None, kw_only=True)
    name: Name | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'Name': 'name',
        'Telephone': 'telephone',
        'ElectronicMail': 'electronic_mail',
    }


@dataclass
class TaxScheme(CacMixin, BaseElement):
    """
    UBL cac:TaxScheme - Tax scheme identification.

    Attributes:
        id: Tax scheme identifier (ID object, typically "VAT" with UN/ECE 5153 scheme)
    """

    id: ID | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {'ID': 'id'}

    def __post_init__(self) -> None:
        """Set default VAT scheme if no ID provided."""
        self._super_post_init(super())

        # Create default VAT ID if none provided
        if self.id is None:
            from ..context import is_peppol_mode

            if is_peppol_mode():
                # PEPPOL: TaxScheme ID without schemeID/schemeAgencyID (BR-CL-10)
                self.id = ID(value='VAT')
            else:
                # Standard: TaxScheme ID with UN/ECE codelist
                self.id = ID(value='VAT', schemeID='UN/ECE 5153', schemeAgencyID='6')


# =============================================================================
# Group 2: Address Components
# =============================================================================


@dataclass
class Address(CacMixin, BaseElement):
    """
    UBL cac:Address - Generic address component.

    Base class for postal addresses and other address types.
    Supports two modes:
    - Building: Provide string values (street_name, city_name, etc.) → generates child elements
    - Parsing: Provide child elements → extracts string values

    Attributes:
        street_name: Street name (StreetName element or str for building)
        city_name: City name (CityName element or str for building)
        postal_zone: Postal/ZIP code (PostalZone element or str for building)
        country_code: ISO 3166-1 alpha-2 country code (convenience field for building, extracted when parsing)
        additional_street_name: Additional street information (optional)
        country_subentity: State/province/region (optional)
        country: Country component (auto-generated from country_code when building, provided when parsing)
    """

    # All fields optional to support both building and parsing modes
    street_name: StreetName | None = None
    city_name: CityName | None = None
    postal_zone: PostalZone | None = None
    additional_street_name: AdditionalStreetName | None = field(default=None, kw_only=True)
    country_subentity: CountrySubentity | None = field(default=None, kw_only=True)
    country: Country | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'StreetName': 'street_name',
        'CityName': 'city_name',
        'PostalZone': 'postal_zone',
        'AdditionalStreetName': 'additional_street_name',
        'CountrySubentity': 'country_subentity',
        'Country': 'country',
    }

    def __post_init__(self) -> None:
        self._super_post_init(super())

        # Validate: Required fields must be provided
        if not self.street_name:
            raise ValidationError('Address (building): street_name is required')
        if not self.city_name:
            raise ValidationError('Address (building): city_name is required')
        if not self.postal_zone:
            raise ValidationError('Address (building): postal_zone is required')
        if not self.country:
            raise ValidationError('Address (building): country is required')


@dataclass
class PostalAddress(Address):
    """
    UBL cac:PostalAddress - Postal address (alias of Address).

    This is functionally identical to Address but uses the PostalAddress
    element name in XML for Party postal addresses.
    """

    pass


# =============================================================================
# Group 3: Financial Components
# =============================================================================


@dataclass
class FinancialInstitution(CacMixin, BaseElement):
    """
    UBL cac:FinancialInstitution - Financial institution (bank).

    Per UBL 2.1 specification, supports ID, Name, and Address child elements.

    Attributes:
        id: BIC code identifier (cbc:ID) [0..1]
        name: Name of the financial institution (cbc:Name) [0..1]
        address: Address of the financial institution (cac:Address) [0..1]
    """

    id: Identifier  # BIC code
    name: Name | None = field(default=None, kw_only=True)
    address: Address | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'ID': 'id',
        'Name': 'name',
        'Address': 'address',
    }


@dataclass
class FinancialInstitutionBranch(CacMixin, BaseElement):
    """
    UBL cac:FinancialInstitutionBranch - Bank branch.

    Attributes:
        id: BIC identifier (optional, Peppol BIS 3 pattern)
        financial_institution: Financial institution details (optional)
    """

    id: Identifier | None = field(default=None, kw_only=True)
    financial_institution: FinancialInstitution | None = field(default=None, kw_only=True)

    _base_class_name_to_attr: ClassVar[dict[str, str]] = {
        'ID': 'id',
        'FinancialInstitution': 'financial_institution',
    }

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """
        Get element mapping, filtered for PEPPOL mode.

        PEPPOL/CEN UBL-CR-664: Should not include FinancialInstitution element.

        Returns:
            Filtered mapping dictionary
        """
        from ..context import is_peppol_mode

        mapping = self._base_class_name_to_attr.copy()

        if is_peppol_mode():
            # UBL-CR-664: Remove FinancialInstitution
            mapping.pop('FinancialInstitution', None)

        return mapping


@dataclass
class PayeeFinancialAccount(CacMixin, BaseElement):
    """
    UBL cac:PayeeFinancialAccount - Payee's bank account.

    Attributes:
        id: IBAN identifier
        name: Account holder name (CBC element)
        financial_institution_branch: Branch details with BIC
    """

    id: Identifier  # IBAN
    name: Name | None = field(default=None, kw_only=True)
    financial_institution_branch: FinancialInstitutionBranch | None = field(default=None, kw_only=True)

    _base_class_name_to_attr: ClassVar[dict[str, str]] = {
        'ID': 'id',
        'Name': 'name',
        'FinancialInstitutionBranch': 'financial_institution_branch',
    }

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """
        Get element mapping, filtered for PEPPOL mode.

        PEPPOL/CEN UBL-CR-664: Should not include FinancialInstitutionBranch.

        Returns:
            Filtered mapping dictionary
        """
        from ..context import is_peppol_mode

        mapping = self._base_class_name_to_attr.copy()

        if is_peppol_mode():
            # UBL-CR-664: Remove FinancialInstitutionBranch
            mapping.pop('FinancialInstitutionBranch', None)

        return mapping


# =============================================================================
# Group 4: Tax Components
# =============================================================================


@dataclass
class TaxCategory(CacMixin, WithAsMixin, BaseElement):
    """
    UBL cac:TaxCategory - Tax category with rate.

    Supported codes (UNCL5305):
    - S: Standard rate
    - Z: Zero rated
    - E: Exempt from tax
    - AE: VAT Reverse Charge
    - G: Free export item, tax not charged
    - K: VAT exempt for EEA intra-community supply
    - ZZ: Not subject to VAT

    Validation is performed by ID._handle_uncl_codelist_id() method.

    Attributes:
        id: Tax category code (ID object with schemeID="UNCL5305")
        percent: Tax percentage rate (Percent object)
        name: Optional human-readable tax category name (Name object)
        tax_scheme: Tax scheme (defaults to VAT)
    """

    id: ID
    percent: Percent
    name: Name | None = field(default=None, kw_only=True)
    tax_scheme: TaxScheme | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'ID': 'id',
        'Name': 'name',
        'Percent': 'percent',
        'TaxScheme': 'tax_scheme',
    }

    def __post_init__(self) -> None:
        """Set default tax scheme if none provided."""
        self._super_post_init(super())

        # Create default VAT scheme if none provided
        if self.tax_scheme is None:
            self.tax_scheme = TaxScheme()


@dataclass
class ClassifiedTaxCategory(TaxCategory):
    """
    Alias for item-level tax categories (renders as ClassifiedTaxCategory).

    Functionally identical to TaxCategory but with different XML element name.
    Used in Item to specify the tax category for a product/service.
    """
    _element_name = 'ClassifiedTaxCategory'


@dataclass
class TaxSubtotal(CacMixin, BaseElement):
    """
    UBL cac:TaxSubtotal - Tax calculation for a single rate.

    The percent field is optional - it can be present directly in TaxSubtotal
    (for convenience/redundancy) or derived from the TaxCategory. If both are
    present, they should match.

    Attributes:
        taxable_amount: Amount subject to tax
        tax_amount: Calculated tax amount
        tax_category: Tax category details (contains percent)
        percent: Tax percentage (optional, falls back to tax_category.percent)
    """

    taxable_amount: TaxableAmount
    tax_amount: TaxAmount
    tax_category: TaxCategory
    percent: Percent | None = field(default=None, kw_only=True)

    _base_class_name_to_attr: ClassVar[dict[str, str]] = {
        'TaxableAmount': 'taxable_amount',
        'TaxAmount': 'tax_amount',
        'Percent': 'percent',
        'TaxCategory': 'tax_category',
    }

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """
        Get element mapping, filtered for PEPPOL mode.

        PEPPOL/CEN UBL-CR-499: TaxSubtotal should not include Percent element.

        Returns:
            Filtered mapping dictionary
        """
        from ..context import is_peppol_mode

        mapping = self._base_class_name_to_attr.copy()

        if is_peppol_mode():
            # UBL-CR-499: Remove Percent
            mapping.pop('Percent', None)

        return mapping

    def __post_init__(self) -> None:
        """Derive percent from tax_category if not provided."""
        self._super_post_init(super())

        # If no percent provided, use the one from tax_category
        if self.percent is None and self.tax_category:
            self.percent = self.tax_category.percent


@dataclass
class TaxTotal(CacMixin, BaseElement):
    """
    UBL cac:TaxTotal - Aggregated tax totals.

    Attributes:
        tax_amount: Total tax amount (must equal sum of subtotals)
        tax_subtotals: List of tax subtotals (one per rate)
    """

    tax_amount: TaxAmount
    tax_subtotals: list[TaxSubtotal] = field(default_factory=list, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'TaxAmount': 'tax_amount',
        'TaxSubtotal': 'tax_subtotals',
    }

    def __post_init__(self) -> None:
        """Validate tax amount equals sum of subtotals."""
        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Then: validate sum
        if self.tax_subtotals:
            calculated = sum(st.tax_amount.value for st in self.tax_subtotals)
            if calculated != self.tax_amount.value:
                raise ValidationError(
                    f'TaxTotal amount {self.tax_amount.value} does not match sum of subtotals {calculated}',
                )


# =============================================================================
# Group 5: Payment Component
# =============================================================================


@dataclass
class PaymentMeans(CacMixin, BaseElement):
    """
    UBL cac:PaymentMeans - Payment instructions.

    Payment means codes (UNCL4461):
    - 1: Instrument not defined
    - 30: Credit transfer
    - 31: Debit transfer (default)
    - 42: Payment to bank account
    - 48: Bank card
    - 49: Direct debit

    Attributes:
        payment_means_code: Payment method code (CBC element, default: 31 = debit transfer)
        payment_due_date: Payment due date (CBC element)
        payment_id: Structured communication reference (CBC element)
        payee_financial_account: Payee's bank account details
    """

    payment_means_code: PaymentMeansCode | None = field(default=None, kw_only=True)  # Will be set in __post_init__
    payment_due_date: PaymentDueDate | None = field(default=None, kw_only=True)
    payment_id: PaymentID | None = field(default=None, kw_only=True)
    payee_financial_account: PayeeFinancialAccount | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'PaymentMeansCode': 'payment_means_code',
        'PaymentDueDate': 'payment_due_date',
        'PaymentID': 'payment_id',
        'PayeeFinancialAccount': 'payee_financial_account',
    }

    def __post_init__(self) -> None:
        """Set default PaymentMeansCode if not provided."""
        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Set default payment_means_code if None
        if self.payment_means_code is None:
            self.payment_means_code = PaymentMeansCode(value='31')


# =============================================================================
# Group 6: Line Item Components
# =============================================================================


@dataclass
class Price(CacMixin, BaseElement):
    """
    UBL cac:Price - Unit price.

    Attributes:
        price_amount: Price per unit
    """

    price_amount: PriceAmount

    class_name_to_attr: ClassVar[dict[str, str]] = {'PriceAmount': 'price_amount'}


@dataclass
class SellersItemIdentification(CacMixin, BaseElement):
    """
    UBL cac:SellersItemIdentification - Seller's item identifier wrapper.

    Simple wrapper around cbc:ID for seller's product code.

    Supports two modes:
    - Building: Provide value, schemeID → generates id element
    - Parsing: Provide id element → extracts value, schemeID

    Attributes:
        value: The identifier value (required for building, extracted when parsing)
        schemeID: Optional scheme identifier (e.g., "GTIN", "EAN")
        id: Identifier element (provided when parsing, generated when building)
    """

    # Fields for building mode
    value: str | None = None
    schemeID: str | None = None

    # ID element - provided when parsing, generated when building
    id: Identifier | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {'ID': 'id'}

    def __post_init__(self) -> None:
        """Process based on mode (building vs parsing)."""
        building_mode = self.id is None

        if building_mode:
            # BUILDING MODE: Trigger type casting FIRST
            self._super_post_init(super())

            # Validate: value required
            if not self.value:
                raise ValidationError('SellersItemIdentification (building): value is required')

            # Create ID child element
            self.id = Identifier(value=self.value, schemeID=self.schemeID)
        else:
            # PARSING MODE: Extract from id element
            self.value = self.id.value
            self.schemeID = self.id.schemeID

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        """
        SellersItemIdentification doesn't serialize any direct fields as XML attributes.

        All XML output comes from the id child element (cbc:ID) mapped in class_name_to_attr.
        The value and schemeID fields are internal and used for:
        - Building the id element
        - Extracting from the id element during parsing
        """
        return []


@dataclass
class Item(CacMixin, BaseElement):
    """
    UBL cac:Item - Product or service description.

    Attributes:
        name: Item name/description (can be derived from description if not provided)
        description: Additional description (or main description if name not provided)
        sellers_item_identification: Seller's product code
        classified_tax_category: Tax category for this item
    """

    name: Name | None = field(default=None, kw_only=True)
    description: Description | None = field(default=None, kw_only=True)
    sellers_item_identification: SellersItemIdentification | None = field(default=None, kw_only=True)
    classified_tax_category: ClassifiedTaxCategory | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'Name': 'name',
        'Description': 'description',
        'SellersItemIdentification': 'sellers_item_identification',
        'ClassifiedTaxCategory': 'classified_tax_category',
    }

    def __post_init__(self) -> None:
        """Derive name from description if needed."""
        self._super_post_init(super())

        # If no name but have description, use description as name
        if self.name is None and self.description:
            from .basic_components import Name

            self.name = Name(self.description.value)
        elif self.name is None:
            raise ValidationError('Item: name or description must be provided')


@dataclass
class InvoiceLine(CacMixin, BaseElement):
    """
    UBL cac:InvoiceLine - Invoice line item.

    In full invoices, validates that line_extension_amount = invoiced_quantity × price_amount.
    In minimal invoices, quantity and price may be omitted.

    Attributes:
        id: Line number (ID element)
        line_extension_amount: Line total
        item: Product/service details
        invoiced_quantity: Quantity with unit (optional in minimal invoices)
        price: Unit price (optional in minimal invoices)
        uuid: Unique line identifier (UUID element)
        notes: Line-level notes (list of Note CBC elements)
        tax_total: Optional line-level tax details
    """

    id: ID
    line_extension_amount: LineExtensionAmount
    item: Item
    invoiced_quantity: InvoicedQuantity | None = field(default=None, kw_only=True)
    price: Price | None = field(default=None, kw_only=True)
    uuid: UUID | None = field(default=None, kw_only=True)
    notes: list[Note] = field(default_factory=list, kw_only=True)
    tax_total: TaxTotal | None = field(default=None, kw_only=True)

    _base_class_name_to_attr: ClassVar[dict[str, str]] = {
        'ID': 'id',
        'UUID': 'uuid',
        'Note': 'notes',
        'InvoicedQuantity': 'invoiced_quantity',
        'LineExtensionAmount': 'line_extension_amount',
        'TaxTotal': 'tax_total',  # UBL 2.1: TaxTotal must come before Item and Price
        'Item': 'item',
        'Price': 'price',
    }

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """
        Get element mapping, filtered for PEPPOL mode.

        PEPPOL/CEN UBL-CR-561: InvoiceLine should not include TaxTotal element.

        Returns:
            Filtered mapping dictionary
        """
        from ..context import is_peppol_mode

        mapping = self._base_class_name_to_attr.copy()

        if is_peppol_mode():
            # UBL-CR-561: Remove TaxTotal
            mapping.pop('TaxTotal', None)

        return mapping

    def __post_init__(self) -> None:
        """Validate line extension amount = quantity × price (if both present)."""
        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Then: validate calculation (only if both quantity and price are present)
        if self.invoiced_quantity and self.price:
            calculated = self.invoiced_quantity.value * self.price.price_amount.value
            if calculated != self.line_extension_amount.value:
                raise ValidationError(
                    f'Line {self.id}: Extension amount {self.line_extension_amount.value} '
                    f'does not match quantity × price = {calculated}',
                )


@dataclass
class CreditNoteLine(InvoiceLine):
    """
    UBL cac:CreditNoteLine - Credit note line item.

    Identical structure to InvoiceLine, just different XML element name.
    """

    _element_name = 'CreditNoteLine'


# =============================================================================
# Group 7: Document Totals
# =============================================================================


@dataclass
class LegalMonetaryTotal(CacMixin, BaseElement):
    """
    UBL cac:LegalMonetaryTotal - Document-level monetary totals.

    Attributes:
        payable_amount: Final amount due (required)
        line_extension_amount: Sum of all line totals (optional in minimal invoices)
        tax_exclusive_amount: Subtotal before tax (optional)
        tax_inclusive_amount: Total with tax (optional)
        allowance_total_amount: Total allowances/discounts (optional)
        charge_total_amount: Total charges (optional)
    """

    payable_amount: PayableAmount
    line_extension_amount: LineExtensionAmount | None = field(default=None, kw_only=True)
    tax_exclusive_amount: TaxExclusiveAmount | None = field(default=None, kw_only=True)
    tax_inclusive_amount: TaxInclusiveAmount | None = field(default=None, kw_only=True)
    allowance_total_amount: AllowanceTotalAmount | None = field(default=None, kw_only=True)
    charge_total_amount: ChargeTotalAmount | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'LineExtensionAmount': 'line_extension_amount',
        'TaxExclusiveAmount': 'tax_exclusive_amount',
        'TaxInclusiveAmount': 'tax_inclusive_amount',
        'PayableAmount': 'payable_amount',
        'AllowanceTotalAmount': 'allowance_total_amount',
        'ChargeTotalAmount': 'charge_total_amount',
    }


# =============================================================================
# Group 8: Party Components
# =============================================================================


@dataclass
class PartyName(CacMixin, BaseElement):
    """
    UBL cac:PartyName - Container for party name.

    Simple wrapper that holds the party's name as a cbc:Name child element.

    Attributes:
        name: The party's legal or trading name (string, extracted from Name child if parsing)
    """

    name: Name

    class_name_to_attr: ClassVar[dict[str, str]] = {'Name': 'name'}


@dataclass
class PartyIdentification(CacMixin, BaseElement):
    """
    UBL cac:PartyIdentification - A single identifier for a party.

    Can be in schemeID format (BE:VAT) or iso6523 format (9925).
    Used to represent party identifiers in both human-readable and
    PEPPOL routing formats.

    Supports two modes:
    - Building: Provide value, schemeID, iso6523 → generates id element
    - Parsing: Provide id element → extracts value, schemeID, iso6523

    Attributes:
        value: The identifier value (required for building, extracted when parsing)
        schemeID: Scheme identifier (e.g., "BE:VAT", "9925") (required for building, extracted when parsing)
        iso6523: ISO 6523 ICD code (for mapping between formats) (required for building, extracted when parsing)
        id: Identifier element (provided when parsing, generated when building)

    Note:
        Treat as immutable in practice (not frozen due to Python 3.13 constraints).
        Custom __eq__ and __hash__ enable proper comparison and deduplication.
    """

    # All fields optional to support both building and parsing modes
    value: str | None = None
    schemeID: str | None = None
    iso6523: str | None = None

    # ID element - provided when parsing, generated when building
    id: Identifier | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {'ID': 'id'}

    def __post_init__(self) -> None:
        """
        Process based on mode (building vs parsing) with three-phase logic.

        Phase 1: Mode-specific processing
        Phase 2: Normalization (schemeID ↔ iso6523)
        Phase 3: Finalization
        """
        from ..identifiers import to_iso6523, to_scheme_id

        # ========== PHASE 1: Mode-specific processing ==========
        building_mode = self.id is None

        if building_mode:
            # BUILDING MODE: Trigger type casting FIRST
            self._super_post_init(super())

            # Validate: value required + at least one of (schemeID OR iso6523)
            if not self.value:
                raise ValidationError('PartyIdentification (building): value is required')
            if not self.schemeID and not self.iso6523:
                raise ValidationError(
                    f'PartyIdentification (building): at least one of schemeID or iso6523 is required. '
                    f'Got value={self.value}, schemeID={self.schemeID}, iso6523={self.iso6523}'
                )
        else:
            # PARSING MODE: Extract from id element
            self.value = self.id.value
            self.schemeID = self.id.schemeID
            # iso6523 will be deduced in Phase 2

        # ========== PHASE 2: Normalization (both modes) ==========

        # 1. If schemeID is numeric → move to iso6523 (unless they already match)
        if self.schemeID and self.schemeID.isdigit():
            # If iso6523 already matches schemeID, keep both as-is (dual representation)
            if self.iso6523 != self.schemeID:
                self.iso6523 = self.schemeID
                self.schemeID = None

        # 2. If schemeID is None → deduce from iso6523
        if self.schemeID is None and self.iso6523:
            self.schemeID = to_scheme_id(self.iso6523)

        # 3. If iso6523 is None → deduce from schemeID
        if self.iso6523 is None and self.schemeID:
            self.iso6523 = to_iso6523(self.schemeID)

        # ========== PHASE 3: Finalization ==========
        if building_mode:
            # Create ID child element
            self.id = Identifier(value=self.value, schemeID=self.schemeID)

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        """
        PartyIdentification doesn't serialize any direct fields as XML attributes.

        All XML output comes from the id child element (cbc:ID) mapped in class_name_to_attr.
        The value, schemeID, and iso6523 fields are internal and used for:
        - Building the id element
        - Extracting from the id element during parsing
        - Comparison and deduplication (__eq__, __hash__)

        Returns:
            Empty list - no direct fields should be XML attributes
        """
        return []

    def __eq__(self, other: object) -> bool:
        """
        Compare identifiers accounting for dual representation.

        9925:be0867709540 == BE:VAT:BE0867709540 (same scheme, case-insensitive value)

        Uses child Identifier's schemeID as canonical value after __post_init__.
        """
        if not isinstance(other, PartyIdentification):
            return False

        # Use child Identifier's schemeID as canonical value (handles extraction failures)
        self_scheme = self.id.schemeID if self.id else self.schemeID
        other_scheme = other.id.schemeID if other.id else other.schemeID

        # Same scheme (case-insensitive value)
        if self_scheme == other_scheme:
            return self.value.lower() == other.value.lower()

        # Different schemes - check if equivalent via iso6523
        if self.iso6523 and other.iso6523:
            if self.iso6523 == other.iso6523:
                return self.value.lower() == other.value.lower()

        return False

    def __hash__(self) -> int:
        """
        Hash for deduplication in sets and dicts.

        Uses child Identifier's schemeID as canonical value after __post_init__.
        """
        # Use child Identifier's schemeID as canonical value (handles extraction failures)
        scheme_for_hash = self.id.schemeID if self.id else self.schemeID
        return hash((self.value.lower(), scheme_for_hash))

    def deserialize(self) -> dict:
        """
        Deserialize party identification to Party attributes.

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
        if scheme.identifier_type == 'vat':
            return {'vat': self.value}
        elif scheme.identifier_type == 'registration':
            return {'registration': self.value}
        else:
            # Other types go to peppol_participant_ids
            return {'peppol_participant_ids': [f'{self.schemeID}:{self.value.lower()}']}


@dataclass
class PartyTaxScheme(CacMixin, BaseElement):
    """
    UBL cac:PartyTaxScheme - Party's tax registration.

    Represents a party's registration with a tax authority (typically VAT).

    Attributes:
        company_id: Tax registration number (VAT number, serializes as cbc:CompanyID)
        tax_scheme: Tax scheme (defaults to VAT)
    """

    company_id: CompanyID
    tax_scheme: TaxScheme = field(default_factory=TaxScheme, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {'CompanyID': 'company_id', 'TaxScheme': 'tax_scheme'}

    def deserialize(self) -> dict:
        """
        Deserialize party tax scheme to Party attributes.

        Returns:
            dict with 'vat' key
        """
        if self.company_id:
            return {'vat': self.company_id.value}
        return {}


@dataclass
class PartyLegalEntity(CacMixin, BaseElement):
    """
    UBL cac:PartyLegalEntity - Party's legal entity information.

    Represents legal registration information for the party.

    Attributes:
        registration_name: Legal registered name (CBC element)
        company_id: Legal registration number (enterprise/company number, serializes as cbc:CompanyID)
    """

    registration_name: RegistrationName
    company_id: CompanyID | None = field(default=None, kw_only=True)

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'RegistrationName': 'registration_name',
        'CompanyID': 'company_id',
    }

    def deserialize(self) -> dict:
        """
        Deserialize party legal entity to Party attributes.

        Returns:
            dict with 'registration' key if company_id exists
        """
        if self.company_id:
            return {'registration': self.company_id.value}
        return {}


@dataclass
class Party(CacMixin, BaseElement):
    """
    UBL cac:Party - Business party (supplier or customer).

    Automatically generates all applicable PEPPOL identifiers from country,
    VAT, and registration data using PEPPOL v9.4 schemes.

    Attributes:
        name: Party legal/trading name
        country_code: ISO 3166-1 alpha-2 country code
        postal_address: Full postal address (REQUIRED)
        vat: VAT number (raw, will be extracted/validated)
        registration: Registration/enterprise number (raw, will be extracted)
        contact: Contact information
        website_uri: Website URL
        peppol_participant_ids: PEPPOL participant IDs (format: "iso6523:value")

    Generated Properties:
        all_identifiers: All applicable party identifiers (auto-generated)
        endpoint_id: First identifier (used for PEPPOL routing)
        party_identification_list: All identifiers as PartyIdentification list
        party_tax_scheme: Tax registration (if VAT available)
        party_legal_entity: Legal entity info (if registration available)

    Examples:
        >>> # Belgium party with VAT only → 2 identifiers
        >>> party = Party(
        ...     name="P4X SA",
        ...     country_code="BE",
        ...     postal_address=address,
        ...     vat="BE0867709540"
        ... )
        >>> len(party.all_identifiers)
        2

        >>> # Netherlands party with VAT + KVK → 4 identifiers
        >>> party = Party(
        ...     name="Squads B.V.",
        ...     country_code="NL",
        ...     postal_address=address,
        ...     vat="NL855934682B01",
        ...     registration="kvk: 64985636"
        ... )
        >>> len(party.all_identifiers)
        4
    """

    postal_address: PostalAddress | None = field(default=None, kw_only=True)
    name: str | None = field(default=None, kw_only=True)
    country_code: str | None = field(default=None, kw_only=True)
    vat: str | None = field(default=None, kw_only=True)
    registration: str | None = field(default=None, kw_only=True)
    contact: Contact | None = field(default=None, kw_only=True)
    website_uri: str | None = field(default=None, kw_only=True)
    peppol_participant_ids: list[str] = field(default_factory=list, kw_only=True)

    # Internal: party name wrapper for XML
    party_name: PartyName | None = field(default=None, repr=False)

    # InitVars for XML deserialization (values from XML that get deserialized in __post_init__)
    endpoint_id: InitVar[EndpointID | None] = None
    party_identification_list: InitVar[list[PartyIdentification] | None] = None
    party_tax_scheme: InitVar[PartyTaxScheme | None] = None
    party_legal_entity: InitVar[PartyLegalEntity | None] = None

    class_name_to_attr: ClassVar[dict[str, str]] = {
        'EndpointID': 'endpoint_id',
        'PartyIdentification': 'party_identification_list',
        'PartyName': 'party_name',
        'PostalAddress': 'postal_address',
        'PartyTaxScheme': 'party_tax_scheme',
        'PartyLegalEntity': 'party_legal_entity',
        'Contact': 'contact',
    }

    # Priority order for InitVars (reversed in __post_init__, so last = highest priority)
    init_vars_priority: ClassVar[list[str]] = [
        'party_tax_scheme',  # Hightest priority, gets called last, overwrites others
        'party_legal_entity',
        'party_identification_list',
        'endpoint_id',  # Lowest priority, overwritten by others (if any)
    ]

    @classmethod
    def get_init_fields(cls):
        return super().get_init_fields() | {
            'endpoint_id',
            'party_identification_list',
            'party_tax_scheme',
            'party_legal_entity',
        }

    def __post_init__(
        self,
        endpoint_id: EndpointID | None,
        party_identification_list: list[PartyIdentification] | None,
        party_tax_scheme: PartyTaxScheme | None,
        party_legal_entity: PartyLegalEntity | None,
    ) -> None:
        """Extract name and country_code if needed, then validate identifiers."""
        # Delegate InitVar deserialization to base class
        self._process_init_vars(
            endpoint_id=endpoint_id,
            party_identification_list=party_identification_list,
            party_tax_scheme=party_tax_scheme,
            party_legal_entity=party_legal_entity,
        )

        # Explicitly NOT sending init_vars as those will all be properties
        # that cannot be type_casted
        self._super_post_init(super())

        # Extract name from party_name if parsing from XML
        if self.name is None:
            if self.party_name and hasattr(self.party_name, 'name'):
                self.name = self.party_name.name
            else:
                raise ValidationError('Party: name must be provided or derivable from PartyName')

        # Create PartyName wrapper for XML serialization if not already set
        if self.party_name is None:
            self.party_name = PartyName(self.name)

        # Derive country_code from postal_address if not provided
        if self.country_code is None and self.postal_address and self.postal_address.country:
            self.country_code = str(self.postal_address.country.identification_code)

        # Note: We don't validate identifiers here anymore
        # Minimal UBL documents (like UBL-Invoice-2.1-Example-Trivial.xml) may have
        # parties with only a name and no identifiers, which is valid UBL

    @property
    def all_identifiers(self) -> list[PartyIdentification]:
        """
        Auto-generate ALL applicable identifiers.

        Logic:
            1. Generate from VAT → both scheme_id and iso6523 formats
            2. Generate from registration → both formats
            3. Apply peppol_ids precedence:
               - peppol_ids take precedence for iso6523 format
               - Compare generated vs peppol, warn if different
               - Keep scheme_id format from VAT/registration

        Returns:
            Deduplicated list of PartyIdentification objects, or empty list if no country_code
        """
        # Can't generate identifiers without country code
        if not self.country_code:
            return []

        from ..identifiers import generate_all_with_precedence

        return generate_all_with_precedence(
            country_code=self.country_code,
            vat=self.vat,
            registration=self.registration,
            peppol_participant_ids=self.peppol_participant_ids,
        )

    @property
    def endpoint_id(self):
        """
        First identifier (used for PEPPOL routing endpoint).

        Returns:
            EndpointID for cbc:EndpointID element, or None if no identifiers
        """
        from .basic_components import EndpointID

        identifiers = self.all_identifiers
        if not identifiers:
            return None

        first = identifiers[0]
        return EndpointID(value=first.value, schemeID=first.schemeID)

    @property
    def party_identification_list(self) -> list[PartyIdentification]:
        """
        First identifier as PartyIdentification list.

        PEPPOL BIS 3.0 (UBL-SR-16) requires only ONE buyer/seller party identification.
        PEPPOL/CEN BR-CL-10 requires schemeID in range 0002-0240 for PartyIdentification.

        Returns:
            List with single PartyIdentification object:
            - In PEPPOL mode: First identifier with schemeID in range 0002-0240
            - Standard mode: First identifier from all_identifiers
            Empty list if no suitable identifiers found
        """
        from ..context import is_peppol_mode

        identifiers = self.all_identifiers
        if not identifiers:
            return []

        # In PEPPOL mode, filter for CEN-approved codes (0002-0240)
        if is_peppol_mode():
            for identifier in identifiers:
                scheme_id = identifier.schemeID
                # Check if schemeID is a 4-digit number in range 0002-0240
                if scheme_id and scheme_id.isdigit() and len(scheme_id) == 4:
                    code = int(scheme_id)
                    if 2 <= code <= 240:
                        return [identifier]

            # No approved identifier found - return empty list
            # This will prevent BR-CL-10 errors rather than using invalid code
            return []

        # Standard mode: return first identifier
        return [identifiers[0]]

    @property
    def party_tax_scheme(self) -> PartyTaxScheme | None:
        """
        Tax registration scheme (if VAT available).

        PEPPOL BIS 3.0 / CEN EN16931:
        - UBL-CR-652: CompanyID should not include schemeID attribute
        - In PEPPOL mode, omit schemeID and use plain VAT value

        Returns:
            PartyTaxScheme with or without schemeID based on mode
        """
        from ..context import is_peppol_mode

        if self.vat and self.country_code:
            if is_peppol_mode():
                # PEPPOL/CEN UBL-CR-652: No schemeID on PartyTaxScheme/CompanyID
                return PartyTaxScheme(
                    company_id=CompanyID(value=self.vat),
                )
            else:
                # Standard mode: Include schemeID
                from ..identifiers import get_schemes_for_country

                vat_schemes = [
                    s
                    for s in get_schemes_for_country(self.country_code)
                    if s.identifier_type == 'vat' and s.state == 'active'
                ]

                if vat_schemes:
                    return PartyTaxScheme(
                        company_id=CompanyID(value=self.vat, schemeID=vat_schemes[0].iso6523),
                    )

        return None

    @property
    def party_legal_entity(self) -> PartyLegalEntity | None:
        """
        Legal entity information.

        PEPPOL BIS 3.0 (BR-CL-11) requires numeric ISO 6523 ICD code for schemeID.

        Returns:
            PartyLegalEntity with registration name and optional company ID
        """
        company_id = None
        if self.registration and self.country_code:
            # Use first registration scheme for company_id (ISO 6523 numeric code)
            from ..identifiers import get_schemes_for_country

            reg_schemes = [
                s
                for s in get_schemes_for_country(self.country_code)
                if s.identifier_type == 'registration' and s.state == 'active'
            ]
            if reg_schemes:
                company_id = CompanyID(value=self.registration, schemeID=reg_schemes[0].iso6523)

        return PartyLegalEntity(registration_name=self.name, company_id=company_id)

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        """
        Party doesn't serialize any direct fields as XML attributes.

        All XML output comes from computed properties (endpoint_id,
        party_identification_list, postal_address, party_tax_scheme,
        party_legal_entity, contact) mapped in class_name_to_attr.

        Returns:
            Empty list - no direct fields should be XML attributes
        """
        return []


@dataclass
class AccountingSupplierParty(CacMixin, BaseElement):
    """
    UBL cac:AccountingSupplierParty - Wrapper for supplier party.

    This is a wrapper component that contains a Party child element
    representing the invoice supplier (seller).

    Attributes:
        party: The supplier party details
    """

    party: Party

    class_name_to_attr: ClassVar[dict[str, str]] = {'Party': 'party'}


@dataclass
class AccountingCustomerParty(CacMixin, BaseElement):
    """
    UBL cac:AccountingCustomerParty - Wrapper for customer party.

    This is a wrapper component that contains a Party child element
    representing the invoice customer (buyer).

    Attributes:
        party: The customer party details
    """

    party: Party

    class_name_to_attr: ClassVar[dict[str, str]] = {'Party': 'party'}
