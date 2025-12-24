"""
Unit tests for basic components (Amount, Quantity, Identifier, Code).
"""

import unittest
from decimal import Decimal

from ubl.constants import DEFAULT_CURRENCY_CODE, DEFAULT_UNIT_CODE, UNIT_CODE_LIST_ID
from ubl.exceptions import ValidationError
from ubl.models import Amount, Code, Identifier, Quantity
from ubl.models.basic_components import get_max_decimal_places, quantize_to_max_precision


class TestQuantizationFunctions(unittest.TestCase):
    """Test quantization utility functions."""

    def test_get_max_decimal_places(self):
        """Test get_max_decimal_places with various inputs."""
        # Test with Decimal values
        self.assertEqual(get_max_decimal_places(Decimal('10.99'), Decimal('20.50')), 2)
        self.assertEqual(get_max_decimal_places(Decimal('10.999'), Decimal('20.50')), 3)
        self.assertEqual(get_max_decimal_places(Decimal('10'), Decimal('20.50')), 2)

        # Test with mixed types (non-Decimal should be ignored)
        self.assertEqual(get_max_decimal_places(Decimal('10.99'), 100, 'text'), 2)

        # Test with no Decimal values
        self.assertEqual(get_max_decimal_places(100, 'text'), 0)

        # Test with empty input
        self.assertEqual(get_max_decimal_places(), 0)

    def test_quantize_with_default_cap(self):
        """Test quantize_to_max_precision with default 2-decimal cap."""
        # 5 decimal places capped to 2
        result = quantize_to_max_precision(
            Decimal('31.49000'),
            Decimal('10.99999'),
            Decimal('20.50000')
        )
        self.assertEqual(result, Decimal('31.49'))

        # Lower precision preserved (1 decimal)
        result = quantize_to_max_precision(
            Decimal('31.5'),
            Decimal('10.5'),
            Decimal('21.0')
        )
        self.assertEqual(result, Decimal('31.5'))

    def test_quantize_with_custom_cap(self):
        """Test quantize_to_max_precision with custom cap values."""
        # Cap at 3 decimals
        result = quantize_to_max_precision(
            Decimal('31.49999'),
            Decimal('10.99999'),
            Decimal('20.50000'),
            cap=3
        )
        self.assertEqual(result, Decimal('31.500'))

        # Cap at 1 decimal
        result = quantize_to_max_precision(
            Decimal('31.49'),
            Decimal('10.99'),
            Decimal('20.50'),
            cap=1
        )
        self.assertEqual(result, Decimal('31.5'))

        # Cap at 0 decimals (integers only)
        result = quantize_to_max_precision(
            Decimal('31.49'),
            Decimal('10.99'),
            Decimal('20.50'),
            cap=0
        )
        self.assertEqual(result, Decimal('31'))

    def test_quantize_with_no_cap(self):
        """Test quantize_to_max_precision with cap=None (unlimited precision)."""
        # 5 decimal places preserved
        result = quantize_to_max_precision(
            Decimal('31.49999'),
            Decimal('10.99999'),
            Decimal('20.50000'),
            cap=None
        )
        self.assertEqual(result, Decimal('31.49999'))

    def test_quantize_caps_high_precision(self):
        """Test that high-precision sources are capped to 2 decimals by default."""
        # Calculation with 5-decimal precision should be capped to 2
        high_precision = Decimal('123.45678')
        result = quantize_to_max_precision(high_precision, high_precision)
        self.assertEqual(result, Decimal('123.46'))  # Rounded up

    def test_quantize_preserves_lower_precision(self):
        """Test that precision lower than cap is preserved."""
        # 1-decimal source should result in 1-decimal output
        one_decimal = Decimal('100.5')
        result = quantize_to_max_precision(one_decimal, one_decimal)
        self.assertEqual(result, Decimal('100.5'))

        # Integer (0 decimals) should stay integer
        integer = Decimal('100')
        result = quantize_to_max_precision(integer, integer)
        self.assertEqual(result, Decimal('100'))

    def test_amount_respects_cap(self):
        """Test that Amount with high precision gets capped to 2 decimals."""
        # Amount with 5 decimals should be capped to 2
        amount = Amount(value=Decimal('100.99999'))
        self.assertEqual(amount.value, Decimal('101.00'))  # Rounded up

        # Amount with 1 decimal should preserve 1 decimal
        amount = Amount(value=Decimal('100.5'))
        self.assertEqual(amount.value, Decimal('100.5'))

        # Amount with 2 decimals should preserve 2 decimals
        amount = Amount(value=Decimal('100.99'))
        self.assertEqual(amount.value, Decimal('100.99'))


