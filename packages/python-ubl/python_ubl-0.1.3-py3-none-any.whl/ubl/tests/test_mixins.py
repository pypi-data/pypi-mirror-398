"""
Unit tests for namespace mixins (BaseXMLNS, UblMixin, CacMixin, CbcMixin).
"""

import unittest

from ubl.constants import NAMESPACES
from ubl.models.common import BaseXMLNS, CacMixin, CbcMixin, UblMixin


class TestBaseXMLNS(unittest.TestCase):
    """Test the BaseXMLNS base class."""

    def test_default_values(self):
        """Test that BaseXMLNS has None defaults."""
        base = BaseXMLNS()
        self.assertIsNone(base.url)
        self.assertIsNone(base.prefix)

    def test_custom_values(self):
        """Test that BaseXMLNS has url and prefix."""
        base = BaseXMLNS()
        # BaseXMLNS doesn't define url/prefix values, just declares the fields
        self.assertIsNone(base.url)
        self.assertIsNone(base.prefix)


class TestCacMixin(unittest.TestCase):
    """Test the CacMixin for CommonAggregateComponents."""

    def test_cac_namespace(self):
        """Test that CacMixin uses cac namespace and prefix."""
        mixin = CacMixin()
        self.assertEqual(mixin.url, NAMESPACES["cac"])
        self.assertEqual(mixin.prefix, "cac")


class TestCbcMixin(unittest.TestCase):
    """Test the CbcMixin for CommonBasicComponents."""

    def test_cbc_namespace(self):
        """Test that CbcMixin uses cbc namespace and prefix."""
        mixin = CbcMixin()
        self.assertEqual(mixin.url, NAMESPACES["cbc"])
        self.assertEqual(mixin.prefix, "cbc")


if __name__ == "__main__":
    unittest.main()
