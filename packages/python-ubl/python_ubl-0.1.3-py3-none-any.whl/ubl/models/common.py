"""
Common base classes and mixins for UBL models.

This module provides the foundational infrastructure for all UBL models:
- Namespace management (BaseXMLNS and namespace mixins)
- XML serialization (ToXMLMixin)
- XML parsing (FromXMLMixin)
- Abstract base class (BaseElement)
"""

from abc import ABC
from copy import copy
from dataclasses import dataclass, field, fields, is_dataclass, _FIELD_INITVAR
from functools import lru_cache
from typing import Any, ClassVar, get_origin, get_args, List, Dict, Optional, Union

from lxml import etree

from ..constants import NAMESPACES
from ..exceptions import ParsingError, SerializationError


@dataclass
class BaseXMLNS:
    """
    Base class for namespace management.

    Attributes:
        url: Namespace URL (None if not set)
        prefix: XML namespace prefix (None or empty string for default namespace)
    """

    url: str | None = field(default=None, init=False, repr=False)
    prefix: str | None = field(default=None, init=False, repr=False)

    def _super_post_init(self, parent, *args, **kwargs):
        """
        Call parent's __post_init__ if it exists.

        Args:
            parent: The super() object from the calling class
            *args, **kwargs: Arguments to pass to parent's __post_init__
        """
        super_post_init = getattr(parent, '__post_init__', None)
        if super_post_init and callable(super_post_init):
            return super_post_init(*args, **kwargs)

        return args, kwargs


@dataclass
class SimpleTypeCastMixin:
    """Mixin for dataclasses that contain simple types (str, int, Decimal, etc.)"""

    auto_cast = True  # Class attribute (not a dataclass field)

    def __post_init__(self, *args, **kwargs):

        if self.auto_cast:
            for field_ in fields(self):
                # Skip fields with init=False (they don't exist yet)
                if not field_.init:
                    continue

                value = getattr(self, field_.name)

                # Skip generic types (list[X], dict[X,Y], etc.) - they're handled by AutoCastDataclassMixin
                origin = get_origin(field_.type)
                if origin is not None:
                    continue

                if isinstance(value, field_.type):
                    continue

                setattr(self, field_.name, self._simple_cast(value, field_.type, field_.name))

        self._super_post_init(super(), *args, **kwargs)

    def _simple_cast(self, value, expected_type, field_name):
        try:
            return expected_type(value)
        except Exception as e:
            raise TypeError(
                f'Cannot cast field "{field_name}" from {type(value).get("__name__", "None")} to {expected_type.__name__}: {e}'
            )


