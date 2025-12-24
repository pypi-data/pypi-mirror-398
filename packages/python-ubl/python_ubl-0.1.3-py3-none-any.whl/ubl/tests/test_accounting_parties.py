"""
Tests for AccountingSupplierParty and AccountingCustomerParty wrappers.

Tests the wrapper components that contain Party elements, used to
represent the supplier (seller) and customer (buyer) in UBL documents.
"""

import unittest

from faker import Faker
from lxml import etree

from ubl.models.aggregate_components import (
    AccountingCustomerParty,
    AccountingSupplierParty,
    Party,
    PostalAddress,
)

# Faker instances for Belgian data
fake_be = Faker('nl_BE')


class TestAccountingPartyWrappers(unittest.TestCase):
    """Test AccountingSupplierParty and AccountingCustomerParty wrappers."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = PostalAddress(
            street_name=fake_be.street_name(),
            city_name=fake_be.city(),
            postal_zone=fake_be.postcode(),
            country="BE",
        )

        self.company_name = fake_be.company()
        self.vat_number = fake_be.vat_id()

        self.party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
        )

    def test_create_accounting_supplier_party(self):
        """Create AccountingSupplierParty wrapper."""
        supplier = AccountingSupplierParty(party=self.party)

        self.assertIsInstance(supplier.party, Party)
        self.assertEqual(supplier.party.name, self.company_name)

    def test_create_accounting_customer_party(self):
        """Create AccountingCustomerParty wrapper."""
        customer = AccountingCustomerParty(party=self.party)

        self.assertIsInstance(customer.party, Party)
        self.assertEqual(customer.party.name, self.company_name)

    def test_supplier_and_customer_are_separate_types(self):
        """Supplier and customer are distinct types."""
        supplier = AccountingSupplierParty(party=self.party)
        customer = AccountingCustomerParty(party=self.party)

        # Different types
        self.assertNotEqual(type(supplier), type(customer))

    def test_accounting_supplier_party_to_xml(self):
        """AccountingSupplierParty generates correct XML structure."""
        supplier = AccountingSupplierParty(party=self.party)

        xml = supplier.to_xml()
        self.assertEqual(
            xml.tag, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty",
        )

        # Should have Party child
        party_elements = xml.findall("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        self.assertEqual(len(party_elements), 1)

    def test_accounting_customer_party_to_xml(self):
        """AccountingCustomerParty generates correct XML structure."""
        customer = AccountingCustomerParty(party=self.party)

        xml = customer.to_xml()
        self.assertEqual(
            xml.tag, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty",
        )

        # Should have Party child
        party_elements = xml.findall("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        self.assertEqual(len(party_elements), 1)

    def test_accounting_supplier_party_xml_roundtrip(self):
        """AccountingSupplierParty round-trip preservation."""
        supplier = AccountingSupplierParty(party=self.party)

        # Generate XML
        xml = supplier.to_xml()
        xml_str = etree.tostring(xml, encoding="unicode")

        # Parse back
        parsed_xml = etree.fromstring(xml_str)
        reconstructed = AccountingSupplierParty.from_xml(parsed_xml)

        # Should preserve party name
        self.assertEqual(str(reconstructed.party.name), self.company_name)
        self.assertEqual(reconstructed.party.country_code, "BE")

    def test_accounting_customer_party_xml_roundtrip(self):
        """AccountingCustomerParty round-trip preservation."""
        customer = AccountingCustomerParty(party=self.party)

        # Generate XML
        xml = customer.to_xml()
        xml_str = etree.tostring(xml, encoding="unicode")

        # Parse back
        parsed_xml = etree.fromstring(xml_str)
        reconstructed = AccountingCustomerParty.from_xml(parsed_xml)

        # Should preserve party details
        self.assertEqual(str(reconstructed.party.name), self.company_name)
        self.assertEqual(reconstructed.party.country_code, "BE")

    def test_accounting_party_with_complex_party(self):
        """Wrapper with complex party (VAT + registration + contact)."""
        from ubl.models.aggregate_components import Contact

        complex_company_name = fake_be.company()
        complex_email = fake_be.email()
        complex_phone = fake_be.phone_number()
        complex_vat = fake_be.vat_id()
        complex_registration = complex_vat.replace('BE', '').replace('be', '')
        complex_website = fake_be.url()
        peppol_id = f"9925:{complex_vat.lower()}"

        contact = Contact(electronic_mail=complex_email, telephone=complex_phone)

        complex_party = Party(
            name=complex_company_name,
            country_code="BE",
            postal_address=self.address,
            vat=complex_vat,
            registration=complex_registration,
            contact=contact,
            website_uri=complex_website,
            peppol_participant_ids=[peppol_id],
        )

        supplier = AccountingSupplierParty(party=complex_party)

        # Should preserve all party details
        self.assertEqual(supplier.party.name, complex_company_name)
        self.assertEqual(supplier.party.vat, complex_vat)
        self.assertEqual(supplier.party.registration, complex_registration)
        self.assertIsNotNone(supplier.party.contact)
        self.assertEqual(supplier.party.website_uri, complex_website)
        self.assertEqual(len(supplier.party.peppol_participant_ids), 1)

    def test_xml_contains_party_identifications(self):
        """XML contains all party identifications."""
        supplier = AccountingSupplierParty(party=self.party)

        xml = supplier.to_xml()
        xml_str = etree.tostring(xml, encoding="unicode")

        # Should contain PartyIdentification elements
        self.assertIn("PartyIdentification", xml_str)

        # Should have endpoint ID
        self.assertIn("EndpointID", xml_str)

    def test_xml_namespace_collection(self):
        """Wrapper XML contains expected namespaces."""
        supplier = AccountingSupplierParty(party=self.party)

        xml = supplier.to_xml()
        xml_str = etree.tostring(xml, encoding='unicode')

        # Should have CAC namespace
        self.assertIn('xmlns:cac=', xml_str)

        # Should also have CBC namespace (from Identifier, etc.)
        self.assertIn('xmlns:cbc=', xml_str)


if __name__ == "__main__":
    unittest.main()
