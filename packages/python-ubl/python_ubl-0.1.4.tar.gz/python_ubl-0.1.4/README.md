# python_ubl

A pure Python library for generating and parsing UBL 2.1 XML documents with full PEPPOL BIS Billing 3.0 compliance.

## Status: Alpha (v0.1.3)

This library is in early development. The API is not yet stable and may change in future releases.

## Features

- **Pure Python**: No Django dependency required (optional Django integration available)
- **UBL 2.1 Support**: Generate and parse invoices and credit notes
- **PEPPOL Compliance**: Full support for PEPPOL BIS Billing 3.0
- **Dataclass-based**: Type-safe, immutable-by-convention data structures
- **Bidirectional**: Generate UBL XML from Python objects, parse UBL XML into Python objects
- **Automatic Identifier Generation**: Auto-generate PEPPOL participant identifiers from VAT/registration numbers
- **100 PEPPOL Schemes**: Supports all PEPPOL v9.4 participant identifier schemes

## Installation

```bash
pip install python_ubl
```

## Quick Start

```python
from ubl.models import Invoice, Party, InvoiceLine, Amount, Quantity, PostalAddress
from datetime import date

# Create a simple invoice
invoice = Invoice(
    id="INV-001",
    issue_date=date.today(),
    supplier=Party(
        name="My Company",
        vat="BE0123456789",
        country_code="BE",
        postal_address=PostalAddress(
            street_name="Main Street 1",
            city_name="Brussels",
            postal_zone="1000",
            country="BE"  # Smart casting: string -> Country object
        )
    ),
    customer=Party(...),
    lines=[
        InvoiceLine(
            id="1",
            invoiced_quantity=Quantity(value=10, unitCode="EA"),
            line_extension_amount=Amount(value=100.00),
            item=Item(name="Product A"),
            price=Price(price_amount=Amount(value=10.00))
        )
    ]
)

# Export to XML
xml_bytes = invoice.to_xml()

# Parse from XML
invoice = Invoice.from_xml(xml_bytes)
```

## PEPPOL Compliance Mode

For PEPPOL BIS 3.0 / CEN EN16931 compliance, use the `peppol_context()` context manager:

```python
from ubl import peppol_context
from ubl.models import Invoice

# Generate PEPPOL-compliant UBL XML
with peppol_context():
    invoice = Invoice(...)
    xml = invoice.to_xml_string()
```

When active, PEPPOL mode automatically:

- **Removes forbidden elements**: LineCountNumeric, TaxSubtotal/Percent, InvoiceLine/TaxTotal, FinancialInstitution
- **Removes forbidden attributes**: listID, schemeName, listAgencyID, unitCodeListID
- **Filters identifiers**: Uses only CEN-approved codes (0002-0240) for PartyIdentification
- **Normalizes financial IDs**: IBAN/BIC values are prefixed without schemeID attribute
- **Simplifies tax schemes**: Removes schemeID from PartyTaxScheme CompanyID (UBL-CR-652)

This ensures generated XML passes all CEN EN16931 and PEPPOL BIS 3.0 validation rules without manual adjustments.

## Requirements

- Python 3.11+
- lxml >= 4.9.0
- python-dateutil >= 2.8.0

## Development Status

Currently implemented:
- ✅ Basic components (Amount, Quantity, Identifier, Code)
- ✅ Aggregate components (Party, Address, Tax, Payment)
- ✅ PEPPOL identifier generation (100 schemes)
- ✅ Document models (Invoice, CreditNote)
- ✅ Bidirectional XML serialization
- ✅ Official UBL 2.1 example validation

Coming soon:
- 🚧 XSD schema validation
- 🚧 Business rules validation
- 🚧 Django integration module
- 🚧 Comprehensive documentation
- 🚧 Public repository and issue tracker

## License

MIT License - see [LICENSE](LICENSE) file for details.

## About

This library is developed by LevIT SC as part of their PEPPOL e-invoicing integration project.
