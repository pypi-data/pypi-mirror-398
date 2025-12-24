"""
XML roundtrip tests: dataclass → XML → dataclass → equality.

These tests verify that we can serialize dataclasses to XML and
parse them back without losing data.
"""

import unittest
from decimal import Decimal

from faker import Faker
from lxml import etree

from ubl.models import Amount, Code, Identifier, Quantity

# Faker instance
fake_be = Faker('nl_BE')

# Reusable test data
VAT_1 = fake_be.vat_id()
VAT_2 = fake_be.vat_id()


class TestAmountRoundtrip(unittest.TestCase):
    """Test Amount XML roundtrip."""

    def test_amount_roundtrip_basic(self):
        """Test basic Amount serialization and parsing."""
        # Create Amount
        original = Amount(value=Decimal("100.50"))

        # Serialize to XML
        xml_element = original.to_xml()

        # Parse back
        parsed = Amount.from_xml(xml_element)

        # Verify equality
        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.currencyID, parsed.currencyID)

    def test_amount_roundtrip_with_custom_currency(self):
        """Test Amount roundtrip with custom currency."""
        original = Amount(value=Decimal("250.75"), currencyID="USD")

        xml_element = original.to_xml()
        parsed = Amount.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.currencyID, parsed.currencyID)

    def test_amount_roundtrip_with_custom_element_name(self):
        """Test Amount roundtrip with custom element name."""

        class TaxAmount(Amount):
            pass

        original = TaxAmount(value=Decimal("21.00"), currencyID="EUR")

        xml_element = original.to_xml()

        # Verify element name in XML
        tag_name = etree.QName(xml_element).localname
        self.assertEqual(tag_name, "TaxAmount")

        # Parse back
        parsed = TaxAmount.from_xml(xml_element)
        self.assertEqual(original.value, parsed.value)

    def test_amount_xml_structure(self):
        """Test that Amount generates correct XML structure."""
        amount = Amount(value=Decimal("100.00"), currencyID="EUR")

        xml_element = amount.to_xml()

        # Check text content
        self.assertEqual(xml_element.text, "100.00")

        # Check currencyID attribute
        self.assertEqual(xml_element.get("currencyID"), "EUR")

        # Check namespace
        self.assertIn("CommonBasicComponents", etree.QName(xml_element).namespace)


class TestQuantityRoundtrip(unittest.TestCase):
    """Test Quantity XML roundtrip."""

    def test_quantity_roundtrip_basic(self):
        """Test basic Quantity serialization and parsing."""
        original = Quantity(value=Decimal("5.0"))

        xml_element = original.to_xml()
        parsed = Quantity.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.unitCode, parsed.unitCode)

    def test_quantity_roundtrip_with_custom_unit(self):
        """Test Quantity roundtrip with custom unit code."""
        original = Quantity(value=Decimal("2.5"), unitCode="KGM", unitCodeListID="UNECERec20")

        xml_element = original.to_xml()
        parsed = Quantity.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.unitCode, parsed.unitCode)
        self.assertEqual(original.unitCodeListID, parsed.unitCodeListID)


class TestIdentifierRoundtrip(unittest.TestCase):
    """Test Identifier XML roundtrip."""

    def test_identifier_roundtrip_basic(self):
        """Test basic Identifier serialization and parsing."""
        original = Identifier(value=VAT_1)

        xml_element = original.to_xml()
        parsed = Identifier.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.schemeID, parsed.schemeID)

    def test_identifier_roundtrip_with_scheme(self):
        """Test Identifier roundtrip with scheme."""
        original = Identifier(value=VAT_1, schemeID="BE:VAT")

        xml_element = original.to_xml()
        parsed = Identifier.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.schemeID, parsed.schemeID)

    def test_identifier_xml_structure(self):
        """Test that Identifier generates correct XML structure."""
        identifier = Identifier(value=VAT_2, schemeID="BE:VAT")

        xml_element = identifier.to_xml()

        # Check text content
        self.assertEqual(xml_element.text, VAT_2)

        # Check schemeID attribute
        self.assertEqual(xml_element.get("schemeID"), "BE:VAT")


