"""Python annotation parser can convert type annotations into JSONSchema objects.

.. seealso:: :py:class:`~kaiju_base.jsonschema.JSONSchemaObject`

It deals with magic so a few noqa have been tolerated.

Use the annotation parser
^^^^^^^^^^^^^^^^^^^^^^^^^

Imagine you have a sevice with some public methods which input you would like to validate on each call. Or maybe you'd
like to document these methods input.

>>> class DataService:
...     async def get_items(self, item_ids: list[str], columns: list[str] = None) -> list[dict]:
...         pass

You can create JSONSchema objects from these methods by calling
:py:meth:`~kaiju_base.annotations.AnnotationParser.parse_function_annotations`. The returned result is a tuple
containing input and output data schemas.

>>> parser = AnnotationParser()
>>> schema = parser.parse_function_annotations(DataService, DataService.get_items)
>>> schema # doctest: +ELLIPSIS
(<Object(**{...})>, <Array(**{...})>)

You can then validate any incoming data by compiling the schema into a validation function.

>>> input_schema, output_schema = schema
>>> validator = j.compile_schema(input_schema)
>>> validator({'item_ids': ['a', 'b', 3]})
Traceback (most recent call last):
...
fastjsonschema.exceptions.JsonSchemaValueException: data.item_ids[2] must be string

The other way (which the RPC server uses) is to get the full method description using
:py:meth:`~kaiju_base.annotations.AnnotationParser.parse_method`.

>>> parser.parse_method(DataService, 'method_route', DataService.get_items) # doctest: +ELLIPSIS
{'title': ..., 'description': ..., 'documentation': ..., 'params': <Object(**{...})>, 'returns': <Array(**{...})>}

"""