@dataclass
class AutoCastDataclassMixin(SimpleTypeCastMixin):

    def __post_init__(self, *args, **kwargs):
        if self.auto_cast:
            args, kwargs = self._cast_init_vars(*args, **kwargs)
            self._cast_fields()

        rv = self._super_post_init(super(), *args, **kwargs)
        if rv is None:
            return args, kwargs
        return rv

    def _cast_value(self, value, expected_type, field_name):
        if value is None:
            return None

        # Get the origin type (List, Dict, Union, etc.) and arguments (inner types)
        origin = get_origin(expected_type)
        args = get_args(expected_type)

        dedicated_cast = getattr(
            self,
            f'_cast_value_{getattr(origin, "__name__", "None").lower()}',
            self._default_cast_value
        )
        return dedicated_cast(expected_type, args, value, field_name)

    def _cast_value_list(self, expected_type, args, value, field_name):
        if args:
            inner_type = args[0]
            return [
                self._cast_value(item, inner_type, f'{field_name}[{i}]')
                for i, item in enumerate(value)
            ]

        return value

    def _cast_value_dict(self, expected_type, args, value, field_name):
        if args and len(args) == 2:
            key_type, val_type = args
            return {
                self._cast_value(k, key_type, f"{field_name}.key"):
                self._cast_value(v, val_type, f"{field_name}[{k}]")
                for k, v in value.items()
            }

        return value

    def _cast_value_uniontype(self, expected_type, args, value, field_name):
        return self._cast_value_union(expected_type, args, value, field_name)

    def _cast_value_union(self, expected_type, args, value, field_name):
        non_none_types = [arg for arg in args if arg is not type(None)]

        if len(non_none_types) == 1:
            # Optional[X] → just handle X
            target_type = non_none_types[0]
            try:
                needs_cast = not isinstance(value, target_type)
            except TypeError:
                # taget_type is a generic
                needs_cast = True
            if not needs_cast:
                return value  # Already correct type
            # Try to cast to target type
            return self._cast_value(value, target_type, field_name)

        if len(non_none_types) > 1:
            # Complex union like Union[str, int] - not supported yet
            raise NotImplementedError(f'Cannot cast "{field_name}" to complex Union types like {non_none_types}')

        return value

    def _default_cast_value(self, expected_type, args, value, field_name):
        if is_dataclass(value) and is_dataclass(expected_type) and issubclass(expected_type, type(value)):
            if hasattr(value, '__as__'):
                # XML Element casting only
                return value.__as__(expected_type.__name__)
            else:
                try:
                    return expected_type(**{
                        f.name: getattr(value, f.name)
                        for f in fields(value)
                        if f.init
                    })
                except Exception as e:
                    raise TypeError(f'Unable to cast {type(value).__name__} to {expected_type.__name__}: {e}')

        # SimpleTypeCastMixin will handle straight-forward casting
        return self._simple_cast(value, expected_type, field_name)

    def _cast_fields(self):
        for field_ in fields(self):
            # Skip fields with init=False (they don't exist yet at this point)
            if not field_.init:
                continue

            # Skip if field doesn't exist (shouldn't happen but defensive)
            if not hasattr(self, field_.name):
                continue

            value = getattr(self, field_.name)

            # For generic types (like list[Something]), we can't use isinstance directly
            # So we always call _cast_value and let it handle the logic
            origin = get_origin(field_.type)
            if origin is not None:
                # It's a generic type, always try to cast
                casted_value = self._cast_value(value, field_.type, field_.name)
            else:
                # Non-generic type, check isinstance first
                casted_value = self._cast_value(value, field_.type, field_.name) \
                    if not isinstance(value, field_.type) \
                    else value

            if casted_value is not value:
                setattr(self, field_.name, casted_value)

    def _cast_init_vars(self, *args, **kwargs):
        args = list(args)

        all_fields = self.__dataclass_fields__
        # init_vars are the only ones that will be passed to __post_init__
        # so the only one in args and kwargs.
        init_vars = [f for f in all_fields.values() if f._field_type == _FIELD_INITVAR]

        for i, field_ in enumerate(init_vars):
            key = None
            if i < len(args):
                value = args[i]
            elif field_.name in kwargs:
                key = field_.name
                value = kwargs[field_.name]
            else:
                continue

            casted_value = value
            try:
                needs_cast = not isinstance(value, field_.type.type)
            except TypeError:
                # field_.type.type is a generic Type and doesn't work with isinstance
                needs_cast = True

            if needs_cast:
                casted_value = self._cast_value(value, field_.type.type, field_.name)

            if casted_value is not value:
                if key is None:
                    args[i] = casted_value
                else:
                    kwargs[key] = casted_value

        return args, kwargs


@dataclass
class UblMixin(BaseXMLNS, AutoCastDataclassMixin):
    """
    Mixin for UBL root namespace elements (Invoice, CreditNote).

    Uses default namespace (no prefix) for root elements.
    Note: Root elements should set their namespace dynamically in __post_init__
    based on element_name (invoice or creditnote).
    """

    url: str | None = field(default='', init=False, repr=False)
    prefix: str | None = field(default='', init=False, repr=False)


@dataclass
class CacMixin(BaseXMLNS, AutoCastDataclassMixin):
    """
    Mixin for CommonAggregateComponents namespace elements.

    Used for complex nested structures like Party, Address, TaxCategory, etc.
    """

    url: str | None = field(default=NAMESPACES['cac'], init=False, repr=False)
    prefix: str | None = field(default='cac', init=False, repr=False)