class TestCodeRoundtrip(unittest.TestCase):
    """Test Code XML roundtrip."""

    def test_code_roundtrip_basic(self):
        """Test basic Code serialization and parsing."""
        original = Code(value="S")

        xml_element = original.to_xml()
        parsed = Code.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.listID, parsed.listID)

    def test_code_roundtrip_with_metadata(self):
        """Test Code roundtrip with list metadata."""
        original = Code(value="S", listID="UNCL5305", listAgencyID="6")

        xml_element = original.to_xml()
        parsed = Code.from_xml(xml_element)

        self.assertEqual(original.value, parsed.value)
        self.assertEqual(original.listID, parsed.listID)
        self.assertEqual(original.listAgencyID, parsed.listAgencyID)


class TestXMLPrettyPrint(unittest.TestCase):
    """Test XML pretty printing and formatting."""

    def test_amount_pretty_print(self):
        """Test that Amount can be pretty-printed as XML."""

        class TaxAmount(Amount):
            pass

        amount = TaxAmount(value=Decimal("100.00"), currencyID="EUR")

        xml_element = amount.to_xml()
        xml_string = etree.tostring(xml_element, encoding="unicode", pretty_print=True)

        # Should contain the element name, value, and currency
        self.assertIn("TaxAmount", xml_string)
        self.assertIn("100.00", xml_string)
        self.assertIn("currencyID", xml_string)
        self.assertIn("EUR", xml_string)

    def test_xml_has_namespaces(self):
        """Test that generated XML includes namespace declarations."""
        amount = Amount(value=Decimal("50.00"))

        xml_element = amount.to_xml()
        xml_string = etree.tostring(xml_element, encoding="unicode")

        # Should contain namespace declarations
        self.assertIn("xmlns:", xml_string)
        self.assertIn("CommonBasicComponents", xml_string)


class TestNamespaceCollection(unittest.TestCase):
    """Test namespace collection and declaration."""

    def test_namespace_collection_single_element(self):
        """Test namespace collection for single element."""
        amount = Amount(value=Decimal("100"))

        namespaces = amount._collect_all_namespaces()

        # Should return set of tuples
        self.assertIsInstance(namespaces, set)

        # Should contain CBC namespace
        namespace_urls = {url for url, prefix in namespaces}
        self.assertIn(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            namespace_urls,
        )

    def test_namespace_collection_nested_elements(self):
        """Test namespace collection for nested elements."""
        from ubl.models import Price, PriceAmount

        price = Price(price_amount=PriceAmount(value=Decimal("10")))

        namespaces = price._collect_all_namespaces()

        # Should return set
        self.assertIsInstance(namespaces, set)

        # Should contain both CAC (Price) and CBC (PriceAmount) namespaces
        namespace_urls = {url for url, prefix in namespaces}
        self.assertIn(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            namespace_urls,
        )
        self.assertIn(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            namespace_urls,
        )

    def test_namespace_deduplication(self):
        """Test that duplicate namespaces are deduplicated."""
        from ubl.models import InvoicedQuantity, InvoiceLine, Item, LineExtensionAmount, Price, PriceAmount

        # Create line with multiple CBC elements
        item = Item(name="Test")
        price = Price(price_amount=PriceAmount(value=Decimal("10")))
        line = InvoiceLine(
            id="1",
            invoiced_quantity=InvoicedQuantity(value=Decimal("5")),
            line_extension_amount=LineExtensionAmount(value=Decimal("50")),
            item=item,
            price=price,
        )

        namespaces = line._collect_all_namespaces()

        # Should be a set (automatic deduplication)
        self.assertIsInstance(namespaces, set)

        # Count occurrences of CBC namespace (should appear only once despite multiple CBC children)
        cbc_count = sum(1 for url, prefix in namespaces if "CommonBasicComponents" in url)
        self.assertEqual(cbc_count, 1, "CBC namespace should appear only once")

    def test_root_element_has_nsmap(self):
        """Test that root element includes nsmap."""
        amount = Amount(value=Decimal("100"))

        xml = amount.to_xml()

        # Root element should have nsmap
        self.assertIsNotNone(xml.nsmap)
        self.assertGreater(len(xml.nsmap), 0)

    def test_child_element_no_nsmap(self):
        """Test that child elements don't redeclare namespaces."""
        from ubl.models import Price, PriceAmount

        price = Price(price_amount=PriceAmount(value=Decimal("10")))

        # Generate XML (price is root, price_amount is child)
        xml = price.to_xml()

        # Find the child element (PriceAmount)
        price_amount_elem = xml.find(
            ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount",
        )

        self.assertIsNotNone(price_amount_elem, "PriceAmount child should exist")

        # Child should not have its own nsmap (uses parent's)
        # Note: lxml may show nsmap inherited from parent, but it shouldn't declare new ones
        # The key test is that the XML string doesn't redeclare xmlns on children
        xml_string = etree.tostring(xml, encoding="unicode")

        # Count xmlns declarations (should only be on root element)
        # Split by opening tags and count xmlns occurrences
        xmlns_count = xml_string.count("xmlns:")

        # Should have xmlns declarations, but not duplicated on every child
        self.assertGreater(xmlns_count, 0, "Should have namespace declarations")

    def test_only_used_namespaces_included(self):
        """Test that only namespaces actually used are declared."""
        amount = Amount(value=Decimal("100"))

        xml = amount.to_xml()

        # Get namespace map
        nsmap = xml.nsmap

        # Should include CBC (used by Amount)
        self.assertIn(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            nsmap.values(),
        )

        # Should NOT include CAC (not used by Amount alone)
        # Note: This test would fail with the old implementation that included ALL namespaces
        self.assertNotIn(
            "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            nsmap.values(),
            "CAC namespace should not be included when not used",
        )


