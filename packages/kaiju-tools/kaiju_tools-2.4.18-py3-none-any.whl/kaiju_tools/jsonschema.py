"""Python classes for jsonschema validators."""

import abc
from collections.abc import Callable, Collection
from datetime import date, datetime
from uuid import UUID

import fastjsonschema
from fastjsonschema import compile
from fastjsonschema.exceptions import JsonSchemaException

from kaiju_tools.encoding import Serializable


__all__ = (
    'STRING_FORMATS',
    'compile_schema',
    'JSONSchemaObject',
    'Enumerated',
    'Boolean',
    'String',
    'Number',
    'Integer',
    'Array',
    'Object',
    'Generic',
    'JSONSchemaKeyword',
    'AnyOf',
    'OneOf',
    'AllOf',
    'Not',
    'GUID',
    'Date',
    'DateTime',
    'Null',
    'Constant',
)


# This 'hack' allows to validate datetime and uuid objects as if they were formatted strings.


class _CodeGenerator(fastjsonschema.CodeGeneratorDraft07):
    """Patch for the code generator to accept datetime and uuid objects."""

    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self._extra_imports_lines.extend(['from uuid import UUID', 'from datetime import datetime, date'])
        self._extra_imports_objects.update({'UUID': UUID, 'datetime': datetime, 'date': date})


def _get_code_generator_class(schema):
    return _CodeGenerator


fastjsonschema._get_code_generator_class = _get_code_generator_class
fastjsonschema.draft04.JSON_TYPE_TO_PYTHON_TYPE['string'] = 'str, datetime, date, UUID'

#


class JSONSchemaObject(Serializable):
    """Base JSONSchema object."""

    type: str = None

    __slots__ = ('default', 'title', 'description', 'examples', 'enum', 'nullable')

    def __init__(
        self,
        *,
        title: str = None,
        description: str = None,
        default=...,
        examples: list = None,
        enum: list = None,
        nullable: bool = None,
    ):
        """Initialize.

        :param title: short description
        :param description: long description
        :param default: default value
        :param examples: value examples
        :param enum: accepted list of values
        :param nullable: not used
        """
        self.default = default
        self.title = title
        self.description = description
        self.examples = examples
        self.enum = enum
        self.nullable = nullable

    def _set_non_null_values(self, data, keys) -> None:
        for key in keys:
            value = getattr(self, key)
            if value is not None:
                if isinstance(value, JSONSchemaObject):
                    value = value.repr()
                data[key] = value

    def repr(self) -> dict:
        """Serialize."""
        data = {}
        if self.type:
            data['type'] = self.type
        self._set_non_null_values(data, ('title', 'description', 'examples', 'enum'))
        if self.default is not ...:
            data['default'] = self.default
        return data


class Boolean(JSONSchemaObject):
    """Boolean `True` or `False`."""

    type = 'boolean'


Enumerated = JSONSchemaObject  # compatibility, the base object has enum


# noinspection PyPep8Naming
class String(JSONSchemaObject):
    """Text/string data type."""

    type = 'string'
    format_: str = None

    STRING_FORMATS = frozenset(
        {
            'date-time',
            'time',
            'date',
            'email',
            'idn-email',
            'hostname',
            'idn-hostname',
            'ipv4',
            'ipv6',
            'uri',
            'uri-reference',
            'iri',
            'iri-reference',
            'regex',
        }
    )

    __slots__ = ('minLength', 'maxLength', 'pattern', 'format')

    def __init__(self, *, minLength: int = None, maxLength: int = None, pattern: str = None, format: str = None, **kws):
        """Initialize.

        :param args: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :params kws: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :param minLength: min string size
        :param maxLength: max string size
        :param pattern: regex pattern
        :param format: string format (not working?)
        """
        super().__init__(**kws)
        self.minLength = minLength
        self.maxLength = maxLength
        self.pattern = pattern
        if format and format not in self.STRING_FORMATS:
            raise JsonSchemaException(
                'Invalid string format "%s".' 'Must be one of: "%s".' % (format, list(self.STRING_FORMATS))
            )
        self.format = self.format_ if self.format_ else format

    def repr(self) -> dict:
        """Serialize."""
        data = super().repr()
        self._set_non_null_values(data, ('minLength', 'maxLength', 'pattern', 'format'))
        return data


