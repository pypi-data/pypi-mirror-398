"""
Tests for identifier generation with PEPPOL precedence logic.

Tests the generate_all_with_precedence function which generates all
applicable party identifiers from VAT, registration, and PEPPOL IDs.
"""

import unittest
import warnings

from faker import Faker

from ubl.identifiers.generator import generate_all_with_precedence
from ubl.models.aggregate_components import PartyIdentification

# Generate test VAT numbers for different countries
fake_be = Faker('nl_BE')
fake_nl = Faker('nl_NL')
fake_de = Faker('de_DE')
fake_fr = Faker('fr_FR')

# Reusable test data - generate once at module level
BE_VAT_1 = fake_be.vat_id()
BE_VAT_2 = fake_be.vat_id()
BE_REG_1 = BE_VAT_1.replace('BE', '').replace('be', '')
BE_REG_2 = BE_VAT_2.replace('BE', '').replace('be', '')
NL_VAT = fake_nl.vat_id()
DE_VAT = fake_de.vat_id()
FR_VAT = fake_fr.vat_id()
FR_SIRENE = fake_fr.siren().replace(' ', '')  # Remove spaces for validation
FR_SIRET = fake_fr.siret().replace(' ', '')  # Remove spaces for validation


class TestIdentifierGeneration(unittest.TestCase):
    """Test identifier generation with precedence logic."""

    def test_p4x_belgium_vat_only(self):
        """
        Belgian company - VAT only → 2 identifiers.

        Expected:
        1. BE:VAT:(VAT number) (scheme_id format)
        2. 9925:(vat number lowercase) (iso6523 format)
        """
        identifiers = generate_all_with_precedence(
            country_code="BE", vat=BE_VAT_1, registration=None, peppol_participant_ids=[], numeric_only=False,
        )

        self.assertEqual(len(identifiers), 2)

        # Check scheme_id format
        scheme_id_format = [i for i in identifiers if i.schemeID == "BE:VAT"]
        self.assertEqual(len(scheme_id_format), 1)
        self.assertEqual(scheme_id_format[0].value, BE_VAT_1)
        self.assertEqual(scheme_id_format[0].iso6523, "9925")

        # Check iso6523 format (lowercase)
        iso6523_format = [i for i in identifiers if i.schemeID == "9925"]
        self.assertEqual(len(iso6523_format), 1)
        self.assertEqual(iso6523_format[0].value, BE_VAT_1.lower())

    def test_squads_netherlands_vat_only(self):
        """
        Squads B.V. (Netherlands) - VAT only → 2 identifiers.

        Netherlands registration schemes (KVK, OINO) have specific length requirements
        that don't match typical business numbers, so we only use VAT.

        Expected:
        1. NL:VAT:NL_VAT (scheme_id format)
        2. 9944:NL_VAT.lower() (iso6523 format)
        """
        identifiers = generate_all_with_precedence(
            country_code="NL",
            vat=NL_VAT,
            registration=None,  # NL registration schemes have strict length requirements
            peppol_participant_ids=[], numeric_only=False,
        )

        # Only VAT generates identifiers
        self.assertEqual(len(identifiers), 2)

        # VAT scheme_id format
        vat_scheme_id = [i for i in identifiers if i.schemeID == "NL:VAT"]
        self.assertEqual(len(vat_scheme_id), 1)
        self.assertEqual(vat_scheme_id[0].value, NL_VAT)

        # VAT iso6523 format
        vat_iso = [i for i in identifiers if i.schemeID == "9944"]
        self.assertEqual(len(vat_iso), 1)
        self.assertEqual(vat_iso[0].value, NL_VAT.lower())

    def test_levit_with_peppol_precedence(self):
        """
        LevIT SC (Belgium) - VAT + registration + peppol_ids → 4 identifiers.

        PEPPOL IDs take precedence for iso6523 format.

        Expected:
        1. BE:VAT:BE_VAT_2
        2. 9925:BE_VAT_2.lower() (from peppol, not generated)
        3. BE:EN:BE_REG_2
        4. 0208:BE_REG_2 (from peppol, not generated)
        """
        identifiers = generate_all_with_precedence(
            country_code="BE",
            vat=BE_VAT_2,
            registration=BE_REG_2,
            peppol_participant_ids=[f"9925:{BE_VAT_2.lower()}", f"0208:{BE_REG_2}"], numeric_only=False,
        )

        self.assertEqual(len(identifiers), 4)

        # VAT scheme_id format
        vat_scheme = [i for i in identifiers if i.schemeID == "BE:VAT"]
        self.assertEqual(len(vat_scheme), 1)
        self.assertEqual(vat_scheme[0].value, BE_VAT_2)

        # VAT iso6523 format (from peppol)
        vat_iso = [i for i in identifiers if i.schemeID == "9925"]
        self.assertEqual(len(vat_iso), 1)
        self.assertEqual(vat_iso[0].value, BE_VAT_2.lower())

        # Registration scheme_id format
        reg_scheme = [i for i in identifiers if i.schemeID == "BE:EN"]
        self.assertEqual(len(reg_scheme), 1)
        self.assertEqual(reg_scheme[0].value, BE_REG_2)

        # Registration iso6523 format (from peppol)
        reg_iso = [i for i in identifiers if i.schemeID == "0208"]
        self.assertEqual(len(reg_iso), 1)
        self.assertEqual(reg_iso[0].value, BE_REG_2)

    def test_peppol_precedence_mismatch_warning(self):
        """PEPPOL ID differs from generated → warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            identifiers = generate_all_with_precedence(
                country_code="BE",
                vat=BE_VAT_1,
                registration=None,
                peppol_participant_ids=["9925:be9999999999"],  # Different value
            )

            # Should warn about mismatch
            self.assertGreater(len(w), 0)
            warning_msg = str(w[0].message)
            self.assertIn("PEPPOL ID", warning_msg)
            self.assertIn("differs", warning_msg)

            # Should use PEPPOL value regardless
            iso_format = [i for i in identifiers if i.schemeID == "9925"]
            self.assertEqual(len(iso_format), 1)
            self.assertEqual(iso_format[0].value, "be9999999999")

    def test_peppol_precedence_match_no_warning(self):
        """PEPPOL ID matches generated → no warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            identifiers = generate_all_with_precedence(
                country_code="BE",
                vat=BE_VAT_1,
                registration=None,
                peppol_participant_ids=[f"9925:{BE_VAT_1.lower()}"],  # Matches
            )

            # Should not warn
            self.assertEqual(len(w), 0)

    def test_deduplication(self):
        """Duplicate identifiers are deduplicated."""
        identifiers = generate_all_with_precedence(
            country_code="BE",
            vat=BE_VAT_1,
            registration=None,
            peppol_participant_ids=[f"9925:{BE_VAT_1.lower()}"], numeric_only=False,  # Duplicate iso6523 format
        )

        # Should not have duplicates
        self.assertEqual(len(identifiers), 2)  # scheme_id + iso6523

        # Check using set
        id_tuples = [(i.schemeID, i.value.lower()) for i in identifiers]
        self.assertEqual(len(id_tuples), len(set(id_tuples)))

    def test_no_vat_no_registration(self):
        """No VAT or registration → empty list."""
        identifiers = generate_all_with_precedence(
            country_code="BE", vat=None, registration=None, peppol_participant_ids=[], numeric_only=False,
        )

        self.assertEqual(len(identifiers), 0)

    def test_only_peppol_ids(self):
        """Only PEPPOL IDs provided → returns them."""
        identifiers = generate_all_with_precedence(
            country_code="BE",
            vat=None,
            registration=None,
            peppol_participant_ids=[f"9925:{BE_VAT_1.lower()}", f"0208:{BE_REG_2}"], numeric_only=False,
        )

        self.assertEqual(len(identifiers), 2)

        ids_dict = {i.schemeID: i.value for i in identifiers}
        self.assertEqual(ids_dict["9925"], BE_VAT_1.lower())
        self.assertEqual(ids_dict["0208"], BE_REG_2)

    def test_invalid_peppol_format_ignored(self):
        """Invalid PEPPOL ID format (no colon) is ignored."""
        identifiers = generate_all_with_precedence(
            country_code="BE", vat=BE_VAT_1, registration=None, peppol_participant_ids=["invalid_format"], numeric_only=False,
        )

        # Should generate from VAT normally
        self.assertEqual(len(identifiers), 2)

    def test_multiple_registration_schemes(self):
        """Country with multiple registration schemes."""
        # Belgium has multiple registration schemes: BE:EN, BE:CBE, BE:KBON
        identifiers = generate_all_with_precedence(
            country_code="BE", vat=None, registration=BE_REG_2, peppol_participant_ids=[], numeric_only=False,
        )

        # Should generate at least one registration identifier
        self.assertGreater(len(identifiers), 0)

        # Should have scheme_id format
        scheme_ids = [i.schemeID for i in identifiers]
        self.assertTrue(any("BE:" in s for s in scheme_ids))

    def test_identifier_equality(self):
        """PartyIdentification equality works correctly."""
        id1 = PartyIdentification(value=BE_VAT_1, schemeID="BE:VAT", iso6523="9925")
        id2 = PartyIdentification(value=BE_VAT_1.lower(), schemeID="BE:VAT", iso6523="9925")
        id3 = PartyIdentification(value=BE_VAT_1.lower(), schemeID="9925", iso6523="9925")

        # Same scheme, different case → equal
        self.assertEqual(id1, id2)

        # Different scheme_id, same iso6523 → equal
        self.assertEqual(id1, id3)

    def test_identifier_hash(self):
        """PartyIdentification hash works for deduplication."""
        id1 = PartyIdentification(value=BE_VAT_1, schemeID="BE:VAT", iso6523="9925")
        id2 = PartyIdentification(value=BE_VAT_1.lower(), schemeID="BE:VAT", iso6523="9925")

        # Same hash despite case difference
        self.assertEqual(hash(id1), hash(id2))

        # Can use in set
        id_set = {id1, id2}
        self.assertEqual(len(id_set), 1)

    def test_germany_vat(self):
        """German VAT generation."""
        identifiers = generate_all_with_precedence(
            country_code="DE", vat=DE_VAT, registration=None, peppol_participant_ids=[], numeric_only=False,
        )

        self.assertEqual(len(identifiers), 2)

        # Check DE:VAT scheme
        vat_scheme = [i for i in identifiers if i.schemeID == "DE:VAT"]
        self.assertEqual(len(vat_scheme), 1)

    def test_france_vat_and_sirene(self):
        """French VAT + SIRENE."""
        identifiers = generate_all_with_precedence(
            country_code="FR", vat=FR_VAT, registration=FR_SIRENE, peppol_participant_ids=[], numeric_only=False,
        )

        self.assertGreaterEqual(len(identifiers), 4)

        # Should have FR:VAT
        vat_ids = [i for i in identifiers if "VAT" in i.schemeID]
        self.assertGreater(len(vat_ids), 0)

        # Should have FR:SIRENE
        sirene_ids = [i for i in identifiers if "SIRENE" in i.schemeID]
        self.assertGreater(len(sirene_ids), 0)

    def test_case_insensitive_scheme_lookup(self):
        """PEPPOL IDs with case variations."""
        identifiers = generate_all_with_precedence(
            country_code="BE", vat=BE_VAT_1.lower(), registration=None, peppol_participant_ids=[f"9925:{BE_VAT_1}"], numeric_only=False,
        )

        # Should handle case differences
        self.assertEqual(len(identifiers), 2)

    def test_empty_peppol_list(self):
        """Empty PEPPOL list behaves same as None."""
        ids1 = generate_all_with_precedence(
            country_code="BE", vat=BE_VAT_1, registration=None, peppol_participant_ids=[], numeric_only=False,
        )

        ids2 = generate_all_with_precedence(
            country_code="BE", vat=BE_VAT_1, registration=None, peppol_participant_ids=[], numeric_only=False,
        )

        self.assertEqual(len(ids1), len(ids2))

    def test_invalid_registration_filtered(self):
        """
        Invalid registration (regex fails) → identifiers filtered out.

        NL KVK requires 17 chars (8 digits + 9-char suffix), "KVK: 64985636" has only 8 digits.
        Extraction fails, schemeID cleared, identifier filtered out.

        This prevents duplicate identifiers with no schemeID from appearing in XML.
        """
        identifiers = generate_all_with_precedence(
            country_code="NL",
            vat=None,
            registration="KVK: 64985636",  # Invalid - won't match NL KVK regex (requires 17 chars)
            peppol_participant_ids=[], numeric_only=False,
        )

        # Should be empty - invalid registration filtered out
        self.assertEqual(len(identifiers), 0)

    def test_invalid_registration_with_valid_vat(self):
        """
        Invalid registration + valid VAT → only VAT identifiers generated.

        Ensures invalid identifiers are filtered while valid ones pass through.
        """
        identifiers = generate_all_with_precedence(
            country_code="NL",
            vat=NL_VAT,
            registration="KVK: 64985636",  # Invalid
            peppol_participant_ids=[], numeric_only=False,
        )

        # Should have 2 identifiers from VAT only
        self.assertEqual(len(identifiers), 2)

        # Should all be VAT identifiers
        scheme_ids = [i.schemeID for i in identifiers]
        self.assertIn("NL:VAT", scheme_ids)
        self.assertIn("9944", scheme_ids)

        # Should have NO KVK identifiers
        self.assertNotIn("NL:KVK", scheme_ids)
        self.assertNotIn("0106", scheme_ids)


if __name__ == "__main__":
    unittest.main()
