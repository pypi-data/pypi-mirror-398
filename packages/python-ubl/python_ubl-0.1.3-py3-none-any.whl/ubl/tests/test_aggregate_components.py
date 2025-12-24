"""
Tests for UBL aggregate components (CAC elements).
"""

import unittest
from datetime import date
from decimal import Decimal

from faker import Faker
from lxml import etree

from ubl.exceptions import ValidationError

# Faker instances
fake_be = Faker('nl_BE')

# Reusable test data
BIC_CODE = fake_be.swift8()
IBAN = fake_be.iban()
COMPANY_NAME = fake_be.company()
from ubl.models.aggregate_components import (
    Contact,
    Country,
    FinancialInstitution,
    FinancialInstitutionBranch,
    InvoiceLine,
    Item,
    LegalMonetaryTotal,
    PayeeFinancialAccount,
    PaymentMeans,
    PostalAddress,
    Price,
    SellersItemIdentification,
    TaxCategory,
    TaxScheme,
    TaxSubtotal,
    TaxTotal,
)
from ubl.models.basic_components import (
    Identifier,
    InvoicedQuantity,
    LineExtensionAmount,
    Name,
    PayableAmount,
    Percent,
    PriceAmount,
    TaxableAmount,
    TaxAmount,
    TaxExclusiveAmount,
    TaxInclusiveAmount,
)


class TestCountry(unittest.TestCase):
    """Tests for Country component."""

    def test_create_country(self):
        """Test country creation."""
        country = Country(identification_code="BE")
        # identification_code is now an IdentificationCode object with ValueStrMixin
        self.assertEqual(str(country.identification_code), "BE")

    def test_country_to_xml(self):
        """Test country XML serialization."""
        country = Country(identification_code="NL")
        xml = country.to_xml()
        self.assertEqual(etree.QName(xml).localname, "Country")
        # XML should have IdentificationCode child element
        id_code = xml.find(".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode")
        self.assertIsNotNone(id_code)
        self.assertEqual(id_code.text, "NL")


class TestContact(unittest.TestCase):
    """Tests for Contact component."""

    def test_create_contact_full(self):
        """Test contact with all fields."""
        contact = Contact(
            electronic_mail="test@example.com",
            telephone="+32 2 123 45 67",
            name="John Doe",
        )
        self.assertEqual(contact.electronic_mail.value, "test@example.com")
        self.assertEqual(contact.telephone.value, "+32 2 123 45 67")
        self.assertEqual(contact.name.value, "John Doe")

    def test_create_contact_minimal(self):
        """Test contact with no fields (all optional)."""
        contact = Contact()
        self.assertIsNone(contact.electronic_mail)
        self.assertIsNone(contact.telephone)
        self.assertIsNone(contact.name)


class TestTaxScheme(unittest.TestCase):
    """Tests for TaxScheme component."""

    def test_create_tax_scheme_default(self):
        """Test tax scheme with defaults."""
        scheme = TaxScheme()
        self.assertIsInstance(scheme.id, Identifier)
        self.assertEqual(scheme.id.value, "VAT")
        self.assertEqual(scheme.id.schemeID, "UN/ECE 5153")

    def test_create_tax_scheme_custom(self):
        """Test tax scheme with custom values."""
        scheme = TaxScheme(id=Identifier(value="GST", schemeID="UN/ECE 5153"))
        self.assertIsInstance(scheme.id, Identifier)
        self.assertEqual(scheme.id.value, "GST")


class TestPostalAddress(unittest.TestCase):
    """Tests for PostalAddress component."""

    def test_create_address_basic(self):
        """Test postal address creation."""
        address = PostalAddress(
            street_name="Rue de la Loi 1",
            city_name="Brussels",
            postal_zone="1000",
            country="BE",
        )
        self.assertEqual(str(address.street_name), "Rue de la Loi 1")
        self.assertEqual(str(address.city_name), "Brussels")
        self.assertEqual(str(address.postal_zone), "1000")
        self.assertEqual(str(address.country.identification_code), "BE")

    def test_address_smart_type_casting(self):
        """Test that country string is auto-cast to Country component."""
        address = PostalAddress(
            street_name="Main St",
            city_name="Amsterdam",
            postal_zone="1012",
            country="NL",
        )
        self.assertIsInstance(address.country, Country)
        self.assertEqual(str(address.country.identification_code), "NL")

    def test_address_with_optional_fields(self):
        """Test address with optional fields."""
        address = PostalAddress(
            street_name="Main St",
            city_name="Brussels",
            postal_zone="1000",
            country="BE",
            additional_street_name="Building A",
            country_subentity="Brussels Capital",
        )
        self.assertEqual(str(address.additional_street_name), "Building A")
        self.assertEqual(str(address.country_subentity), "Brussels Capital")


