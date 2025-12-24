"""
UBL Document Models - Invoice and CreditNote

This module implements the root document classes for UBL 2.1:
- BaseDocument: Shared logic for all document types
- Invoice: UBL Invoice (type code 380)
- CreditNote: UBL CreditNote (type code 381)
"""

from dataclasses import InitVar, dataclass, field
from decimal import Decimal
from typing import ClassVar

from ..constants import NAMESPACES
from ..exceptions import ValidationError
from .aggregate_components import (
    AccountingCustomerParty,
    AccountingSupplierParty,
    InvoiceLine,
    LegalMonetaryTotal,
    Party,
    PaymentMeans,
    TaxTotal,
)
from .basic_components import (
    CustomizationID,
    DocumentCurrencyCode,
    DueDate,
    Identifier,
    InvoiceTypeCode,
    IssueDate,
    LineCountNumeric,
    ProfileID,
    TaxCurrencyCode,
    UBLVersionID,
    UUID,
)
from .common import BaseElement, AutoCastDataclassMixin


@dataclass
class BaseDocument(BaseElement, AutoCastDataclassMixin):
    """
    Base class for Invoice and CreditNote.

    Contains all shared fields and logic. Only difference between
    Invoice and CreditNote is the document_type_code property.

    Attributes:
        id: Invoice/credit note number
        issue_date: Date when document was issued
        supplier: Accounting supplier party (seller)
        customer: Accounting customer party (buyer)
        lines: Document lines (at least one required)
        uuid: Optional document UUID for tracking
        due_date: Optional payment due date
        document_currency_code: ISO 4217 currency code (default: EUR)
        tax_currency_code: Optional tax currency code
        line_count_numeric: Number of lines (auto-calculated if not provided)
        payment_means: List of payment methods
        tax_totals: List of tax totals (at least one required for valid UBL)
        legal_monetary_total: Document monetary totals
        customization_id: UBL customization profile
        profile_id: Business process profile
    """

    # Required fields (CBC/CAC objects)
    id: Identifier
    issue_date: IssueDate

    # Party fields - optional to support both building and parsing modes
    # Building mode: provide supplier/customer directly
    # Parsing mode: these are populated from accounting_supplier_party/accounting_customer_party in __post_init__
    supplier: Party | None = None
    customer: Party | None = None
    lines: list[InvoiceLine] = field(default_factory=list)

    # Optional fields (CBC objects)
    uuid: UUID | None = None
    due_date: DueDate | None = None
    document_currency_code: DocumentCurrencyCode | None = None  # Default EUR set in __post_init__
    tax_currency_code: TaxCurrencyCode | None = None

    # Aggregate components
    payment_means: list[PaymentMeans] = field(default_factory=list)

    # Wrapper party components - populated when parsing XML, generated as properties when building
    accounting_supplier_party: AccountingSupplierParty | None = field(default=None, kw_only=True, repr=False)
    accounting_customer_party: AccountingCustomerParty | None = field(default=None, kw_only=True, repr=False)

    # Note: tax_totals, legal_monetary_total, line_count_numeric are now @property (computed)

    # Metadata for XML serialization (will be set in __post_init__)
    url: str = field(default='', init=False, repr=False)
    prefix: str = field(default='', init=False, repr=False)

    # Base mapping from XML element names to property/field names (ClassVar for parsing)
    _base_class_name_to_attr: ClassVar[dict[str, str]] = {
        'UBLVersionID': 'ubl_version_id',
        'CustomizationID': 'customization_id',
        'ProfileID': 'profile_id',
        'ID': 'id',
        'UUID': 'uuid',
        'IssueDate': 'issue_date',
        'DueDate': 'due_date',
        'InvoiceTypeCode': 'invoice_type_code',
        'DocumentCurrencyCode': 'document_currency_code',
        'TaxCurrencyCode': 'tax_currency_code',
        'LineCountNumeric': 'line_count_numeric',
        'AccountingSupplierParty': 'accounting_supplier_party',  # Parsed to private field
        'AccountingCustomerParty': 'accounting_customer_party',  # Parsed to private field
        'PaymentMeans': 'payment_means',
        'TaxTotal': 'tax_totals',
        'LegalMonetaryTotal': 'legal_monetary_total',
        'InvoiceLine': 'lines',
        'CreditNoteLine': 'lines',
    }

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """
        Get element name to attribute mapping, filtered for PEPPOL mode.

        PEPPOL/CEN UBL-CR rules prohibit certain elements:
        - UBL-CR-011: LineCountNumeric should not be included

        Returns:
            Filtered mapping dictionary
        """
        from ..context import is_peppol_mode

        mapping = self._base_class_name_to_attr.copy()

        if is_peppol_mode():
            # UBL-CR-011: Remove LineCountNumeric
            mapping.pop('LineCountNumeric', None)

        return mapping

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        return [
            name
            for name in super()._get_property_attr_names()
            if name not in ['customer', 'supplier']
        ]

    @property
    def element_name(self) -> str:
        """Return document type name (Invoice or CreditNote)."""
        raise NotImplementedError('Must be implemented in subclass')

    @property
    def document_type_code(self) -> str:
        """
        Return UBL document type code.

        Must be implemented in subclass:
        - Invoice: "380"
        - CreditNote: "381"
        """
        raise NotImplementedError('Must be implemented in subclass')

    # Constant properties (immutable, can be overridden in subclasses)
    @property
    def ubl_version_id(self) -> UBLVersionID:
        """Return UBL version identifier (always 2.1)."""
        from .basic_components import UBLVersionID

        return UBLVersionID()

    @property
    def customization_id(self) -> CustomizationID:
        """Return customization profile identifier."""
        from .basic_components import CustomizationID

        return CustomizationID(value='urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0')

    @property
    def profile_id(self) -> ProfileID:
        """Return business process profile identifier."""
        from .basic_components import ProfileID

        return ProfileID(value='urn:fdc:peppol.eu:2017:poacc:billing:01:1.0')

    @property
    def invoice_type_code(self) -> InvoiceTypeCode:
        """Return invoice type code (380=invoice, 381=credit note)."""
        from .basic_components import InvoiceTypeCode

        return InvoiceTypeCode(value=self.document_type_code)

    # Computed properties
    @property
    def line_count_numeric(self) -> LineCountNumeric:
        """Return line count (computed from number of lines)."""
        from .basic_components import LineCountNumeric

        return LineCountNumeric(value=len(self.lines))

    @property
    def tax_totals(self) -> list[TaxTotal]:
        """
        Return tax totals (computed by grouping taxes from lines).

        Groups line-level taxes by tax category and rate, creating
        TaxTotal with TaxSubtotals for each unique tax.
        """
        from collections import defaultdict

        from .aggregate_components import TaxSubtotal, TaxTotal
        from .basic_components import TaxableAmount, TaxAmount, quantize_to_max_precision

        # Collect all source amounts for precision detection
        all_source_amounts = []

        # Group taxes by category and rate
        tax_groups = defaultdict(lambda: {'taxable': Decimal('0'), 'tax': Decimal('0'), 'category': None, 'sources': []})

        for line in self.lines:
            if line.tax_total:
                for subtotal in line.tax_total.tax_subtotals:
                    key = (subtotal.tax_category.id, subtotal.percent.value)
                    tax_groups[key]['taxable'] += subtotal.taxable_amount.value
                    tax_groups[key]['tax'] += subtotal.tax_amount.value
                    tax_groups[key]['category'] = subtotal.tax_category
                    # Track source amounts for precision
                    tax_groups[key]['sources'].extend([subtotal.taxable_amount.value, subtotal.tax_amount.value])
                    all_source_amounts.extend([subtotal.taxable_amount.value, subtotal.tax_amount.value])

        # Create TaxSubtotals with preserved precision
        subtotals = []
        for (cat_id, percent_value), data in tax_groups.items():
            # Quantize to max precision of source amounts for this group
            taxable = quantize_to_max_precision(data['taxable'], *data['sources'])
            tax = quantize_to_max_precision(data['tax'], *data['sources'])

            subtotals.append(
                TaxSubtotal(
                    taxable_amount=TaxableAmount(value=taxable),
                    tax_amount=TaxAmount(value=tax),
                    percent=percent_value,
                    tax_category=data['category'],
                )
            )

        # Return single TaxTotal with all subtotals
        if subtotals:
            total_tax = sum(st.tax_amount.value for st in subtotals)
            # Quantize total to max precision of all source amounts
            total_tax = quantize_to_max_precision(total_tax, *all_source_amounts)
            return [TaxTotal(tax_amount=TaxAmount(value=total_tax), tax_subtotals=subtotals)]
        return []

    @property
    def legal_monetary_total(self) -> LegalMonetaryTotal:
        """
        Return legal monetary total (computed from lines and taxes).

        Calculates:
        - LineExtensionAmount: sum of all line totals
        - TaxExclusiveAmount: same as LineExtensionAmount (no allowances/charges)
        - TaxInclusiveAmount: TaxExclusiveAmount + total taxes
        - PayableAmount: final amount due
        """

        from .aggregate_components import LegalMonetaryTotal
        from .basic_components import LineExtensionAmount, PayableAmount, TaxExclusiveAmount, TaxInclusiveAmount, quantize_to_max_precision

        # Collect all source amounts for precision detection
        line_amounts = [line.line_extension_amount.value for line in self.lines]

        # Sum line totals
        line_total = sum(line_amounts)

        # Quantize line_total to max precision of line amounts
        line_total = quantize_to_max_precision(line_total, *line_amounts)

        # Sum taxes (tax_totals already quantized)
        tax_amounts = [tt.tax_amount.value for tt in self.tax_totals]
        tax_total = sum(tax_amounts) if tax_amounts else Decimal('0')

        # Calculate totals with precision from both line and tax amounts
        all_amounts = line_amounts + tax_amounts
        total_with_tax = line_total + tax_total
        total_with_tax = quantize_to_max_precision(total_with_tax, *all_amounts)

        return LegalMonetaryTotal(
            line_extension_amount=LineExtensionAmount(value=line_total),
            tax_exclusive_amount=TaxExclusiveAmount(value=line_total),
            tax_inclusive_amount=TaxInclusiveAmount(value=total_with_tax),
            payable_amount=PayableAmount(value=total_with_tax),
        )

    def __post_init__(self):
        """Initialize and validate document on creation."""

        # First: trigger type casting through mixin chain
        self._super_post_init(super())

        # Parsing mode detection: if wrapper parties are populated, extract the Party objects
        for attr, WrapperClass in (('customer', AccountingCustomerParty), ('supplier', AccountingSupplierParty)):
            if getattr(self, f'accounting_{attr}_party') is not None and getattr(self, attr) is None:
                setattr(self, attr, getattr(self, f'accounting_{attr}_party').party)
            elif getattr(self, attr) is not None and getattr(self, f'accounting_{attr}_party') is None:
                setattr(self, f'accounting_{attr}_party', WrapperClass(party=getattr(self, attr)))
            elif getattr(self, attr) is None and getattr(self, f'accounting_{attr}_party') is None:
                raise ValueError(f'{attr} is required')

        # Auto-set document namespace based on type (invoice or creditnote)
        if not self.url:
            self.url = NAMESPACES[self.element_name.lower()]

        # Set default document currency if not provided
        if self.document_currency_code is None:
            from .basic_components import DocumentCurrencyCode

            self.document_currency_code = DocumentCurrencyCode(value='EUR')

        # Validate at least one line
        if not self.lines:
            raise ValidationError(f'{self.element_name} must have at least one line')

    def to_xml_string(self, pretty_print: bool = True) -> str:
        """
        Generate UBL XML as string.

        Args:
            pretty_print: Whether to format XML with indentation

        Returns:
            XML string with declaration
        """
        from lxml import etree

        xml = self.to_xml()
        return etree.tostring(
            xml, encoding='UTF-8', xml_declaration=True, pretty_print=pretty_print
        ).decode('utf-8')

    @classmethod
    def from_xml_string(cls, xml_string: str) -> 'BaseDocument':
        """
        Parse UBL XML string into document object.

        Args:
            xml_string: UBL XML as string

        Returns:
            Document instance (Invoice or CreditNote)
        """
        from lxml import etree

        root = etree.fromstring(xml_string.encode('utf-8'))
        return cls.from_xml(root)