@dataclass
class CbcMixin(BaseXMLNS, SimpleTypeCastMixin):
    """
    Mixin for CommonBasicComponents namespace elements.

    Used for primitive/scalar elements like Amount, Identifier, Code, Date, etc.
    """

    url: str | None = field(default=NAMESPACES['cbc'], init=False, repr=False)
    prefix: str | None = field(default='cbc', init=False, repr=False)


class ToXMLMixin:
    """
    Mixin providing XML serialization capabilities.

    This mixin converts dataclass instances to lxml Element objects,
    handling namespaces, attributes, and nested elements.
    """

    # Required attributes (provided by BaseElement or subclass)
    # Note: While typed as optional, concrete classes must provide these values
    url: str | None
    prefix: str | None
    element_name: str | None
    # property_attr_names: computed as @property in BaseElement
    # child_attr_names: computed as @property in BaseElement

    def to_xml(self, parent: etree.Element | None = None) -> etree.Element:
        """
        Convert this dataclass to an XML element.

        Args:
            parent: Optional parent element. If None, creates root element with all namespaces.

        Returns:
            lxml Element representing this object

        Raises:
            SerializationError: If XML generation fails
        """
        try:
            # Validate required fields
            if self.element_name is None:
                raise SerializationError(f'{self.__class__.__name__}: element_name is required for XML serialization')
            if self.url is None:
                raise SerializationError(
                    f'{self.__class__.__name__}: url (namespace) is required for XML serialization',
                )

            # Build tag name with namespace
            tag_name = f'{{{self.url}}}{self.element_name}'

            # Create element
            if parent is None:
                # Root element - collect and include namespace declarations
                namespace_tuples = self._collect_all_namespaces()
                nsmap = {(None if prefix == '' else prefix): url for url, prefix in namespace_tuples}
                element = etree.Element(tag_name, nsmap=nsmap)
            else:
                # Child element - append to parent
                element = etree.SubElement(parent, tag_name)

            # Add properties (attributes or text content)
            self._apply_properties(element)

            # Add child elements
            self._collect_children(element)

            return element

        except Exception as e:
            raise SerializationError(f'Failed to serialize {self.__class__.__name__}: {e}') from e

    def _collect_all_namespaces(self) -> set[tuple[str, str]]:
        """
        Recursively collect all namespaces used in this element tree.

        Returns:
            Set of (url, prefix) tuples for all namespaces actually used
        """
        namespaces = set()

        # Add this element's namespace
        if self.url:
            namespaces.add((self.url, self.prefix))

        # Recursively collect from children
        for attr_name in self.child_attr_names:
            child = getattr(self, attr_name, None)

            if child is None:
                continue

            # Handle lists of children
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, '_collect_all_namespaces'):
                        namespaces.update(item._collect_all_namespaces())
            # Handle single child
            elif hasattr(child, '_collect_all_namespaces'):
                namespaces.update(child._collect_all_namespaces())

        return namespaces

    def _apply_properties(self, element: etree.Element) -> None:
        """
        Apply properties (dataclass fields) as XML attributes or text content.

        For basic components (CBC), the "value" field becomes text content,
        and other fields become attributes (e.g., currencyID, schemeID).

        PEPPOL/CEN UBL-CR rules prohibit certain attributes:
        - UBL-CR-652: PartyTaxScheme CompanyID schemeID
        - UBL-CR-656, 657, 660, 661: Various listID attributes
        - UBL-CR-663: unitCodeListID
        - UBL-DT-08: schemeName attributes
        - UBL-DT-28: listAgencyID attributes

        Args:
            element: The XML element to populate
        """
        from ..context import is_peppol_mode

        # Attributes forbidden in PEPPOL mode
        peppol_forbidden_attrs = {
            'listID', 'schemeName', 'listAgencyID', 'unitCodeListID'
        }

        for attr_name in self.property_attr_names:
            value = getattr(self, attr_name, None)

            # Skip None values (don't create empty elements)
            if value is None:
                continue

            # PEPPOL mode: Skip forbidden attributes
            if is_peppol_mode() and attr_name in peppol_forbidden_attrs:
                continue

            # PEPPOL mode UBL-CR-652: Skip schemeID for PartyTaxScheme/CompanyID
            if is_peppol_mode() and attr_name == 'schemeID':
                # Check if this is a CompanyID in PartyTaxScheme context
                if hasattr(self, 'element_name') and self.element_name == 'CompanyID':
                    # Check parent context - skip if we're in PartyTaxScheme
                    # For now, we'll keep schemeID for CompanyID since it's needed for BR-CL-10/11
                    # The warning UBL-CR-652 is less critical than the error BR-CL-10
                    pass

            # Convert value to string
            str_value = self._format_value(value)

            # For basic components: "value" becomes text content, others become attributes
            if hasattr(self, 'prefix') and self.prefix == 'cbc' and attr_name == 'value':
                element.text = str_value
            else:
                # Set as attribute (for things like currencyID, schemeID, unitCode, etc.)
                element.set(attr_name, str_value)

    def _collect_children(self, element: etree.Element) -> None:
        """
        Collect and append child elements.

        Args:
            element: The parent XML element
        """
        for attr_name in self.child_attr_names:
            child = getattr(self, attr_name, None)

            # Skip None values
            if child is None:
                continue

            # Handle lists of children
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, 'to_xml'):
                        item.to_xml(parent=element)
            # Handle single child
            elif hasattr(child, 'to_xml'):
                child.to_xml(parent=element)

    def _format_value(self, value: Any) -> str:
        """
        Format a Python value for XML output.

        Args:
            value: The value to format

        Returns:
            String representation suitable for XML
        """
        from datetime import date
        from decimal import Decimal

        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)