import abc
import enum
import inspect
import sys
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import MISSING, dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from inspect import _ParameterKind  # noqa: magic is required
from numbers import Number
from textwrap import dedent
from types import SimpleNamespace, UnionType
from typing import _GenericAlias  # noqa: magic is required
from typing import _TypedDictMeta  # noqa: magic is required
from typing import (
    Literal,
    NamedTuple,
    NewType,
    NotRequired,
    Required,
    Set,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID, SafeUUID

import kaiju_tools.jsonschema as j
from kaiju_tools.registry import ClassRegistry


__all__ = ['AnnotationParser', 'FunctionAnnotation', 'TYPE_PARSERS', 'MethodSignatureError']


NoneType = type(None)


def is_generic(value) -> bool:
    """Check if an object is a generic."""
    return isinstance(value, _GenericAlias)


def get_generic_alias(obj: type) -> _GenericAlias | None:
    return next((n for n in getattr(obj, '__orig_bases__', []) if is_generic(n)), None)


def is_typeddict(value) -> bool:
    """Check if an object is a typed dict."""
    return isinstance(value, _TypedDictMeta)


def is_namedtuple(value) -> bool:
    """Check if a value is a named tuple."""
    return inspect.isclass(value) and issubclass(value, tuple) and hasattr(value, '_fields')


def is_union_type(value) -> bool:
    """Check if an object is a union."""
    return getattr(value, '__origin__', None) is Union or type(value) is UnionType


class MethodSignatureError(Exception):
    """Method signature does not match the current RPC specification."""


class FunctionAnnotation(TypedDict):
    """Function annotation data."""

    title: str
    description: str
    documentation: str
    params: j.JSONSchemaObject
    returns: j.JSONSchemaObject


class AnnotationParser:
    """Parser for python annotations."""

    @classmethod
    def parse_method(cls, service_cls: type, route: str, method: Callable, /) -> FunctionAnnotation:
        """Parse public route and method."""
        params, returns = cls.parse_function_annotations(service_cls, method)
        doc = inspect.getdoc(method)
        annotation = FunctionAnnotation(
            title=route,
            description=cls.get_function_short_description(doc),
            documentation=doc,
            params=params,
            returns=returns,
        )
        return annotation

    @classmethod
    def get_function_short_description(cls, doc: str | None, /) -> str | None:
        """Extract and normalize function description (first row)."""
        if doc:
            doc = dedent(doc)
            doc = doc.split('\n')[0]
            doc.capitalize()
            return doc

    @classmethod
    def parse_function_annotations(
        cls, service_cls: type, f: Callable
    ) -> tuple[j.JSONSchemaObject, j.JSONSchemaObject]:
        """Parse function arguments and result into jsonschema objects."""
        sign = inspect.signature(f)
        params, required = {}, []
        additional_properties = False
        for name, arg in sign.parameters.items():
            if name.startswith('_'):
                continue
            elif name in {'self', 'cls', 'mcs'}:
                continue
            elif arg.kind == _ParameterKind.VAR_POSITIONAL:
                continue  # *args (skipped because positionals not allowed in our server)
            elif arg.kind == _ParameterKind.VAR_KEYWORD:
                additional_properties = True
                continue  # **kws (means you can pass any keys)
            elif arg.kind == _ParameterKind.POSITIONAL_ONLY:
                raise MethodSignatureError('Invalid RPC method signature: POSITIONAL ONLY arguments not allowed.')
            elif type(arg.annotation) is TypeVar:
                annotation = cls.parse_generic_alias(service_cls, arg.annotation)
            else:
                annotation = arg.annotation
            if arg.default == arg.empty:
                default = ...
                required.append(name)
            else:
                default = arg.default
            params[name] = cls.parse_annotation(annotation, default)
        if params:
            params = j.Object(properties=params, required=required, additionalProperties=additional_properties)
        else:
            params = None
        returns = cls.parse_annotation(sign.return_annotation, ..., returns_only=True)
        return params, returns

    @staticmethod
    def parse_annotation(annotation, /, default=..., returns_only: bool = False) -> j.JSONSchemaObject:
        """Convert python annotation into a jsonschema object."""
        for parser in TYPE_PARSERS.values():
            if not returns_only and parser.returns_only:
                continue
            if parser.can_parse(annotation):
                annotation = parser.parse_annotation(annotation)
                break
        else:
            if annotation == inspect._empty:  # noqa: no public attr here
                title = None
            else:
                title = str(annotation)
            annotation = j.JSONSchemaObject(title=title)
        if default is not ...:
            annotation.default = default
        return annotation

    @staticmethod
    def parse_generic_alias(service_cls, annotation):
        """Parse a class containing Generic hints in itself."""
        alias = base_alias = get_generic_alias(service_cls)
        args = base_args = alias.__args__
        while base_alias:
            base_args = base_alias.__args__
            base_cls = base_alias.__origin__
            base_alias = get_generic_alias(base_cls)
        try:
            annotation = args[base_args.index(annotation)]
        except (ValueError, IndexError):
            pass
        return annotation


class TypeParser(abc.ABC):
    returns_only: bool = False  # use this parser only when parsing a return value

    @classmethod
    @abc.abstractmethod
    def can_parse(cls, annotation, /) -> bool: ...

    @classmethod
    @abc.abstractmethod
    def parse_annotation(cls, annotation, /) -> j.JSONSchemaObject: ...

    @classmethod
    def get_origin(cls, annotation, /):
        return getattr(annotation, '__origin__', None)

    @classmethod
    def get_args(cls, annotation, /):
        return getattr(annotation, '__args__', None)

    @classmethod
    def is_generic(cls, annotation, /) -> bool:
        return is_generic(annotation)

    @classmethod
    def is_union_type(cls, annotation, /) -> bool:
        return is_union_type(annotation)

    @classmethod
    def parse_args(cls, args, /):
        if args:
            for arg in args:
                if arg is not ...:
                    yield AnnotationParser.parse_annotation(arg)


class SimpleTypeParser(TypeParser, abc.ABC):
    _types: set[type]
    _annotation_class: type[j.JSONSchemaObject]
    _attrs: dict = None

    @classmethod
    def can_parse(cls, annotation) -> bool:
        origin = cls.get_origin(annotation)
        if origin:
            return origin in cls._types
        else:
            return annotation in cls._types

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        _attrs = {} if cls._attrs is None else cls._attrs
        return cls._annotation_class(**_attrs)  # noqa


class StringParser(SimpleTypeParser):
    """Parse a python string.

    >>> StringParser().parse_annotation(str) # doctest: +ELLIPSIS
    <String(**{...})>

    """

    _types = {str, bytes}
    _annotation_class = j.String


class UUIDParser(SimpleTypeParser):
    """Parse an UUID string or object.

    >>> UUIDParser().parse_annotation(UUID) # doctest: +ELLIPSIS
    <GUID(**{...})>

    """

    _types = {UUID, SafeUUID}
    _annotation_class = j.GUID


class DateParser(SimpleTypeParser):
    """Parse a date object.

    >>> DateParser().parse_annotation(date) # doctest: +ELLIPSIS
    <Date(**{...})>

    """

    _types = {date}
    _annotation_class = j.Date


class DateTimeParser(SimpleTypeParser):
    """Parse a date object.

    >>> DateTimeParser().parse_annotation(datetime) # doctest: +ELLIPSIS
    <DateTime(**{...})>

    """

    _types = {datetime}
    _annotation_class = j.DateTime


class IntegerParser(SimpleTypeParser):
    """Parse an integer object.

    >>> IntegerParser().parse_annotation(int) # doctest: +ELLIPSIS
    <Integer(**{...})>

    """

    _types = {int}
    _annotation_class = j.Integer


class NumberParser(SimpleTypeParser):
    """Parse any number.

    >>> NumberParser().parse_annotation(float) # doctest: +ELLIPSIS
    <Number(**{...})>

    >>> NumberParser().parse_annotation(Decimal) # doctest: +ELLIPSIS
    <Number(**{...})>

    """

    _types = {float, Decimal, Number}
    _annotation_class = j.Number


class BooleanParser(SimpleTypeParser):
    """Parse a boolean.

    >>> BooleanParser().parse_annotation(bool) # doctest: +ELLIPSIS
    <Boolean(**{...})>

    """

    _types = {bool}
    _annotation_class = j.Boolean


class NullParser(SimpleTypeParser):
    """Parse null value.

    >>> NullParser().parse_annotation(None) # doctest: +ELLIPSIS
    <Null(**{...})>

    """

    _types = {None, NoneType}
    _annotation_class = j.Null


class TypeVarParser(TypeParser):
    """Parse a custom type variable.

    >>> _Var = TypeVar('_Var', bound=str)
    >>> TypeVarParser().parse_annotation(_Var) # doctest: +ELLIPSIS
    <String(**{...'title': '_Var'...})>

    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return isinstance(annotation, TypeVar)

    @classmethod
    def parse_annotation(cls, annotation: TypeVar) -> j.JSONSchemaObject:
        title = annotation.__name__
        annotation = annotation.__bound__
        arg = AnnotationParser.parse_annotation(annotation)
        arg.title = title
        return arg


class NewTypeParser(TypeParser):
    """Parse a custom type variable.

    >>> _Var = NewType('_Var', str)
    >>> NewTypeParser().parse_annotation(_Var) # doctest: +ELLIPSIS
    <String(**{...'title': '_Var'...})>

    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        if sys.version_info[1] < 10:
            return getattr(annotation, '__qualname__', '').split('.')[0] == 'NewType'
        else:
            return isinstance(annotation, NewType)  # noqa: magic with typing

    @classmethod
    def parse_annotation(cls, annotation: NewType) -> j.JSONSchemaObject:
        title = annotation.__name__
        annotation = annotation.__supertype__
        arg = AnnotationParser.parse_annotation(annotation)
        arg.title = title
        return arg


class ConstantParser(TypeParser):
    """Parse a constant.

    >>> _Var = Literal[42]
    >>> ConstantParser().parse_annotation(_Var)  # noqa # doctest: +ELLIPSIS
    <JSONSchemaObject(**{...'enum': [42]...})>

    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return getattr(annotation, '__origin__', None) is Literal

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        return j.Enumerated(enum=list(annotation.__args__))


class UnionParser(TypeParser):
    """Parse a union type.

    >>> _Var = int | str
    >>> UnionParser().parse_annotation(_Var) # doctest: +ELLIPSIS
    <AnyOf(**{'anyOf': [{'type': 'integer'}, {'type': 'string'}]})>

    >>> _Var = Union[int, str]
    >>> UnionParser().parse_annotation(_Var) # doctest: +ELLIPSIS
    <AnyOf(**{'anyOf': [{'type': 'integer'}, {'type': 'string'}]})>

    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return is_union_type(annotation)

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        args = cls.get_args(annotation)
        return j.AnyOf(*cls.parse_args(args))


class ListParser(SimpleTypeParser):
    """Parse a list.

    >>> _Var = list[str]
    >>> ListParser().parse_annotation(_Var)
    <Array(**{'type': 'array', 'items': {'type': 'string'}})>

    >>> _Var = list[str, int]
    >>> ListParser().parse_annotation(_Var)
    <Array(**{'type': 'array', 'items': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}})>

    >>> _Var = list[str | int]
    >>> ListParser().parse_annotation(_Var)
    <Array(**{'type': 'array', 'items': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}})>

    """

    _types = {list, Collection, Iterable}
    _annotation_class = j.Array

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        args = cls.get_args(annotation)
        if args is None:
            return cls._annotation_class()
        _args = []
        for arg in cls.parse_args(args):
            if type(arg) is j.AnyOf:
                arg = cast(j.AnyOf, arg)
                _args.extend(arg.items)  # noqa (ported)
            else:
                _args.append(arg)
        if len(_args) == 1:
            return cls._annotation_class(items=_args[0])
        else:
            return cls._annotation_class(items=j.AnyOf(*_args))


class SetParser(ListParser):
    """Parse a set.

    >>> _Var = list[str]
    >>> SetParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'items': {'type': 'string'}, 'uniqueItems': True})>

    >>> _Var = list[str, int]
    >>> SetParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'items': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}, 'uniqueItems': True})>

    >>> _Var = list[str | int]
    >>> SetParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'items': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}, 'uniqueItems': True})>

    """

    _types = {set, frozenset}

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        annotation = super().parse_annotation(annotation)
        annotation.uniqueItems = True
        return annotation


class TupleParser(ListParser):
    """Parse a tuple.

    >>> _Var = tuple[str]
    >>> TupleParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'prefixItems': [{'type': 'string'}]})>

    >>> _Var = tuple[str, int]
    >>> TupleParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'prefixItems': [{'type': 'string'}, {'type': 'integer'}]})>

    >>> _Var = tuple[str, ...]
    >>> TupleParser().parse_annotation(_Var)  # doctest: +ELLIPSIS
    <Array(**{'type': 'array', 'items': {'type': 'string'}})>

    """

    _types = {tuple}

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        args = cls.get_args(annotation)
        if not args or (len(args) > 1 and args[1] is ...):
            return super().parse_annotation(annotation)
        return cls._annotation_class(prefixItems=list(cls.parse_args(args)))


class DictParser(SimpleTypeParser):
    """Parse a dictionary.

    >>> _Var = dict
    >>> DictParser().parse_annotation(_Var)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'properties': {}})>

    >>> _Var = dict[str, int]
    >>> DictParser().parse_annotation(_Var)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'properties': {}, 'patternProperties': {'^.+$': {'type': 'integer'}}})>

    """

    _types = {dict, Mapping, SimpleNamespace}

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        args = cls.get_args(annotation)
        if args and len(annotation.__args__) > 1:
            properties = {'^.+$': AnnotationParser.parse_annotation(annotation.__args__[1])}
        else:
            properties = None
        return j.Object(patternProperties=properties)


class TypedDictParser(TypeParser):
    """Parse a typed dict.

    >>> class D(TypedDict):
    ...     value: int
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': ['value'], 'additionalProperties': False})>

    >>> class D(TypedDict, total=False):
    ...     value: int
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': [], 'additionalProperties': False})>

    >>> class D(TypedDict, total=False):
    ...     value: Required[int]
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': ['value'], 'additionalProperties': False})>

    >>> class D(TypedDict):
    ...     value: NotRequired[int]
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': [], 'additionalProperties': False})>
    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return is_typeddict(annotation)

    @classmethod
    def parse_annotation(cls, annotation: TypedDict) -> j.JSONSchemaObject:
        title = annotation.__name__
        total = getattr(annotation, '__total__', True)
        properties, required = {}, []
        for key, arg in annotation.__annotations__.items():
            origin = cls.get_origin(arg)
            if origin is Required:  # noqa: magic with typing
                arg = cls.get_args(arg)[0]
                required.append(key)
            elif origin is NotRequired:  # noqa: magic with typing
                arg = cls.get_args(arg)[0]
            elif total:
                required.append(key)
            elif key in annotation.__required_keys__:  # noqa: magic with typing
                required.append(key)
            arg = AnnotationParser.parse_annotation(arg)
            properties[key] = arg
        return j.Object(
            properties=properties,
            required=required,
            description=annotation.__doc__,
            additionalProperties=False,
            title=title,
        )


class NamedTupleParser(TypeParser):
    """Parse a typed dict.

    >>> class D(TypedDict):
    ...     value: int
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': ['value'], 'additionalProperties': False})>

    >>> class D(TypedDict, total=False):
    ...     value: int
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': [], 'additionalProperties': False})>

    >>> class D(TypedDict, total=False):
    ...     value: Required[int]
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': ['value'], 'additionalProperties': False})>

    >>> class D(TypedDict):
    ...     value: NotRequired[int]
    >>> TypedDictParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'value': {'type': 'integer'}}, 'required': [], 'additionalProperties': False})>
    """

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return is_namedtuple(annotation)

    @classmethod
    def parse_annotation(cls, annotation: NamedTuple) -> j.JSONSchemaObject:
        title = annotation.__name__
        defaults = annotation._field_defaults  # noqa: no public attr
        annotations = getattr(annotation, '__annotations__', {})
        items = []
        for key in annotation._fields:  # noqa: no public attr
            arg = AnnotationParser.parse_annotation(annotations[key]) if key in annotations else j.JSONSchemaObject()
            arg.title = key
            if key in defaults:
                arg.default = defaults[key]
            items.append(arg)
        return j.Array(prefixItems=items, description=annotation.__doc__, title=title)


class EnumValueParser(TypeParser):
    """Parse a single enum value.

    >>> class E(Enum):
    ...     A = 'A'
    >>> EnumValueParser().parse_annotation(E.A)  # noqa # doctest: +ELLIPSIS
    <Constant(**{'title': 'E.A', 'enum': ['A']})>

    """

    returns_only = True

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return isinstance(annotation, Enum)

    @classmethod
    def parse_annotation(cls, annotation: enum.Enum) -> j.JSONSchemaObject:
        return j.Constant(const=annotation.value, title=f'{annotation.__class__.__name__}.{annotation.name}')


class EnumTypeParser(TypeParser):
    """Enum type parser.

    >>> class E(Enum):
    ...     A = 'A'
    ...     B = 'B'
    >>> EnumTypeParser().parse_annotation(E)  # noqa # doctest: +ELLIPSIS
    <JSONSchemaObject(**{'title': 'E', 'enum': ['A', 'B']})>

    """

    returns_only = True

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return inspect.isclass(annotation) and issubclass(annotation, Enum)

    @classmethod
    def parse_annotation(cls, annotation: type[enum.Enum]) -> j.JSONSchemaObject:
        title = annotation.__name__
        return j.JSONSchemaObject(
            description=annotation.__doc__,
            enum=[v.value for k, v in annotation._member_map_.items()],  # noqa: no public attr
            title=title,
        )


class DataclassParser(TypeParser):
    """Dataclass parser.

    >>> @dataclass
    ... class D:
    ...     a: int
    ...     b: bool = True
    >>> DataclassParser().parse_annotation(D)  # noqa # doctest: +ELLIPSIS
    <Object(**{'type': 'object', 'title': 'D', 'properties': {'a': {'type': 'integer'}, 'b': {'type': 'boolean', 'default': True}}, 'required': ['a'], 'additionalProperties': False})>

    """

    returns_only = True

    @classmethod
    def can_parse(cls, annotation) -> bool:
        return is_dataclass(annotation)

    @classmethod
    def parse_annotation(cls, annotation) -> j.JSONSchemaObject:
        title = annotation.__name__
        properties, required = {}, []
        for field in fields(annotation):
            if not field.name.startswith('_'):
                properties[field.name] = arg = AnnotationParser.parse_annotation(field.type)
                if field.default is MISSING:
                    required.append(field.name)
                else:
                    arg.default = field.default
        return j.Object(properties=properties, required=required, additionalProperties=False, title=title)


class TypeParsers(ClassRegistry[str, type[TypeParser]]):
    """Annotation type parsers registry."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (TypeParser,)


TYPE_PARSERS = TypeParsers()
TYPE_PARSERS.register_from_namespace(locals())