class TestFinancialComponents(unittest.TestCase):
    """Tests for financial components."""

    def test_create_financial_institution(self):
        """Test financial institution creation."""
        fi = FinancialInstitution(id=Identifier(value=BIC_CODE, schemeID="BIC"))
        self.assertEqual(fi.id.value, BIC_CODE)
        self.assertEqual(fi.id.schemeID, "BIC")

    def test_create_financial_institution_branch(self):
        """Test branch creation."""
        fi = FinancialInstitution(id=Identifier(value=BIC_CODE, schemeID="BIC"))
        branch = FinancialInstitutionBranch(financial_institution=fi)
        self.assertIs(branch.financial_institution, fi)

    def test_create_payee_financial_account(self):
        """Test payee account creation."""
        fi = FinancialInstitution(id=Identifier(value=BIC_CODE, schemeID="BIC"))
        branch = FinancialInstitutionBranch(financial_institution=fi)
        account = PayeeFinancialAccount(
            id=Identifier(value=IBAN, schemeID=IBAN),
            name=COMPANY_NAME,
            financial_institution_branch=branch,
        )
        self.assertEqual(account.id.value, IBAN)
        self.assertEqual(account.name.value, COMPANY_NAME)
        self.assertIs(account.financial_institution_branch, branch)

    def test_create_payee_account_minimal(self):
        """Test payee account without optional fields."""
        account = PayeeFinancialAccount(id=Identifier(value=IBAN, schemeID=IBAN))
        self.assertIsNone(account.name)
        self.assertIsNone(account.financial_institution_branch)


class TestTaxCategory(unittest.TestCase):
    """Tests for TaxCategory component."""

    def test_create_tax_category_standard(self):
        """Test standard rate tax category."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        self.assertIsInstance(category.id, Identifier)
        self.assertEqual(category.id.value, "S")
        self.assertEqual(category.id.schemeID, "UNCL5305")
        self.assertIsInstance(category.percent, Percent)
        self.assertEqual(category.percent.value, Decimal("21"))
        self.assertIsNone(category.name)

    def test_create_tax_category_with_name(self):
        """Test tax category with name."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21",
            name="TVA sur ventes 21 %"
        )
        self.assertIsInstance(category.name, Name)
        self.assertEqual(category.name.value, "TVA sur ventes 21 %")

    def test_tax_category_validates_code(self):
        """Test that invalid tax codes raise ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            TaxCategory(
                id=Identifier(value="INVALID", schemeID="UNCL5305", schemeAgencyID="6"),
                percent="21"
            )
        self.assertIn("Invalid tax category code", str(cm.exception))

    def test_tax_category_valid_codes(self):
        """Test all valid tax category codes."""
        valid_codes = ["S", "Z", "E", "AE", "G", "K", "ZZ"]
        for code in valid_codes:
            category = TaxCategory(
                id=Identifier(value=code, schemeID="UNCL5305", schemeAgencyID="6"),
                percent="0"
            )
            self.assertEqual(category.id.value, code)

    def test_tax_category_converts_percent(self):
        """Test percent conversion to Decimal via smart casting."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent=21  # int gets cast to Decimal via smart casting
        )
        self.assertIsInstance(category.percent, Percent)
        self.assertEqual(category.percent.value, Decimal("21"))


class TestTaxSubtotal(unittest.TestCase):
    """Tests for TaxSubtotal component."""

    def test_create_tax_subtotal(self):
        """Test tax subtotal creation."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("100")),
            tax_amount=TaxAmount(value=Decimal("21")),
            percent="21",  # Smart cast to Percent
            tax_category=category,
        )
        self.assertEqual(subtotal.taxable_amount.value, Decimal("100"))
        self.assertEqual(subtotal.tax_amount.value, Decimal("21"))
        self.assertIsInstance(subtotal.percent, Percent)
        self.assertEqual(subtotal.percent.value, Decimal("21"))

    def test_tax_subtotal_converts_percent(self):
        """Test percent conversion to Decimal via smart casting."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("100")),
            tax_amount=TaxAmount(value=Decimal("21")),
            percent=21,  # int gets smart cast to Percent
            tax_category=category,
        )
        self.assertIsInstance(subtotal.percent, Percent)
        self.assertEqual(subtotal.percent.value, Decimal("21"))


