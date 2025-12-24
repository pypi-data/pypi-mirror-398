"""
Tests for Party component and related elements.

Tests the Party dataclass with automatic identifier generation,
as well as PartyIdentification, PartyTaxScheme, and PartyLegalEntity.
"""

import unittest

from faker import Faker

from ubl.exceptions import ValidationError
from ubl.models.aggregate_components import (
    Party,
    PartyIdentification,
    PartyLegalEntity,
    PartyTaxScheme,
    PostalAddress,
    TaxScheme,
)
from ubl.models.basic_components import CompanyID, Identifier

# Faker instances for different locales
fake_be = Faker('nl_BE')
fake_nl = Faker('nl_NL')


class TestPartyIdentification(unittest.TestCase):
    """Test PartyIdentification component."""

    def setUp(self):
        """Set up test fixtures."""
        self.vat_number = fake_be.vat_id()

    def test_create_party_identification(self):
        """Create PartyIdentification with all fields."""
        party_id = PartyIdentification(value=self.vat_number, schemeID="BE:VAT", iso6523="9925")

        self.assertEqual(party_id.value, self.vat_number)
        self.assertEqual(party_id.schemeID, "BE:VAT")
        self.assertEqual(party_id.iso6523, "9925")

    def test_party_identification_generates_id(self):
        """PartyIdentification generates cbc:ID child."""
        party_id = PartyIdentification(value=self.vat_number, schemeID="BE:VAT", iso6523="9925")

        self.assertIsInstance(party_id.id, Identifier)
        self.assertEqual(party_id.id.value, self.vat_number)
        self.assertEqual(party_id.id.schemeID, "BE:VAT")

    def test_party_identification_equality(self):
        """PartyIdentification equality with case-insensitive comparison."""
        id1 = PartyIdentification(value=self.vat_number, schemeID="BE:VAT", iso6523="9925")
        id2 = PartyIdentification(value=self.vat_number.lower(), schemeID="BE:VAT", iso6523="9925")

        self.assertEqual(id1, id2)

    def test_party_identification_hash(self):
        """PartyIdentification hash for set deduplication."""
        id1 = PartyIdentification(value=self.vat_number, schemeID="BE:VAT", iso6523="9925")
        id2 = PartyIdentification(value=self.vat_number.lower(), schemeID="BE:VAT", iso6523="9925")

        self.assertEqual(hash(id1), hash(id2))

        # Can deduplicate in set
        id_set = {id1, id2}
        self.assertEqual(len(id_set), 1)


class TestPartyTaxScheme(unittest.TestCase):
    """Test PartyTaxScheme component."""

    def setUp(self):
        """Set up test fixtures."""
        self.vat_number = fake_be.vat_id()

    def test_create_party_tax_scheme(self):
        """Create PartyTaxScheme with company ID."""
        company_id = CompanyID(value=self.vat_number, schemeID="BE:VAT")
        party_tax_scheme = PartyTaxScheme(company_id=company_id)

        self.assertEqual(party_tax_scheme.company_id.value, self.vat_number)
        self.assertIsInstance(party_tax_scheme.tax_scheme, TaxScheme)
        self.assertEqual(party_tax_scheme.tax_scheme.id.value, "VAT")

    def test_party_tax_scheme_custom_tax_scheme(self):
        """PartyTaxScheme with custom tax scheme."""
        company_id = CompanyID(value="12345")
        tax_scheme = TaxScheme(id=Identifier(value="GST", schemeID="UN/ECE 5153"))
        party_tax_scheme = PartyTaxScheme(company_id=company_id, tax_scheme=tax_scheme)

        self.assertEqual(party_tax_scheme.tax_scheme.id.value, "GST")


class TestPartyLegalEntity(unittest.TestCase):
    """Test PartyLegalEntity component."""

    def setUp(self):
        """Set up test fixtures."""
        self.company_name = fake_be.company()
        vat = fake_be.vat_id()
        self.registration = vat.replace('BE', '').replace('be', '')

    def test_create_party_legal_entity(self):
        """Create PartyLegalEntity with name and company ID."""
        company_id = CompanyID(value=self.registration, schemeID="BE:EN")
        entity = PartyLegalEntity(registration_name=self.company_name, company_id=company_id)

        self.assertEqual(entity.registration_name.value, self.company_name)
        self.assertEqual(entity.company_id.value, self.registration)

    def test_party_legal_entity_no_company_id(self):
        """PartyLegalEntity without company ID."""
        entity = PartyLegalEntity(registration_name=self.company_name)

        self.assertEqual(entity.registration_name.value, self.company_name)
        self.assertIsNone(entity.company_id)