class WithAsMixin:
    """Mixin for ToXML subclasses that can be "casted" to another XML element type"""

    def __as__(self, new_element_name):
        casted = copy(self)
        if 'element_name' in casted.__dict__:
            # Actual attribute
            casted.element_name = new_element_name
        else:
            # Assuming default behaviour of @property
            casted._element_name = new_element_name
        return casted


class ValueStrMixin:
    """
    Mixin that provides string representation via value attribute.

    Used by basic components that have a 'value' field and should
    be stringifiable to that value (e.g., Name, IdentificationCode).

    The concrete class must declare the 'value' field.
    """

    def __str__(self) -> str:
        """Return string representation of value."""
        return str(self.value)


class FromXMLMixin:
    """
    Mixin providing XML parsing capabilities.

    This mixin converts lxml Element objects back to dataclass instances.
    """

    # Required attributes (provided by BaseElement or subclass)
    class_name_to_attr: ClassVar[dict[str, str]]
    # property_attr_names: computed as @property in BaseElement

    @classmethod
    def from_xml(cls, element: etree.Element) -> 'FromXMLMixin':
        """
        Parse an XML element into a dataclass instance.

        Args:
            element: lxml Element to parse

        Returns:
            Instance of this class populated from XML

        Raises:
            ParsingError: If XML parsing fails
        """
        try:
            kwargs = {}

            # Parse properties (attributes and text content)
            for attr_name in cls._get_property_attr_names():
                value = None

                # For basic components, "value" field comes from text content
                if attr_name == 'value' and element.text:
                    value = element.text.strip()
                else:
                    # All other fields come from attributes
                    value = element.get(attr_name)

                # Store if found
                if value is not None:
                    kwargs[attr_name] = cls._parse_value(attr_name, value)

            # Parse child elements
            for child in element:
                # Get tag name without namespace
                tag = etree.QName(child).localname

                # Look up corresponding attribute name
                attr_name = cls.class_name_to_attr.get(tag)
                if attr_name is None:
                    # Unknown child element - skip
                    continue

                # Get the child class dynamically (cached)
                child_class = cls._get_element_class(tag)

                # Recursively parse child
                child_obj = child_class.from_xml(child)

                # Check if this is a list field
                is_list = cls._is_list_field(attr_name)

                if is_list:
                    # List field: create list if doesn't exist, then append
                    if attr_name not in kwargs:
                        kwargs[attr_name] = []
                    kwargs[attr_name].append(child_obj)
                else:
                    # Scalar field: assign directly
                    kwargs[attr_name] = child_obj

            # Filter out fields with init=False (auto-generated fields)
            filtered_kwargs = cls.filter_kwargs(kwargs)

            # Disable auto_cast during XML deserialization
            orig = cls.auto_cast
            cls.auto_cast = False
            rv = cls(**filtered_kwargs)
            cls.auto_cast = orig
            return rv

        except Exception as e:
            raise ParsingError(f'Failed to parse {cls.__name__}: {e}') from e

    @classmethod
    def filter_kwargs(cls, kwargs):
        init_fields = cls.get_init_fields()
        return {k: v for k, v in kwargs.items() if k in init_fields}

    @classmethod
    def get_init_fields(cls):
        return {f.name for f in fields(cls) if f.init}

    @classmethod
    def _is_list_field(cls, attr_name: str) -> bool:
        """Check if a field is declared as list[X]."""
        for f in fields(cls):
            if f.name == attr_name:
                origin = get_origin(f.type)
                return origin is list
        return False

    @classmethod
    @lru_cache(maxsize=128)
    def _get_element_class(cls, tag_name: str):
        """Get element class from XML tag name (cached)."""
        from . import basic_components

        try:
            from . import aggregate_components
        except ImportError:
            aggregate_components = None

        # Try basic components first
        child_class = getattr(basic_components, tag_name, None)
        if child_class is None and aggregate_components is not None:
            child_class = getattr(aggregate_components, tag_name, None)

        if child_class is None:
            raise ParsingError(f'Unknown child element class: {tag_name}')

        return child_class

    @classmethod
    def _parse_value(cls, attr_name: str, value: str) -> Any:
        """
        Parse a string value from XML into the appropriate Python type.

        Args:
            attr_name: Name of the attribute
            value: String value from XML

        Returns:
            Parsed value in appropriate Python type
        """
        from datetime import date
        from decimal import Decimal

        # Get the field type from dataclass definition
        for f in fields(cls):
            if f.name == attr_name:
                field_type = f.type

                # Handle Optional types
                if hasattr(field_type, '__origin__'):
                    # For Optional[X], extract X
                    field_type = field_type.__args__[0]

                # Parse based on type
                if field_type == Decimal:
                    return Decimal(value)
                if field_type == date:
                    return date.fromisoformat(value)
                if field_type == bool:
                    return value.lower() in ('true', '1')
                if field_type == int:
                    return int(value)
                if field_type == float:
                    return float(value)
                return value

        # Default: return as string
        return value