class DateTime(String):
    """Datetime string alias."""

    format_ = 'date-time'
    __slots__ = tuple()


class Date(String):
    """Date string alias."""

    format_ = 'date'
    __slots__ = tuple()


class GUID(String):
    """UUID string alias."""

    format_ = 'uuid'
    __slots__ = tuple()


class Constant(Enumerated):
    """Value is a constant."""

    __slots__ = tuple()

    def __init__(self, const, **kws):
        """Initialize.

        :param args: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :params kws: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :param const: constant value
        """
        super().__init__(enum=[const], **kws)


class Null(Enumerated):
    """Null value only."""

    __slots__ = tuple()

    def __init__(self):
        """Initialize."""
        super().__init__(enum=[None])


# noinspection PyPep8Naming
class Number(JSONSchemaObject):
    """Numeric data type (use it for both float or integer params)."""

    type = 'number'
    __slots__ = ('multipleOf', 'minimum', 'exclusiveMinimum', 'maximum', 'exclusiveMaximum')

    def __init__(
        self,
        *,
        multipleOf: float = None,
        minimum: float = None,
        maximum: float = None,
        exclusiveMinimum: float = None,
        exclusiveMaximum: float = None,
        **kws,
    ):
        """Initialize.

        :param args: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :params kws: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :param multipleOf: value should be a multiplier of
        :param minimum: min allowed value
        :param maximum: max allowed value
        :param exclusiveMinimum: min allowed value (excl)
        :param exclusiveMaximum: max allowed value (excl)
        """
        super().__init__(**kws)
        self.multipleOf = multipleOf
        self.minimum = minimum
        self.maximum = maximum
        self.exclusiveMinimum = exclusiveMinimum
        self.exclusiveMaximum = exclusiveMaximum

    def repr(self) -> dict:
        """Serialize."""
        data = super().repr()
        self._set_non_null_values(data, ('multipleOf', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum'))
        return data


class Integer(Number):
    """Integer type."""

    type = 'integer'
    __slots__ = tuple()


# noinspection PyPep8Naming
class Array(JSONSchemaObject):
    """Array, list, set or tuple definition (depends on params)."""

    type = 'array'
    __slots__ = ('items', 'prefixItems', 'contains', 'additionalItems', 'uniqueItems', 'minItems', 'maxItems')

    def __init__(
        self,
        items: JSONSchemaObject = None,
        *,
        prefixItems: Collection[JSONSchemaObject] = None,
        contains: JSONSchemaObject = None,
        additionalItems: bool = None,
        uniqueItems: bool = None,
        minItems: int = None,
        maxItems: int = None,
        **kws,
    ):
        """Initialize.

        :params kws: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :param items: item type
        :param prefixItems: use this to create a tuple like structure with different types of items
        :param contains: a list should contain this type of objects
        :param additionalItems: allow additional items in the tuple
        :param uniqueItems: unique items - set
        :param minItems: min number of items
        :param maxItems: max number of items
        """
        super().__init__(**kws)
        self.items = items
        self.prefixItems = prefixItems
        self.contains = contains
        self.additionalItems = additionalItems
        self.uniqueItems = uniqueItems
        self.minItems = minItems
        self.maxItems = maxItems

    @staticmethod
    def _unpack_items(data: dict, key: str):
        if key in data:
            data[key] = [item.repr() for item in data[key]]

    def repr(self) -> dict:
        data = super().repr()
        self._set_non_null_values(
            data, ('items', 'prefixItems', 'contains', 'additionalItems', 'uniqueItems', 'minItems', 'maxItems')
        )
        for key in ('prefixItems',):
            self._unpack_items(data, key)
        return data


# noinspection PyPep8Naming
class Object(JSONSchemaObject):
    """JSON object (dictionary) definition."""

    type = 'object'
    __slots__ = (
        'properties',
        'propertyNames',
        'required',
        'patternProperties',
        'additionalProperties',
        'minProperties',
        'maxProperties',
    )

    def __init__(
        self,
        properties: dict[str, JSONSchemaObject] = None,
        *,
        patternProperties: dict[str, JSONSchemaObject] = None,
        propertyNames: dict = None,
        additionalProperties: bool = None,
        minProperties: int = None,
        maxProperties: int = None,
        required: list[str] = None,
        **kws,
    ):
        """Initialize.

        :params kws: see :py:class:`~kaiju_tools.jsonschema.JSONSchemaObject`
        :param properties: object attributes schema
        :param patternProperties: object attribute patterns schema
        :param propertyNames: allowed property names
        :param additionalProperties: allow additional attributes
        :param minProperties: min number of properties
        :param maxProperties: max number of properties
        :param required: list of required keys
        """
        super().__init__(**kws)
        self.properties = properties if properties else {}
        self.patternProperties = patternProperties
        self.propertyNames = propertyNames
        self.additionalProperties = additionalProperties
        self.minProperties = minProperties
        self.maxProperties = maxProperties
        self.required = required

    def repr(self) -> dict:
        """Serialize."""
        data = super().repr()
        self._set_non_null_values(
            data,
            (
                'properties',
                'propertyNames',
                'required',
                'patternProperties',
                'additionalProperties',
                'minProperties',
                'maxProperties',
            ),
        )
        data['properties'] = {key: value.repr() for key, value in data['properties'].items()}
        if 'patternProperties' in data:
            data['patternProperties'] = {key: value.repr() for key, value in data['patternProperties'].items()}
        return data


Generic = JSONSchemaObject  # compatibility


class JSONSchemaKeyword(JSONSchemaObject, abc.ABC):
    """Abstract class for JSON Schema specific logical keywords."""

    type: str = None
    __slots__ = ('items',)

    def __init__(self, *items: JSONSchemaObject):
        """Initialize."""
        super().__init__()
        self.items = items

    def repr(self) -> dict:
        """Serialize."""
        return {self.type: [item.repr() for item in self.items]}


class AnyOf(JSONSchemaKeyword):
    """Given data must be valid against any (one or more) of the given sub-schemas."""

    type = 'anyOf'
    __slots__ = tuple()


class OneOf(JSONSchemaKeyword):
    """Given data must be valid against exactly one of the given sub-schemas."""

    type = 'oneOf'
    __slots__ = tuple()


class AllOf(JSONSchemaKeyword):
    """Given data must be valid against all of the given sub-schemas."""

    type = 'allOf'
    __slots__ = tuple()


class Nullable(AnyOf):
    """Nullable value."""

    type = 'oneOf'
    __slots__ = tuple()

    def __init__(self, item: JSONSchemaObject, /):
        """Initialize."""
        super().__init__(item, Null())


class Not(JSONSchemaObject):
    """Reverse the condition."""

    __slots__ = ('item',)

    def __init__(self, item: JSONSchemaObject, /):
        """Initialize.

        :param item: schema to create negative condition from
        """
        super().__init__()
        self.item = item

    def repr(self):
        """Serialize."""
        return {'not': self.item.repr()}


STRING_FORMATS = {
    'uuid': r'^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}$'
}  # these are used by the fastjsonschema compiler to validate some specific data types


def compile_schema(validator: JSONSchemaObject | dict, /) -> Callable:
    """Compile JSONSchema object into a validator function."""
    if isinstance(validator, JSONSchemaObject):
        validator = validator.repr()
    return compile(validator, formats=STRING_FORMATS)