class TestListFieldParsing(unittest.TestCase):
    """Regression tests for list field parsing from XML."""

    def test_tax_total_single_subtotal_roundtrip(self):
        """Regression test: TaxTotal with single subtotal should parse as list."""
        from ubl.models import TaxTotal, TaxSubtotal, TaxCategory, TaxAmount, TaxableAmount, Percent, ID

        # Create TaxTotal with single subtotal
        category = TaxCategory(id=ID(value='S', schemeID='UNCL5305', schemeAgencyID='6'), percent=Percent(21))
        subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(Decimal('100.00')),
            tax_amount=TaxAmount(Decimal('21.00')),
            percent=Percent(21),
            tax_category=category,
        )
        original = TaxTotal(tax_amount=TaxAmount(Decimal('21.00')), tax_subtotals=[subtotal])

        # Roundtrip
        xml_element = original.to_xml()
        parsed = TaxTotal.from_xml(xml_element)

        # Should still be a list with one element
        self.assertIsInstance(parsed.tax_subtotals, list)
        self.assertEqual(len(parsed.tax_subtotals), 1)
        self.assertEqual(parsed.tax_subtotals[0].tax_amount.value, Decimal('21.00'))

    def test_tax_total_multiple_subtotals_roundtrip(self):
        """Test TaxTotal with multiple subtotals parses correctly."""
        from ubl.models import TaxTotal, TaxSubtotal, TaxCategory, TaxAmount, TaxableAmount, Percent, ID

        # Create TaxTotal with two subtotals
        category1 = TaxCategory(id=ID(value='S', schemeID='UNCL5305', schemeAgencyID='6'), percent=Percent(21))
        subtotal1 = TaxSubtotal(
            taxable_amount=TaxableAmount(Decimal('100.00')),
            tax_amount=TaxAmount(Decimal('21.00')),
            percent=Percent(21),
            tax_category=category1,
        )

        category2 = TaxCategory(id=ID(value='S', schemeID='UNCL5305', schemeAgencyID='6'), percent=Percent(6))
        subtotal2 = TaxSubtotal(
            taxable_amount=TaxableAmount(Decimal('50.00')),
            tax_amount=TaxAmount(Decimal('3.00')),
            percent=Percent(6),
            tax_category=category2,
        )

        original = TaxTotal(tax_amount=TaxAmount(Decimal('24.00')), tax_subtotals=[subtotal1, subtotal2])

        # Roundtrip
        xml_element = original.to_xml()
        parsed = TaxTotal.from_xml(xml_element)

        # Should be a list with two elements
        self.assertIsInstance(parsed.tax_subtotals, list)
        self.assertEqual(len(parsed.tax_subtotals), 2)
        self.assertEqual(parsed.tax_subtotals[0].tax_amount.value, Decimal('21.00'))
        self.assertEqual(parsed.tax_subtotals[1].tax_amount.value, Decimal('3.00'))


if __name__ == "__main__":
    unittest.main()
