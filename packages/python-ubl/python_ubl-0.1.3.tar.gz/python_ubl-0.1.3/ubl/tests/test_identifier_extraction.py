"""
Tests for identifier extraction logic.

Tests the extract_identifier function which extracts clean identifier
values from raw input using country-specific PEPPOL schemes.
"""

import unittest
import warnings

from faker import Faker

from ubl.identifiers.extractor import extract_identifier

# Generate test data
fake_be = Faker('nl_BE')
fake_nl = Faker('nl_NL')
fake_de = Faker('de_DE')
fake_fr = Faker('fr_FR')

# Reusable test identifiers
BE_VAT = fake_be.vat_id()
BE_REG = BE_VAT.replace('BE', '').replace('be', '')
NL_VAT = fake_nl.vat_id()
DE_VAT = fake_de.vat_id()
FR_VAT = fake_fr.vat_id()
FR_SIRENE = fake_fr.siren().replace(' ', '')  # Remove spaces for validation
FR_SIRET = fake_fr.siret().replace(' ', '')  # Remove spaces for validation


class TestIdentifierExtraction(unittest.TestCase):
    """Test identifier extraction with regex patterns."""

    def test_extract_vat_no_regex_belgium(self):
        """VAT schemes have no regex - accept as-is."""
        result = extract_identifier(BE_VAT, "BE", "vat")
        self.assertEqual(result, BE_VAT)

    def test_extract_vat_no_regex_netherlands(self):
        """Netherlands VAT - no regex."""
        result = extract_identifier(NL_VAT, "NL", "vat")
        self.assertEqual(result, NL_VAT)

    def test_extract_vat_with_prefix(self):
        """VAT with 'vat:' prefix - still accepted (no regex)."""
        result = extract_identifier("vat: BE_VAT", "BE", "vat")
        self.assertEqual(result, "vat: BE_VAT")

    def test_extract_kvk_fails_regex(self):
        """Netherlands KVK extraction fails (8 digits vs 17 expected)."""
        # KVK in real world is 8 digits, but PEPPOL scheme expects 17 (padded?)
        # OINO also expects 20 digits. Both regexes fail for 8-digit number.
        # For now, extraction returns None - padding logic can be added later.
        result = extract_identifier("kvk: 64985636", "NL", "registration")
        self.assertIsNone(result)  # No scheme matches 8 digits

    def test_extract_belgian_enterprise_number(self):
        """Belgian enterprise number with regex."""
        result = extract_identifier(BE_REG, "BE", "registration")
        self.assertEqual(result, BE_REG)

    def test_extract_belgian_enterprise_with_prefix(self):
        """Belgian enterprise number with text prefix."""
        result = extract_identifier(f"enterprise: {BE_REG}", "BE", "registration")
        # BE:EN regex is 0[0-9]{9}
        self.assertEqual(result, BE_REG)

    def test_extract_no_matching_scheme(self):
        """No scheme for country+type returns None."""
        result = extract_identifier("12345", "XX", "vat")  # Invalid country
        self.assertIsNone(result)

    def test_extract_invalid_format_with_regex(self):
        """Invalid format for scheme with regex returns None and warns."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Belgian enterprise number must start with 0
            result = extract_identifier("9597601756", "BE", "registration")
            # Should fail regex validation
            self.assertIsNone(result)
            # Should have warning
            self.assertGreater(len(w), 0)
            self.assertIn("Could not extract", str(w[0].message))

    def test_extract_vat_germany(self):
        """German VAT - no regex."""
        result = extract_identifier(DE_VAT, "DE", "vat")
        self.assertEqual(result, DE_VAT)

    def test_extract_vat_france(self):
        """French VAT - no regex."""
        result = extract_identifier(FR_VAT, "FR", "vat")
        self.assertEqual(result, FR_VAT)

    def test_extract_french_sirene(self):
        """French SIRENE with regex."""
        result = extract_identifier(FR_SIRENE, "FR", "registration")
        # FR:SIRENE regex: [0-9]{9}([0-9]{5})?
        self.assertEqual(result, FR_SIRENE)

    def test_extract_french_siret(self):
        """French SIRET (14 digits) with regex."""
        result = extract_identifier(FR_SIRET, "FR", "registration")
        # Should extract 14-digit number
        self.assertEqual(result, FR_SIRET)

    def test_extract_empty_value(self):
        """Empty value with no regex returns empty string."""
        result = extract_identifier("", "BE", "vat")
        # No regex means accept as-is, even empty
        self.assertEqual(result, "")

    def test_extract_whitespace_trimmed(self):
        """Whitespace in value with no regex."""
        result = extract_identifier("  BE_VAT  ", "BE", "vat")
        # No regex means accept as-is, whitespace included
        self.assertEqual(result, "  BE_VAT  ")

    def test_extract_mixed_case(self):
        """Mixed case with no regex."""
        result = extract_identifier("be0867709540", "BE", "vat")
        # No regex means accept as-is
        self.assertEqual(result, "be0867709540")


if __name__ == "__main__":
    unittest.main()