class TestTaxTotal(unittest.TestCase):
    """Tests for TaxTotal component."""

    def test_create_tax_total_without_subtotals(self):
        """Test tax total without subtotals."""
        total = TaxTotal(tax_amount=TaxAmount(value=Decimal("21")))
        self.assertEqual(total.tax_amount.value, Decimal("21"))
        self.assertEqual(total.tax_subtotals, [])

    def test_create_tax_total_with_subtotals(self):
        """Test tax total with matching subtotals."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("100")),
            tax_amount=TaxAmount(value=Decimal("21")),
            percent=Decimal("21"),
            tax_category=category,
        )
        total = TaxTotal(tax_amount=TaxAmount(value=Decimal("21")), tax_subtotals=[subtotal])
        self.assertEqual(len(total.tax_subtotals), 1)

    def test_tax_total_validates_amounts(self):
        """Test that mismatched amounts raise ValidationError."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("100")),
            tax_amount=TaxAmount(value=Decimal("21")),
            percent=Decimal("21"),
            tax_category=category,
        )
        with self.assertRaises(ValidationError) as cm:
            TaxTotal(
                tax_amount=TaxAmount(value=Decimal("50")),  # Wrong amount
                tax_subtotals=[subtotal],
            )
        self.assertIn("does not match sum of subtotals", str(cm.exception))

    def test_tax_total_multiple_subtotals(self):
        """Test tax total with multiple subtotals."""
        cat1 = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        cat2 = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="6"
        )
        subtotal1 = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("100")),
            tax_amount=TaxAmount(value=Decimal("21")),
            percent=Decimal("21"),
            tax_category=cat1,
        )
        subtotal2 = TaxSubtotal(
            taxable_amount=TaxableAmount(value=Decimal("50")),
            tax_amount=TaxAmount(value=Decimal("3")),
            percent=Decimal("6"),
            tax_category=cat2,
        )
        total = TaxTotal(
            tax_amount=TaxAmount(value=Decimal("24")),
            tax_subtotals=[subtotal1, subtotal2],
        )
        self.assertEqual(len(total.tax_subtotals), 2)


class TestPaymentMeans(unittest.TestCase):
    """Tests for PaymentMeans component."""

    def test_create_payment_means_default(self):
        """Test payment means with defaults."""
        pm = PaymentMeans()
        self.assertEqual(pm.payment_means_code.value, "31")
        self.assertEqual(pm.payment_means_code.listID, "UNCL4461")

    def test_create_payment_means_full(self):
        """Test payment means with all fields."""
        account = PayeeFinancialAccount(id=Identifier(value=IBAN, schemeID=IBAN))
        pm = PaymentMeans(
            payment_means_code="30",
            payment_due_date=date(2025, 1, 15),
            payment_id="+++123/4567/89012+++",
            payee_financial_account=account,
        )
        self.assertEqual(pm.payment_means_code.value, "30")
        self.assertEqual(pm.payment_due_date.value, "2025-01-15")
        self.assertEqual(pm.payment_id.value, "+++123/4567/89012+++")
        self.assertIs(pm.payee_financial_account, account)


class TestPrice(unittest.TestCase):
    """Tests for Price component."""

    def test_create_price(self):
        """Test price creation."""
        price = Price(price_amount=PriceAmount(value=Decimal("10.50")))
        self.assertEqual(price.price_amount.value, Decimal("10.50"))