class TestAmount(unittest.TestCase):
    """Test the Amount basic component."""

    def test_create_amount_with_decimal(self):
        """Test creating an Amount with a Decimal value."""
        amount = Amount(value=Decimal("100.50"))
        self.assertEqual(amount.value, Decimal("100.50"))
        self.assertEqual(amount.currencyID, DEFAULT_CURRENCY_CODE)

    def test_create_amount_with_int(self):
        """Test creating an Amount with an int (auto-converted to Decimal)."""
        amount = Amount(value=100)
        self.assertEqual(amount.value, Decimal("100"))

    def test_create_amount_with_float(self):
        """Test creating an Amount with a float (auto-converted to Decimal)."""
        amount = Amount(value=100.50)
        self.assertEqual(amount.value, Decimal("100.50"))

    def test_create_amount_with_custom_currency(self):
        """Test creating an Amount with custom currency."""
        amount = Amount(value=Decimal("50.00"), currencyID="USD")
        self.assertEqual(amount.value, Decimal("50.00"))
        self.assertEqual(amount.currencyID, "USD")

    def test_amount_negative_value_allowed(self):
        """Test that negative amounts are allowed (for credit notes, returns)."""
        amount = Amount(value=Decimal("-10.00"))
        self.assertEqual(amount.value, Decimal("-10.00"))

    def test_amount_is_mutable_but_should_be_treated_as_immutable(self):
        """
        Note: Amount is not frozen due to inheritance constraints.

        While Amount can technically be modified, it should be treated
        as immutable in practice. This test documents that it's not frozen.
        """
        amount = Amount(value=Decimal("100.00"))

        # Not frozen, so this will work (but shouldn't be done in practice)
        amount.value = Decimal("200.00")
        self.assertEqual(amount.value, Decimal("200.00"))

    def test_amount_element_name(self):
        """Test that Amount has correct element name."""
        amount = Amount(value=Decimal("100.00"))
        self.assertEqual(amount.element_name, "Amount")

    def test_amount_custom_element_name(self):
        """Test that Amount element_name can be customized via subclassing."""

        class TaxAmount(Amount):
            pass

        amount = TaxAmount(value=Decimal("100.00"))
        self.assertEqual(amount.element_name, "TaxAmount")


class TestQuantity(unittest.TestCase):
    """Test the Quantity basic component."""

    def test_create_quantity_with_decimal(self):
        """Test creating a Quantity with a Decimal value."""
        quantity = Quantity(value=Decimal("5.0"))
        self.assertEqual(quantity.value, Decimal("5.0"))
        self.assertEqual(quantity.unitCode, DEFAULT_UNIT_CODE)
        self.assertEqual(quantity.unitCodeListID, UNIT_CODE_LIST_ID)

    def test_create_quantity_with_int(self):
        """Test creating a Quantity with an int (auto-converted to Decimal)."""
        quantity = Quantity(value=10)
        self.assertEqual(quantity.value, Decimal("10"))

    def test_create_quantity_with_custom_unit(self):
        """Test creating a Quantity with custom unit code."""
        quantity = Quantity(value=Decimal("2.5"), unitCode="KGM")  # Kilogram
        self.assertEqual(quantity.value, Decimal("2.5"))
        self.assertEqual(quantity.unitCode, "KGM")

    def test_quantity_is_mutable_but_should_be_treated_as_immutable(self):
        """
        Note: Quantity is not frozen due to inheritance constraints.

        While Quantity can technically be modified, it should be treated
        as immutable in practice. This test documents that it's not frozen.
        """
        quantity = Quantity(value=Decimal("10.0"))

        # Not frozen, so this will work (but shouldn't be done in practice)
        quantity.value = Decimal("20.0")
        self.assertEqual(quantity.value, Decimal("20.0"))

    def test_quantity_element_name(self):
        """Test that Quantity has correct element name."""
        quantity = Quantity(value=Decimal("5.0"))
        self.assertEqual(quantity.element_name, "Quantity")

    def test_quantity_custom_element_name(self):
        """Test that Quantity element_name can be customized via subclassing."""

        class InvoicedQuantity(Quantity):
            pass

        quantity = InvoicedQuantity(value=Decimal("5.0"))
        self.assertEqual(quantity.element_name, "InvoicedQuantity")


