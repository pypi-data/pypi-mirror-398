"""
Unit tests for BaseElement abstract class.
"""

import unittest
from dataclasses import dataclass, field
from typing import ClassVar

from lxml import etree

from ubl.models.common import BaseElement, CbcMixin


@dataclass
class TestBasicComponent(CbcMixin, BaseElement):
    """
    Concrete test class for testing BaseElement.

    This represents a simple basic component (like Amount or Identifier)
    with a single value property.
    """

    value: str


class TestBaseElementProperties(unittest.TestCase):
    """Test BaseElement class variables and properties."""

    def test_child_attr_names_property(self):
        """Test that child_attr_names is computed from class_name_to_attr."""

        # Create a test class with child mappings
        @dataclass
        class TestWithChildren(CbcMixin, BaseElement):
            value: str
            element_name: str = field(default="TestElement", kw_only=True)
            property_attr_names: ClassVar[list[str]] = ["value"]
            class_name_to_attr: ClassVar[dict[str, str]] = {
                "ChildA": "child_a",
                "ChildB": "child_b",
            }

        instance = TestWithChildren(value="test")
        self.assertEqual(set(instance.child_attr_names), {"child_a", "child_b"})

    def test_property_attr_names_defined(self):
        """Test that property_attr_names class variable is defined."""
        instance = TestBasicComponent(value="test")
        self.assertIsInstance(instance.property_attr_names, list)
        self.assertIn("value", instance.property_attr_names)


class TestToXMLMixin(unittest.TestCase):
    """Test XML serialization via ToXMLMixin."""

    def test_to_xml_creates_element(self):
        """Test that to_xml() creates an XML element."""
        component = TestBasicComponent(value="TestValue")
        xml_element = component.to_xml()

        self.assertIsInstance(xml_element, etree._Element)

    def test_to_xml_sets_element_name(self):
        """Test that element name is correctly set in XML."""

        class CustomElement(TestBasicComponent):
            pass

        component = CustomElement(value="TestValue")
        xml_element = component.to_xml()

        # Extract local name from QName
        tag_name = etree.QName(xml_element).localname
        self.assertEqual(tag_name, "CustomElement")

    def test_to_xml_sets_namespace(self):
        """Test that namespace is correctly set in XML."""
        component = TestBasicComponent(value="TestValue")
        xml_element = component.to_xml()

        # Extract namespace from QName
        namespace = etree.QName(xml_element).namespace
        self.assertIn("CommonBasicComponents", namespace)

    def test_to_xml_root_includes_used_namespaces(self):
        """Test that root element includes used namespace declarations."""
        component = TestBasicComponent(value="TestValue")
        xml_element = component.to_xml()

        # Check nsmap contains the namespace actually used (CBC for this component)
        nsmap = xml_element.nsmap
        self.assertIsNotNone(nsmap)
        self.assertIn("cbc", nsmap)
        # Should NOT include CAC since it's not used by this component
        self.assertNotIn("cac", nsmap)

    def test_to_xml_sets_text_content(self):
        """Test that value is set as text content for basic components."""
        component = TestBasicComponent(value="TestValue")
        xml_element = component.to_xml()

        self.assertEqual(xml_element.text, "TestValue")

    def test_to_xml_skips_none_values(self):
        """Test that None values are not included in XML."""

        # Create a component with optional attribute
        @dataclass
        class TestWithOptional(CbcMixin, BaseElement):
            value: str
            optional_attr: str | None = field(default=None, kw_only=True)
            element_name: str = field(default="TestElement", kw_only=True)
            property_attr_names: ClassVar[list[str]] = ["value", "optional_attr"]
            class_name_to_attr: ClassVar[dict[str, str]] = {}

        component = TestWithOptional(value="TestValue", optional_attr=None)
        xml_element = component.to_xml()

        # optional_attr should not appear as attribute
        self.assertIsNone(xml_element.get("optional_attr"))


class TestFromXMLMixin(unittest.TestCase):
    """Test XML parsing via FromXMLMixin."""

    def test_from_xml_parses_basic_element(self):
        """Test that from_xml() can parse a simple element."""
        # Create XML element
        xml_string = b"""
        <cbc:TestElement xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            TestValue
        </cbc:TestElement>
        """
        xml_element = etree.fromstring(xml_string)

        # Parse back to object
        component = TestBasicComponent.from_xml(xml_element)

        self.assertEqual(component.value, "TestValue")

    def test_from_xml_parses_text_content(self):
        """Test that text content is correctly parsed."""
        xml_string = b"""
        <cbc:TestElement xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            SomeTextValue
        </cbc:TestElement>
        """
        xml_element = etree.fromstring(xml_string)

        component = TestBasicComponent.from_xml(xml_element)
        self.assertEqual(component.value, "SomeTextValue")


if __name__ == "__main__":
    unittest.main()