class TestSellersItemIdentification(unittest.TestCase):
    """Tests for SellersItemIdentification component."""

    def test_create_sellers_item_identification_building_mode(self):
        """Create SellersItemIdentification with value and schemeID (building mode)."""
        sellers_id = SellersItemIdentification(value="PROD-001", schemeID="GTIN")

        self.assertEqual(sellers_id.value, "PROD-001")
        self.assertEqual(sellers_id.schemeID, "GTIN")
        self.assertIsInstance(sellers_id.id, Identifier)
        self.assertEqual(sellers_id.id.value, "PROD-001")
        self.assertEqual(sellers_id.id.schemeID, "GTIN")

    def test_create_sellers_item_identification_no_scheme(self):
        """Create SellersItemIdentification with value only (no scheme)."""
        sellers_id = SellersItemIdentification(value="SIMPLE-CODE")

        self.assertEqual(sellers_id.value, "SIMPLE-CODE")
        self.assertIsNone(sellers_id.schemeID)
        self.assertIsInstance(sellers_id.id, Identifier)
        self.assertEqual(sellers_id.id.value, "SIMPLE-CODE")
        self.assertIsNone(sellers_id.id.schemeID)

    def test_sellers_item_identification_validation_error(self):
        """SellersItemIdentification requires value in building mode."""
        with self.assertRaises(ValidationError) as ctx:
            SellersItemIdentification()

        self.assertIn("value is required", str(ctx.exception))

    def test_sellers_item_identification_to_xml(self):
        """SellersItemIdentification serializes to XML correctly."""
        sellers_id = SellersItemIdentification(value="MENSUEL-INTERNET-PRO-COAX")
        xml_elem = sellers_id.to_xml()

        self.assertEqual(xml_elem.tag, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}SellersItemIdentification")

        # Should contain cbc:ID child
        id_elem = xml_elem.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        self.assertIsNotNone(id_elem)
        self.assertEqual(id_elem.text, "MENSUEL-INTERNET-PRO-COAX")

    def test_sellers_item_identification_from_xml(self):
        """SellersItemIdentification parses from XML correctly (parsing mode)."""
        xml_str = """
        <cac:SellersItemIdentification xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                                        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>MENSUEL-INTERNET-PRO-COAX</cbc:ID>
        </cac:SellersItemIdentification>
        """
        xml_elem = etree.fromstring(xml_str.strip())
        sellers_id = SellersItemIdentification.from_xml(xml_elem)

        self.assertEqual(sellers_id.value, "MENSUEL-INTERNET-PRO-COAX")
        self.assertIsNone(sellers_id.schemeID)
        self.assertIsInstance(sellers_id.id, Identifier)
        self.assertEqual(sellers_id.id.value, "MENSUEL-INTERNET-PRO-COAX")

    def test_sellers_item_identification_roundtrip(self):
        """SellersItemIdentification roundtrip: build → XML → parse → compare."""
        original = SellersItemIdentification(value="TEST-PRODUCT-123", schemeID="EAN")

        # Serialize to XML
        xml_elem = original.to_xml()

        # Parse back
        parsed = SellersItemIdentification.from_xml(xml_elem)

        # Compare
        self.assertEqual(parsed.value, original.value)
        self.assertEqual(parsed.schemeID, original.schemeID)
        self.assertEqual(parsed.id.value, original.id.value)
        self.assertEqual(parsed.id.schemeID, original.id.schemeID)


class TestItem(unittest.TestCase):
    """Tests for Item component."""

    def test_create_item_basic(self):
        """Test item with name only."""
        item = Item(name="Test Product")
        self.assertEqual(item.name.value, "Test Product")
        self.assertIsNone(item.description)

    def test_create_item_full(self):
        """Test item with all fields."""
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        sellers_id = SellersItemIdentification(value="PROD-001")
        item = Item(
            name="Test Product",
            description="Detailed description",
            sellers_item_identification=sellers_id,
            classified_tax_category=category,
        )
        self.assertEqual(item.description.value, "Detailed description")
        self.assertEqual(item.sellers_item_identification.value, "PROD-001")
        self.assertIs(item.classified_tax_category, category)

    def test_item_with_sellers_item_identification(self):
        """Test Item with SellersItemIdentification component."""
        sellers_id = SellersItemIdentification(value="MENSUEL-INTERNET-PRO-COAX")
        item = Item(name="Internet Verixi Pro Coax", sellers_item_identification=sellers_id)

        self.assertEqual(item.sellers_item_identification.value, "MENSUEL-INTERNET-PRO-COAX")
        self.assertIsInstance(item.sellers_item_identification, SellersItemIdentification)