@dataclass
class BaseElement(BaseXMLNS, ToXMLMixin, FromXMLMixin, SimpleTypeCastMixin, ABC):
    """
    Abstract base class for all UBL elements.

    This class combines namespace management, XML serialization,
    and XML parsing capabilities. All UBL model classes should
    inherit from this class.

    Subclasses must define:
        - property_attr_names: List of dataclass fields that become XML attributes/text
        - class_name_to_attr: Dict mapping XML tag names to dataclass attribute names
        - element_name: Name of the XML element
    """

    # Class variables that subclasses must define
    class_name_to_attr: ClassVar[dict[str, str]] = {}

    # Optional: InitVar processing priority (for components with InitVars)
    init_vars_priority: ClassVar[list[str] | None] = None

    @property
    def element_name(self) -> str:
        """
        Get the XML element name for this component.

        By default, returns the class name. Subclasses can override this
        property to provide custom element names or set `_element_name`.

        Returns:
            The XML element name (e.g., "Amount", "TaxAmount", "Party")
        """
        return getattr(self, '_element_name', self.__class__.__name__)

    @classmethod
    def _get_property_attr_names(cls) -> list[str]:
        """
        Compute property attribute names for this class.

        This is a classmethod so it can be called during parsing (from_xml).

        If this class declares its own fields, returns only those fields.
        If this class declares no fields (e.g., subclass with only element_name change),
        delegates to the single parent class. Raises an error if multiple parents.

        Always excludes:
        - XML metadata fields (url, prefix)
        - Child element fields (values in class_name_to_attr)
        - ClassVar fields

        For example:
        - Amount declares value, currencyID -> ["value", "currencyID"]
        - TaxAmount(Amount) declares nothing -> delegates to Amount

        Returns:
            List of field names to serialize as XML attributes/text

        Raises:
            ValueError: If class declares no fields and has multiple parents
        """
        from dataclasses import fields, is_dataclass

        if not is_dataclass(cls):
            return []

        # Check if this class declares its own fields
        own_field_names = set(cls.__annotations__.keys()) if hasattr(cls, '__annotations__') else set()

        # Metadata fields to exclude from serialization
        metadata_fields = {'url', 'prefix'}

        # Child element fields to exclude (they're serialized as child elements)
        # Access base mapping if property-based, otherwise use ClassVar
        if hasattr(cls, '_base_class_name_to_attr'):
            child_fields = set(cls._base_class_name_to_attr.values())
        elif hasattr(cls, 'class_name_to_attr'):
            # Check if it's a property or ClassVar
            if isinstance(getattr(cls, 'class_name_to_attr', None), property):
                # Cannot access property from classmethod, try base class
                child_fields = set()
                for base in cls.__mro__[1:]:
                    if hasattr(base, '_base_class_name_to_attr'):
                        child_fields = set(base._base_class_name_to_attr.values())
                        break
                    elif hasattr(base, 'class_name_to_attr') and not isinstance(getattr(base, 'class_name_to_attr', None), property):
                        child_fields = set(base.class_name_to_attr.values())
                        break
            else:
                child_fields = set(cls.class_name_to_attr.values())
        else:
            child_fields = set()

        # If class declares its own fields, use only those
        if own_field_names:
            # Get actual dataclass fields (excludes ClassVar)
            actual_field_names = {f.name for f in fields(cls)}

            result = [
                name
                for name in own_field_names
                if name in actual_field_names and name not in metadata_fields and name not in child_fields
            ]
        else:
            # No fields declared - delegate to single parent class
            # Get direct parent classes (excluding object)
            parents = [base for base in cls.__bases__ if base is not object]

            if len(parents) == 0:
                return []
            if len(parents) == 1:
                # Delegate to single parent
                return parents[0]._get_property_attr_names()
            # Multiple inheritance without own fields is ambiguous
            raise ValueError(
                f'{cls.__name__} declares no fields but has multiple parent classes. '
                f"Cannot determine which parent's fields to use.",
            )

        return result

    @property
    def property_attr_names(self) -> list[str]:
        """
        Get property attribute names for this instance.

        This is a convenience property that calls the classmethod.

        Returns:
            List of field names to serialize as XML attributes/text
        """
        return self._get_property_attr_names()

    @property
    def child_attr_names(self) -> list[str]:
        """
        Get list of attribute names for child elements.

        This is computed from class_name_to_attr values.

        Returns:
            List of attribute names representing child elements
        """
        return list(self.class_name_to_attr.values())

    def _deserialize_item(self, item):
        """
        Deserialize a single component and set its attributes on self.

        If the item has a deserialize() method, calls it and sets each
        returned attribute on self using setattr().

        Args:
            item: Component instance with optional deserialize() method
        """
        if hasattr(item, 'deserialize'):
            for attr, val in item.deserialize().items():
                setattr(self, attr, val)

    def _process_init_vars(self, **kwargs):
        """
        Process InitVars with priority-based deserialization.

        Loops through init_vars_priority in reverse order (last = highest priority),
        deserializes each component by calling its .deserialize() method, and sets
        returned attributes on self.

        This enables components to use InitVars for XML parsing while maintaining
        clean separation between parsing logic and domain logic.

        Args:
            **kwargs: InitVar values to process (typically passed from __post_init__)
        """
        priority_list = self.init_vars_priority or []
        for var_name in reversed(priority_list):
            value = kwargs.get(var_name)
            if value is None:
                continue

            # Handle lists of components
            if isinstance(value, list):
                for item in value:
                    self._deserialize_item(item)
            else:
                self._deserialize_item(value)
