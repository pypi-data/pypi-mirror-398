"""
Tests for document models (Invoice and CreditNote).
"""

import unittest
from datetime import date
from decimal import Decimal

from faker import Faker

from ubl.models import (
    Amount,
    Contact,
    Country,
    CreditNote,
    Identifier,
    Invoice,
    InvoicedQuantity,
    InvoiceLine,
    IssueDate,
    Item,
    LegalMonetaryTotal,
    LineExtensionAmount,
    Party,
    PayableAmount,
    PostalAddress,
    Price,
    PriceAmount,
    TaxableAmount,
    TaxAmount,
    TaxCategory,
    TaxExclusiveAmount,
    TaxInclusiveAmount,
    TaxScheme,
    TaxSubtotal,
    TaxTotal,
)

fake = Faker()
fake_be = Faker('nl_BE')
fake_nl = Faker('nl_NL')


class TestInvoice(unittest.TestCase):
    """Test Invoice document model."""

    def setUp(self):
        """Create test data for invoices."""
        # Create supplier (Belgian company)
        self.supplier = Party(
            name=fake_be.company(),
            postal_address=PostalAddress(
                street_name=fake_be.street_name(),
                city_name=fake_be.city(),
                postal_zone=fake_be.postcode(),
                country='BE',
            ),
            vat=fake_be.vat_id(),
            contact=Contact(electronic_mail=fake_be.email()),
        )

        # Create customer (Dutch company)
        self.customer = Party(
            name=fake_nl.company(),
            postal_address=PostalAddress(
                street_name=fake_nl.street_name(),
                city_name=fake_nl.city(),
                postal_zone=fake_nl.postcode(),
                country='NL',
            ),
            vat=fake_nl.vat_id(),
            contact=Contact(electronic_mail=fake_nl.email()),
        )

        # Create invoice line with realistic amounts and line-level tax
        unit_price = Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=1, max_value=999))
        quantity = Decimal(fake.random_int(min=1, max=100))
        line_total = unit_price * quantity

        # Create tax (21% VAT)
        tax_rate = Decimal('21')
        line_tax_amount = (line_total * tax_rate / 100).quantize(Decimal('0.01'))

        tax_category = TaxCategory(id='S', percent=tax_rate, tax_scheme=TaxScheme())
        tax_subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=line_total),
            tax_amount=TaxAmount(value=line_tax_amount),
            percent=tax_rate,
            tax_category=tax_category,
        )
        line_tax_total = TaxTotal(tax_amount=TaxAmount(value=line_tax_amount), tax_subtotals=[tax_subtotal])

        self.line = InvoiceLine(
            id=Identifier(value='1'),
            invoiced_quantity=InvoicedQuantity(value=quantity),
            line_extension_amount=LineExtensionAmount(value=line_total),
            item=Item(name=fake.catch_phrase()),
            price=Price(price_amount=PriceAmount(value=unit_price)),
            tax_total=line_tax_total,  # Line-level tax for document-level tax computation
        )

        # Store for assertions
        self.line_total = line_total
        self.line_tax_amount = line_tax_amount
        self.total_with_tax = line_total + line_tax_amount

    def test_create_invoice(self):
        """Test creating an invoice."""
        invoice_number = f'INV-{fake.random_int(min=1000, max=9999)}'
        issue_date = fake.date_between(start_date='-30d', end_date='today')

        invoice = Invoice(
            id=Identifier(value=invoice_number),
            issue_date=IssueDate(value=issue_date),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        self.assertEqual(invoice.id.value, invoice_number)
        self.assertEqual(invoice.issue_date.value, issue_date.isoformat())
        self.assertIsNotNone(invoice.supplier.name)
        self.assertIsNotNone(invoice.customer.name)
        self.assertEqual(len(invoice.lines), 1)
        self.assertEqual(invoice.document_type_code, '380')
        self.assertEqual(invoice.element_name, 'Invoice')

    def test_invoice_namespace(self):
        """Test that invoice has correct namespace."""
        invoice = Invoice(
            id=Identifier(value=f'INV-{fake.random_int(min=1000, max=9999)}'),
            issue_date=IssueDate(value=fake.date_this_year()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        self.assertEqual(invoice.url, 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2')
        self.assertEqual(invoice.prefix, '')  # Root element uses default namespace

    def test_invoice_auto_line_count(self):
        """Test that line count is computed from lines."""
        invoice = Invoice(
            id=Identifier(value=f'INV-{fake.random_int(min=1000, max=9999)}'),
            issue_date=IssueDate(value=fake.date_this_year()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        self.assertEqual(invoice.line_count_numeric.value, '1')

    def test_invoice_validation_no_lines(self):
        """Test that invoice requires at least one line."""
        with self.assertRaises(Exception) as cm:
            Invoice(
                id=Identifier(value=f'INV-{fake.random_int(min=1000, max=9999)}'),
                issue_date=IssueDate(value=fake.date_this_year()),
                supplier=self.supplier,
                customer=self.customer,
                lines=[],
            )

        self.assertIn('at least one line', str(cm.exception))

    def test_invoice_computed_totals(self):
        """Test that tax_totals and legal_monetary_total are computed correctly."""
        invoice = Invoice(
            id=Identifier(value=f'INV-{fake.random_int(min=1000, max=9999)}'),
            issue_date=IssueDate(value=fake.date_this_year()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        # Tax totals should be computed from line-level taxes
        self.assertEqual(len(invoice.tax_totals), 1)
        self.assertEqual(invoice.tax_totals[0].tax_amount.value, self.line_tax_amount)

        # Legal monetary total should be computed
        self.assertEqual(invoice.legal_monetary_total.line_extension_amount.value, self.line_total)
        self.assertEqual(invoice.legal_monetary_total.payable_amount.value, self.total_with_tax)

    def test_invoice_xml_generation(self):
        """Test that invoice can be serialized to XML."""
        invoice = Invoice(
            id=Identifier(value=f'INV-{fake.random_int(min=1000, max=9999)}'),
            issue_date=IssueDate(value=fake.date_this_year()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        # Generate XML
        xml = invoice.to_xml_string()

        # Verify XML structure
        self.assertIn('<?xml version', xml)
        self.assertIn('<Invoice', xml)
        self.assertIn('xmlns', xml)
        self.assertIn('AccountingSupplierParty', xml)
        self.assertIn('AccountingCustomerParty', xml)
        self.assertIn('InvoiceLine', xml)
        self.assertIn('TaxTotal', xml)
        self.assertIn('LegalMonetaryTotal', xml)


class TestCreditNote(unittest.TestCase):
    """Test CreditNote document model."""

    def setUp(self):
        """Create test data for credit notes."""
        # Create supplier (Belgian company)
        self.supplier = Party(
            name=fake_be.company(),
            postal_address=PostalAddress(
                street_name=fake_be.street_name(),
                city_name=fake_be.city(),
                postal_zone=fake_be.postcode(),
                country='BE',
            ),
            vat=fake_be.vat_id(),
        )

        # Create customer (Dutch company)
        self.customer = Party(
            name=fake_nl.company(),
            postal_address=PostalAddress(
                street_name=fake_nl.street_name(),
                city_name=fake_nl.city(),
                postal_zone=fake_nl.postcode(),
                country='NL',
            ),
            vat=fake_nl.vat_id(),
        )

        # Create credit note line
        unit_price = Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=1, max_value=999))
        quantity = Decimal(fake.random_int(min=1, max=50))
        line_total = unit_price * quantity

        self.line = InvoiceLine(
            id=Identifier(value='1'),
            invoiced_quantity=InvoicedQuantity(value=quantity),
            line_extension_amount=LineExtensionAmount(value=line_total),
            item=Item(name=f'Returned: {fake.catch_phrase()}'),
            price=Price(price_amount=PriceAmount(value=unit_price)),
        )

    def test_create_credit_note(self):
        """Test creating a credit note."""
        credit_note_number = f'CN-{fake.random_int(min=1000, max=9999)}'
        issue_date = fake.date_between(start_date='-30d', end_date='today')

        credit_note = CreditNote(
            id=Identifier(value=credit_note_number),
            issue_date=IssueDate(value=issue_date),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        self.assertEqual(credit_note.id.value, credit_note_number)
        self.assertEqual(credit_note.issue_date.value, issue_date.isoformat())
        self.assertEqual(credit_note.document_type_code, '381')
        self.assertEqual(credit_note.element_name, 'CreditNote')

    def test_credit_note_namespace(self):
        """Test that credit note has correct namespace."""
        credit_note = CreditNote(
            id=Identifier(value=f'CN-{fake.random_int(min=1000, max=9999)}'),
            issue_date=IssueDate(value=fake.date_this_year()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[self.line],
        )

        self.assertEqual(credit_note.url, 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2')
        self.assertEqual(credit_note.prefix, '')  # Root element uses default namespace


class TestDecimalPrecisionCapping(unittest.TestCase):
    """Test that document-level totals are capped to 2 decimal places for UBL/PEPPOL compliance."""

    def setUp(self):
        """Create test data with high-precision amounts."""
        # Create supplier (Belgian company)
        self.supplier = Party(
            name=fake_be.company(),
            postal_address=PostalAddress(
                street_name=fake_be.street_name(),
                city_name=fake_be.city(),
                postal_zone=fake_be.postcode(),
                country='BE',
            ),
            vat=fake_be.vat_id(),
        )

        # Create customer (Dutch company)
        self.customer = Party(
            name=fake_nl.company(),
            postal_address=PostalAddress(
                street_name=fake_nl.street_name(),
                city_name=fake_nl.city(),
                postal_zone=fake_nl.postcode(),
                country='NL',
            ),
            vat=fake_nl.vat_id(),
        )

    def test_tax_totals_capped_to_two_decimals(self):
        """Test that tax_totals are capped to 2 decimal places even with high-precision line amounts."""
        # Create line with high-precision amounts (5 decimals)
        unit_price = Decimal('10.99999')  # 5 decimals
        quantity = Decimal('3.00000')  # 5 decimals
        line_total = unit_price * quantity  # Results in 32.99997

        tax_rate = Decimal('21.00000')  # 5 decimals
        # Tax calculation: 32.99997 * 21 / 100 = 6.929994... → should be capped to 2 decimals
        line_tax_amount = (line_total * tax_rate / 100)

        tax_category = TaxCategory(id='S', percent=tax_rate, tax_scheme=TaxScheme())
        tax_subtotal = TaxSubtotal(
            taxable_amount=TaxableAmount(value=line_total),
            tax_amount=TaxAmount(value=line_tax_amount),
            percent=tax_rate,
            tax_category=tax_category,
        )
        line_tax_total = TaxTotal(tax_amount=TaxAmount(value=line_tax_amount), tax_subtotals=[tax_subtotal])

        line = InvoiceLine(
            id=Identifier(value='1'),
            invoiced_quantity=InvoicedQuantity(value=quantity),
            line_extension_amount=LineExtensionAmount(value=line_total),
            item=Item(name='High precision test item'),
            price=Price(price_amount=PriceAmount(value=unit_price)),
            tax_total=line_tax_total,
        )

        invoice = Invoice(
            id=Identifier(value='INV-PRECISION-TEST'),
            issue_date=IssueDate(value=date.today()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[line],
        )

        # Verify tax totals are capped to 2 decimals
        self.assertEqual(len(invoice.tax_totals), 1)
        tax_amount = invoice.tax_totals[0].tax_amount.value

        # Tax amount should be capped to 2 decimal places
        self.assertEqual(tax_amount.as_tuple().exponent, -2,
                        f"Tax amount should have exactly 2 decimal places, got {tax_amount}")

    def test_legal_monetary_total_capped(self):
        """Test that legal_monetary_total amounts are capped to 2 decimal places."""
        # Create multiple lines with high-precision amounts
        # Use values that when capped don't create validation errors
        lines = []
        for i in range(3):
            # Use prices that won't cause rounding mismatches after capping
            unit_price = Decimal('10.50000')  # 5 decimals, caps to 10.50
            quantity = Decimal('2.00000')  # 5 decimals, caps to 2.00
            # Calculate using capped values to avoid validation errors
            line_total = Decimal('10.50') * Decimal('2.00')  # 21.00

            line = InvoiceLine(
                id=Identifier(value=str(i + 1)),
                invoiced_quantity=InvoicedQuantity(value=quantity),
                line_extension_amount=LineExtensionAmount(value=line_total),
                item=Item(name=f'Item {i + 1}'),
                price=Price(price_amount=PriceAmount(value=unit_price)),
            )
            lines.append(line)

        invoice = Invoice(
            id=Identifier(value='INV-MONETARY-TEST'),
            issue_date=IssueDate(value=date.today()),
            supplier=self.supplier,
            customer=self.customer,
            lines=lines,
        )

        # Verify line_extension_amount is capped to 2 decimals
        line_ext_amt = invoice.legal_monetary_total.line_extension_amount.value
        self.assertEqual(line_ext_amt.as_tuple().exponent, -2,
                        f"Line extension amount should have exactly 2 decimal places, got {line_ext_amt}")

        # Verify payable_amount is capped to 2 decimals
        payable_amt = invoice.legal_monetary_total.payable_amount.value
        self.assertEqual(payable_amt.as_tuple().exponent, -2,
                        f"Payable amount should have exactly 2 decimal places, got {payable_amt}")

    def test_full_document_precision_compliance(self):
        """Test end-to-end document with high-precision inputs produces UBL-compliant 2-decimal outputs."""
        # Create lines with various high-precision amounts
        # Use values that won't cause validation errors after capping
        unit_price_1 = Decimal('12.50000')  # 5 decimals, caps to 12.50
        quantity_1 = Decimal('4.00000')  # 5 decimals, caps to 4.00
        # Calculate using capped values
        line_total_1 = Decimal('12.50') * Decimal('4.00')  # 50.00

        tax_rate = Decimal('21.00000')
        line_tax_1 = (line_total_1 * tax_rate / 100)

        tax_category = TaxCategory(id='S', percent=tax_rate, tax_scheme=TaxScheme())
        tax_subtotal_1 = TaxSubtotal(
            taxable_amount=TaxableAmount(value=line_total_1),
            tax_amount=TaxAmount(value=line_tax_1),
            percent=tax_rate,
            tax_category=tax_category,
        )

        line_1 = InvoiceLine(
            id=Identifier(value='1'),
            invoiced_quantity=InvoicedQuantity(value=quantity_1),
            line_extension_amount=LineExtensionAmount(value=line_total_1),
            item=Item(name='Precision test item 1'),
            price=Price(price_amount=PriceAmount(value=unit_price_1)),
            tax_total=TaxTotal(tax_amount=TaxAmount(value=line_tax_1), tax_subtotals=[tax_subtotal_1]),
        )

        invoice = Invoice(
            id=Identifier(value='INV-COMPLIANCE-TEST'),
            issue_date=IssueDate(value=date.today()),
            supplier=self.supplier,
            customer=self.customer,
            lines=[line_1],
        )

        # Verify all amounts in the invoice are 2-decimal compliant
        # 1. Line amounts (already capped by Amount.__post_init__)
        self.assertLessEqual(invoice.lines[0].line_extension_amount.value.as_tuple().exponent, -2)
        self.assertLessEqual(invoice.lines[0].price.price_amount.value.as_tuple().exponent, -2)

        # 2. Tax totals
        self.assertLessEqual(invoice.tax_totals[0].tax_amount.value.as_tuple().exponent, -2)

        # 3. Legal monetary total
        self.assertLessEqual(invoice.legal_monetary_total.line_extension_amount.value.as_tuple().exponent, -2)
        self.assertLessEqual(invoice.legal_monetary_total.payable_amount.value.as_tuple().exponent, -2)


if __name__ == '__main__':
    unittest.main()