@dataclass
class Invoice(BaseDocument):
    """
    UBL Invoice (type code 380).

    Inherits all fields and logic from BaseDocument.
    Only difference is document_type_code and element_name.
    """

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """Get element mapping, excluding CreditNoteLine."""
        mapping = super().class_name_to_attr
        return {k: v for k, v in mapping.items() if k != 'CreditNoteLine'}

    @property
    def element_name(self) -> str:
        """Return 'Invoice'."""
        return 'Invoice'

    @property
    def document_type_code(self) -> str:
        """Return invoice type code (380)."""
        return '380'


@dataclass
class CreditNote(BaseDocument):
    """
    UBL CreditNote (type code 381).

    Inherits all fields and logic from BaseDocument.
    Only difference is document_type_code and element_name.

    Note: In UBL, CreditNote lines use 'CreditedQuantity' instead of
    'InvoicedQuantity', but this library uses InvoiceLine for both
    document types for simplicity. The XML serialization handles
    the correct element names.
    """

    @property
    def class_name_to_attr(self) -> dict[str, str]:
        """Get element mapping, excluding InvoiceLine."""
        mapping = super().class_name_to_attr
        return {k: v for k, v in mapping.items() if k != 'InvoiceLine'}

    @property
    def element_name(self) -> str:
        """Return 'CreditNote'."""
        return 'CreditNote'

    @property
    def document_type_code(self) -> str:
        """Return credit note type code (381)."""
        return '381'