class TestInvoiceLine(unittest.TestCase):
    """Tests for InvoiceLine component."""

    def test_create_invoice_line_valid(self):
        """Test invoice line with valid calculation."""
        item = Item(name="Test Product")
        price = Price(price_amount=PriceAmount(value=Decimal("10")))
        line = InvoiceLine(
            id="1",
            invoiced_quantity=InvoicedQuantity(value=Decimal("5")),
            line_extension_amount=LineExtensionAmount(value=Decimal("50")),
            item=item,
            price=price,
        )
        self.assertEqual(line.id.value, "1")
        self.assertEqual(line.invoiced_quantity.value, Decimal("5"))
        self.assertEqual(line.line_extension_amount.value, Decimal("50"))

    def test_invoice_line_validates_calculation(self):
        """Test that wrong calculation raises ValidationError."""
        item = Item(name="Test Product")
        price = Price(price_amount=PriceAmount(value=Decimal("10")))
        with self.assertRaises(ValidationError) as cm:
            InvoiceLine(
                id="1",
                invoiced_quantity=InvoicedQuantity(value=Decimal("5")),
                line_extension_amount=LineExtensionAmount(value=Decimal("100")),  # Wrong!
                item=item,
                price=price,
            )
        self.assertIn("does not match quantity × price", str(cm.exception))

    def test_invoice_line_with_optional_fields(self):
        """Test invoice line with optional fields."""
        item = Item(name="Test Product")
        price = Price(price_amount=PriceAmount(value=Decimal("10")))
        category = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21"
        )
        tax_total = TaxTotal(tax_amount=TaxAmount(value=Decimal("10.50")))

        line = InvoiceLine(
            id="1",
            invoiced_quantity=InvoicedQuantity(value=Decimal("5")),
            line_extension_amount=LineExtensionAmount(value=Decimal("50")),
            item=item,
            price=price,
            uuid="550e8400-e29b-41d4-a716-446655440000",
            notes=["Note 1", "Note 2"],
            tax_total=tax_total,
        )
        self.assertEqual(line.uuid.value, "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(len(line.notes), 2)
        self.assertEqual(line.notes[0].value, "Note 1")
        self.assertEqual(line.notes[1].value, "Note 2")
        self.assertIs(line.tax_total, tax_total)


class TestLegalMonetaryTotal(unittest.TestCase):
    """Tests for LegalMonetaryTotal component."""

    def test_create_legal_monetary_total(self):
        """Test legal monetary total creation."""
        total = LegalMonetaryTotal(
            line_extension_amount=LineExtensionAmount(value=Decimal("100")),
            tax_exclusive_amount=TaxExclusiveAmount(value=Decimal("100")),
            tax_inclusive_amount=TaxInclusiveAmount(value=Decimal("121")),
            payable_amount=PayableAmount(value=Decimal("121")),
        )
        self.assertEqual(total.line_extension_amount.value, Decimal("100"))
        self.assertEqual(total.tax_exclusive_amount.value, Decimal("100"))
        self.assertEqual(total.tax_inclusive_amount.value, Decimal("121"))
        self.assertEqual(total.payable_amount.value, Decimal("121"))


class TestXMLRoundTrip(unittest.TestCase):
    """Tests for XML serialization and parsing round-trip."""

    def test_country_roundtrip(self):
        """Test Country XML round-trip."""
        original = Country(identification_code="BE")
        xml = original.to_xml()
        parsed = Country.from_xml(xml)
        self.assertEqual(parsed.identification_code, original.identification_code)

    def test_contact_roundtrip(self):
        """Test Contact XML round-trip."""
        original = Contact(
            electronic_mail="test@example.com",
            telephone="+32 2 123 45 67",
            name="John Doe",
        )
        xml = original.to_xml()
        parsed = Contact.from_xml(xml)
        self.assertEqual(parsed.electronic_mail, original.electronic_mail)
        self.assertEqual(parsed.telephone, original.telephone)
        self.assertEqual(parsed.name, original.name)

    def test_postal_address_roundtrip(self):
        """Test PostalAddress XML round-trip with nested Country."""
        original = PostalAddress(
            street_name="Main St",
            city_name="Brussels",
            postal_zone="1000",
            country="BE",
        )
        xml = original.to_xml()
        parsed = PostalAddress.from_xml(xml)
        self.assertEqual(str(parsed.street_name), str(original.street_name))
        self.assertEqual(str(parsed.city_name), str(original.city_name))
        self.assertEqual(str(parsed.postal_zone), str(original.postal_zone))
        self.assertEqual(str(parsed.country.identification_code), "BE")

    def test_tax_category_roundtrip(self):
        """Test TaxCategory XML round-trip with nested TaxScheme."""
        original = TaxCategory(
            id=Identifier(value="S", schemeID="UNCL5305", schemeAgencyID="6"),
            percent="21",
            name="Standard Rate"
        )
        xml = original.to_xml()
        parsed = TaxCategory.from_xml(xml)
        self.assertEqual(parsed.id, original.id)
        self.assertEqual(parsed.percent, original.percent)
        self.assertEqual(parsed.name, original.name)

    def test_price_roundtrip(self):
        """Test Price XML round-trip."""
        original = Price(price_amount=PriceAmount(value=Decimal("10.50")))
        xml = original.to_xml()
        parsed = Price.from_xml(xml)
        self.assertEqual(parsed.price_amount.value, original.price_amount.value)


if __name__ == "__main__":
    unittest.main()