class TestIdentifier(unittest.TestCase):
    """Test the Identifier basic component."""

    def test_create_identifier(self):
        """Test creating a simple Identifier."""
        identifier = Identifier(value="BE0597601756")
        self.assertEqual(identifier.value, "BE0597601756")
        self.assertIsNone(identifier.schemeID)

    def test_create_identifier_with_scheme(self):
        """Test creating an Identifier with scheme."""
        identifier = Identifier(value="BE0597601756", schemeID="BE:VAT")
        self.assertEqual(identifier.value, "BE0597601756")
        self.assertEqual(identifier.schemeID, "BE:VAT")

    def test_identifier_is_mutable_but_should_be_treated_as_immutable(self):
        """
        Note: Identifier is not frozen due to inheritance constraints.

        While Identifier can technically be modified, it should be treated
        as immutable in practice. This test documents that it's not frozen.
        """
        identifier = Identifier(value="test")

        # Not frozen, so this will work (but shouldn't be done in practice)
        identifier.value = "new_value"
        self.assertEqual(identifier.value, "new_value")

    def test_identifier_equality_case_insensitive(self):
        """Test that Identifier equality is case-insensitive."""
        id1 = Identifier(value="BE0597601756", schemeID="BE:VAT")
        id2 = Identifier(value="be0597601756", schemeID="BE:VAT")

        self.assertEqual(id1, id2)

    def test_identifier_equality_different_schemes(self):
        """Test that Identifiers with different schemes are not equal."""
        id1 = Identifier(value="0597601756", schemeID="BE:VAT")
        id2 = Identifier(value="0597601756", schemeID="BE:EN")

        self.assertNotEqual(id1, id2)

    def test_identifier_hash_for_sets(self):
        """Test that Identifiers can be used in sets (hashable)."""
        id1 = Identifier(value="BE0597601756", schemeID="BE:VAT")
        id2 = Identifier(value="be0597601756", schemeID="BE:VAT")  # Same, different case

        identifier_set = {id1, id2}
        # Should be deduplicated to one item
        self.assertEqual(len(identifier_set), 1)

    def test_identifier_element_name(self):
        """Test that Identifier has correct element name."""
        identifier = Identifier(value="test")
        self.assertEqual(identifier.element_name, "ID")

    def test_identifier_custom_element_name(self):
        """Test that Identifier element_name can be customized via subclassing."""

        class EndpointID(Identifier):
            # Need to override since Identifier.element_name returns "ID"
            @property
            def element_name(self) -> str:
                return self.__class__.__name__

        identifier = EndpointID(value="test")
        self.assertEqual(identifier.element_name, "EndpointID")


class TestCode(unittest.TestCase):
    """Test the Code basic component."""

    def test_create_code(self):
        """Test creating a simple Code."""
        code = Code(value="S")
        self.assertEqual(code.value, "S")
        self.assertIsNone(code.listID)
        self.assertIsNone(code.listAgencyID)

    def test_create_code_with_list_metadata(self):
        """Test creating a Code with list metadata."""
        code = Code(value="S", listID="UNCL5305", listAgencyID="6")
        self.assertEqual(code.value, "S")
        self.assertEqual(code.listID, "UNCL5305")
        self.assertEqual(code.listAgencyID, "6")

    def test_code_is_mutable_but_should_be_treated_as_immutable(self):
        """
        Note: Code is not frozen due to inheritance constraints.

        While Code can technically be modified, it should be treated
        as immutable in practice. This test documents that it's not frozen.
        """
        code = Code(value="S")

        # Not frozen, so this will work (but shouldn't be done in practice)
        code.value = "Z"
        self.assertEqual(code.value, "Z")

    def test_code_element_name(self):
        """Test that Code has correct element name."""
        code = Code(value="S")
        self.assertEqual(code.element_name, "Code")

    def test_code_custom_element_name(self):
        """Test that Code element_name can be customized via subclassing."""

        class PaymentMeansCode(Code):
            pass

        code = PaymentMeansCode(value="31")
        self.assertEqual(code.element_name, "PaymentMeansCode")


if __name__ == "__main__":
    unittest.main()