class TestPartyComponent(unittest.TestCase):
    """Test Party component with identifier generation."""

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
        self.registration = self.vat_number.replace('BE', '').replace('be', '')

    def test_create_party_with_vat(self):
        """Create party with VAT → generates identifiers."""
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
        )

        self.assertEqual(party.name, self.company_name)
        self.assertEqual(party.country_code, "BE")
        self.assertEqual(party.vat, self.vat_number)

        # Should generate 1 numeric identifier (PEPPOL numeric_only mode)
        identifiers = party.all_identifiers
        self.assertEqual(len(identifiers), 1)  # BE:VAT → 9925 only

    def test_party_endpoint_id_property(self):
        """Party.endpoint_id returns first identifier with numeric ISO 6523 schemeID."""
        from ubl.models.basic_components import EndpointID

        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
        )

        endpoint_id = party.endpoint_id
        self.assertIsInstance(endpoint_id, EndpointID)
        # EndpointID normalizes PEPPOL identifiers (BE0123456789 → be0123456789)
        self.assertEqual(endpoint_id.value.lower(), self.vat_number.lower())
        # PEPPOL requires numeric ISO 6523 codes (BE:VAT → 9925)
        self.assertEqual(endpoint_id.schemeID, "9925")

    def test_party_identification_list_property(self):
        """Party.party_identification_list returns first identifier (PEPPOL compliance)."""
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
        )

        id_list = party.party_identification_list
        # PEPPOL BIS 3.0 (UBL-SR-16) requires only ONE buyer/seller party identification
        self.assertEqual(len(id_list), 1)
        self.assertIsInstance(id_list[0], PartyIdentification)
        # Verify it's the first from all_identifiers
        self.assertEqual(id_list[0], party.all_identifiers[0])

    def test_party_tax_scheme_property(self):
        """Party.party_tax_scheme returns tax registration with numeric ISO 6523 schemeID."""
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
        )

        tax_scheme = party.party_tax_scheme
        self.assertIsNotNone(tax_scheme)
        self.assertIsInstance(tax_scheme, PartyTaxScheme)
        # CompanyID normalizes PEPPOL identifiers (BE0123456789 → be0123456789)
        self.assertEqual(tax_scheme.company_id.value.lower(), self.vat_number.lower())
        # PEPPOL BIS 3.0 (BR-CL-10) requires numeric ISO 6523 code, not "BE:VAT"
        self.assertEqual(tax_scheme.company_id.schemeID, "9925")  # BE:VAT → 9925

    def test_party_tax_scheme_no_vat(self):
        """Party without VAT → party_tax_scheme is None."""
        company_name = fake_be.company()
        party = Party(
            name=company_name,
            country_code="BE",
            postal_address=self.address,
            registration=self.registration,  # Belgian enterprise number (valid)
        )

        self.assertIsNone(party.party_tax_scheme)

    def test_party_legal_entity_property(self):
        """Party.party_legal_entity returns legal registration."""
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
            registration=self.registration,
        )

        legal_entity = party.party_legal_entity
        self.assertIsNotNone(legal_entity)
        self.assertIsInstance(legal_entity, PartyLegalEntity)
        self.assertEqual(legal_entity.registration_name.value, self.company_name)
        self.assertIsNotNone(legal_entity.company_id)
        self.assertEqual(legal_entity.company_id.value, self.registration)

    def test_party_with_vat_and_registration(self):
        """Party with both VAT and registration → 2 numeric identifiers (PEPPOL)."""
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
            registration=self.registration,
        )

        identifiers = party.all_identifiers
        # PEPPOL numeric_only mode: 1 VAT (9925) + 1 registration (0208) = 2 identifiers
        self.assertEqual(len(identifiers), 2)

    def test_party_with_peppol_ids(self):
        """Party with PEPPOL participant IDs (numeric only for PEPPOL compliance)."""
        peppol_id_1 = f"9925:{self.vat_number.lower()}"
        peppol_id_2 = f"0208:{self.registration}"

        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
            registration=self.registration,
            peppol_participant_ids=[peppol_id_1, peppol_id_2],
        )

        identifiers = party.all_identifiers
        # PEPPOL numeric_only mode: peppol_ids deduplicated with generated ones = 2 identifiers
        self.assertEqual(len(identifiers), 2)

        # PEPPOL IDs should be in the list
        iso_values = {i.value for i in identifiers if i.schemeID in ["9925", "0208"]}
        self.assertIn(self.vat_number.lower(), iso_values)
        self.assertIn(self.registration, iso_values)

    def test_party_with_contact(self):
        """Party with contact information."""
        from ubl.models.aggregate_components import Contact

        contact_email = fake_be.email()
        contact_phone = fake_be.phone_number()
        contact = Contact(electronic_mail=contact_email, telephone=contact_phone)
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
            contact=contact,
        )

        self.assertIsNotNone(party.contact)
        self.assertEqual(party.contact.electronic_mail.value, contact_email)

    def test_party_with_website(self):
        """Party with website URI."""
        website_url = fake_be.url()
        party = Party(
            name=self.company_name,
            country_code="BE",
            postal_address=self.address,
            vat=self.vat_number,
            website_uri=website_url,
        )

        self.assertEqual(party.website_uri, website_url)

    def test_party_netherlands_vat_only(self):
        """Netherlands party - only VAT (registration schemes have strict length requirements)."""
        nl_address = PostalAddress(
            street_name=fake_nl.street_name(),
            city_name=fake_nl.city(),
            postal_zone=fake_nl.postcode(),
            country="NL",
        )

        nl_company_name = fake_nl.company()
        nl_vat = fake_nl.vat_id()

        party = Party(
            name=nl_company_name,
            country_code="NL",
            postal_address=nl_address,
            vat=nl_vat,
            registration=None,  # NL schemes (KVK, OINO) have strict length requirements
        )

        # Only VAT generates identifiers (numeric only for PEPPOL)
        identifiers = party.all_identifiers
        self.assertEqual(len(identifiers), 1)  # NL:VAT → 9944 (numeric only)

        # Should have numeric VAT identifier (9944)
        vat_ids = [i for i in identifiers if i.schemeID == "9944"]
        self.assertEqual(len(vat_ids), 1)


if __name__ == "__main__":
    unittest.main()
