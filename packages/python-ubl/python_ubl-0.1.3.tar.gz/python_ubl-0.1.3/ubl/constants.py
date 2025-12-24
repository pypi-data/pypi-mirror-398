"""
Constants for UBL XML generation and parsing.

This module contains namespace URLs, code lists, and other constant values
used throughout the UBL library.
"""

# UBL 2.1 Namespace URLs
NAMESPACES = {
    "invoice": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "creditnote": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ccts": "urn:un:unece:uncefact:documentation:2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
    "udt": "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
}

# Default UBL version
UBL_VERSION_ID = "2.1"

# Default PEPPOL BIS Billing 3.0 profiles
DEFAULT_CUSTOMIZATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
DEFAULT_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

# Tax category codes (UNCL5305)
TAX_CATEGORY_CODES = {
    "S": "Standard rate",
    "Z": "Zero rated",
    "E": "Exempt from tax",
    "AE": "VAT Reverse Charge",
    "G": "Free export item, tax not charged",
    "K": "VAT exempt for EEA intra-community supply of goods and services",
    "ZZ": "Not subject to VAT",
}

# Payment means codes (UNCL4461)
PAYMENT_MEANS_CODES = {
    "1": "Instrument not defined",
    "30": "Credit transfer",
    "31": "Debit transfer",
    "42": "Payment to bank account",
    "48": "Bank card",
    "49": "Direct debit",
}

# Invoice type codes (UNCL1001)
INVOICE_TYPE_CODES = {
    "380": "Commercial invoice",
    "381": "Credit note",
    "384": "Corrected invoice",
    "389": "Self-billed invoice",
    "751": "Invoice information for accounting purposes",
}

# Default currency code (ISO 4217)
DEFAULT_CURRENCY_CODE = "EUR"

# Default unit codes (UNECERec20)
DEFAULT_UNIT_CODE = "EA"  # Each

# Country codes list ID
COUNTRY_CODE_LIST_ID = "ISO3166-1:Alpha2"
COUNTRY_CODE_LIST_AGENCY_ID = "6"

# Tax scheme
DEFAULT_TAX_SCHEME_ID = "VAT"
TAX_SCHEME_ID_LIST_ID = "UN/ECE 5153"
TAX_SCHEME_ID_LIST_AGENCY_ID = "6"

# Unit code list
UNIT_CODE_LIST_ID = "UNECERec20"

# Tax category list
TAX_CATEGORY_LIST_ID = "UNCL5305"
TAX_CATEGORY_LIST_AGENCY_ID = "6"

# Payment means code list
PAYMENT_MEANS_CODE_LIST_ID = "UNCL4461"
PAYMENT_MEANS_CODE_LIST_AGENCY_ID = "6"
