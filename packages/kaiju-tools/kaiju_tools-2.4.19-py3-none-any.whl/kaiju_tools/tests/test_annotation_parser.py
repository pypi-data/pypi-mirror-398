from collections import namedtuple
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import (
    Set,
    Tuple,
    Union,
    Optional,
    TypedDict,
    NamedTuple,
    List,
    NewType,
    TypeVar,
    Literal,
    Generic,
)
from collections.abc import Collection, Iterable
from uuid import UUID

import pytest  # noqa: pycharm

from kaiju_tools.annotations import AnnotationParser, MethodSignatureError
from kaiju_tools.jsonschema import compile_schema
from kaiju_tools.rpc import AbstractRPCCompatible


class _TReq(TypedDict):
    """Dict info."""

    id: int
    name: str


class _TNotReq(TypedDict, total=False):
    """Dict info."""

    id: int
    name: str


class _NT(NamedTuple):
    """Tuple info."""

    id: int
    name: str = None


class _Enum(Enum):
    """Enum info."""

    value = 'ENUM_VALUE'
    other_value = 'OTHER_ENUM_VALUE'


_NTSimple = namedtuple('_NTSimple', ['id', 'name'])
_TNew = NewType('_TNew', int)
_TVar = TypeVar('_TVar', bound=int)
_GenericVar = TypeVar('_GenericVar', bound=dict)
_OtherGenericVar = TypeVar('_OtherGenericVar', bound=int)


class _Var(TypedDict):
    id: int


class _BaseTestClass(Generic[_GenericVar, _OtherGenericVar], AbstractRPCCompatible):
    async def generic_type(self, a: _GenericVar, b: _OtherGenericVar): ...


class _TestClass(_BaseTestClass[_Var, int]):
    async def basic(self, a: int, b: str = None, c: float = ..., d: bool = True, _e: str = 'ignored'):
        pass

    async def collections(self, a: Collection[str], b: set[str], c: tuple[str, None], d: Iterable[float]):
        pass

    async def special_wrappers(self, a: str | None, b: str | int):
        pass

    async def no_annotations(self, a, b=1):
        pass

    async def typed_dicts(self, a: _TReq, b: _TNotReq):
        pass

    async def named_tuple(self, a: _NT, b: _NTSimple):
        pass

    async def non_standard_types(self, a: UUID, b: datetime, c: date, d: Decimal):
        pass

    async def nested(self, a: list[str | int]): ...

    async def custom_types(self, a: _TNew, b: _TVar): ...

    async def text_ref(self, a: '_NT'): ...

    async def constants(self, a: Literal['dogs', 'cats']): ...

    async def args_kws(self, a: int, *args, b: str = None, **kws):
        # Args should be discarded since our rpc spec does not allow positional args.
        # Kws should act like allowing additional properties
        pass

    async def positional_only(self, a: int, /):
        # Should not be allowed since our rpc spec does not allow positional-only args.
        pass

    async def enum_returns(self) -> _Enum.value: ...

    async def enum_type_returns(self) -> _Enum: ...


@pytest.mark.parametrize(
    ['cls', 'f', 'params', 'required'],
    (
        (
            _TestClass,
            _TestClass.basic,
            {
                'a': {'type': 'integer'},
                'b': {'type': 'string', 'default': None},
                'c': {'type': 'number'},
                'd': {'type': 'boolean', 'default': True},
            },
            ['a'],
        ),
        (
            _TestClass,
            _TestClass.collections,
            {
                'a': {'type': 'array', 'items': {'type': 'string'}},
                'b': {'type': 'array', 'items': {'type': 'string'}, 'uniqueItems': True},
                'c': {'type': 'array', 'prefixItems': [{'type': 'string'}, {'enum': [None]}]},
                'd': {'type': 'array', 'items': {'type': 'number'}},
            },
            ['a', 'b', 'c', 'd'],
        ),
        (
            _TestClass,
            _TestClass.special_wrappers,
            {
                'a': {'anyOf': [{'type': 'string'}, {'enum': [None]}]},
                'b': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]},
            },
            ['a', 'b'],
        ),
        (_TestClass, _TestClass.no_annotations, {'a': {}, 'b': {'default': 1}}, ['a']),
        (
            _TestClass,
            _TestClass.typed_dicts,
            {
                'a': {
                    'type': 'object',
                    'properties': {'id': {'type': 'integer'}, 'name': {'type': 'string'}},
                    'additionalProperties': False,
                    'required': ['id', 'name'],
                    'title': '_TReq',
                    'description': 'Dict info.',
                },
                'b': {
                    'type': 'object',
                    'properties': {'id': {'type': 'integer'}, 'name': {'type': 'string'}},
                    'additionalProperties': False,
                    'required': [],
                    'title': '_TNotReq',
                    'description': 'Dict info.',
                },
            },
            ['a', 'b'],
        ),
        (
            _TestClass,
            _TestClass.named_tuple,
            {
                'a': {
                    'type': 'array',
                    'prefixItems': [
                        {'title': 'id', 'type': 'integer'},
                        {'title': 'name', 'type': 'string', 'default': None},
                    ],
                    'title': '_NT',
                    'description': 'Tuple info.',
                },
                'b': {
                    'type': 'array',
                    'prefixItems': [{'title': 'id'}, {'title': 'name'}],
                    'title': '_NTSimple',
                    'description': '_NTSimple(id, name)',
                },
            },
            ['a', 'b'],
        ),
        (
            _TestClass,
            _TestClass.non_standard_types,
            {
                'a': {'type': 'string', 'format': 'uuid'},
                'b': {'type': 'string', 'format': 'date-time'},
                'c': {'type': 'string', 'format': 'date'},
                'd': {'type': 'number'},
            },
            ['a', 'b', 'c', 'd'],
        ),
        (
            _TestClass,
            _TestClass.nested,
            {'a': {'type': 'array', 'items': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}}},
            ['a'],
        ),
        (
            _TestClass,
            _TestClass.custom_types,
            {'a': {'type': 'integer', 'title': '_TNew'}, 'b': {'type': 'integer', 'title': '_TVar'}},
            ['a', 'b'],
        ),
        (_TestClass, _TestClass.text_ref, {'a': {'title': '_NT'}}, ['a']),
        (_TestClass, _TestClass.constants, {'a': {'enum': ['dogs', 'cats']}}, ['a']),
        (
            _TestClass,
            _TestClass.generic_type,
            {
                'a': {
                    'type': 'object',
                    'properties': {'id': {'type': 'integer'}},
                    'required': ['id'],
                    'title': '_Var',
                    'additionalProperties': False,
                },
                'b': {'type': 'integer'},
            },
            ['a', 'b'],
        ),
        (
            _BaseTestClass,
            _BaseTestClass.generic_type,
            {
                'a': {'type': 'object', 'properties': {}, 'title': '_GenericVar'},
                'b': {'type': 'integer', 'title': '_OtherGenericVar'},
            },
            ['a', 'b'],
        ),
    ),
    ids=[
        'basic',
        'collections',
        'special_wrappers',
        'no_annotations',
        'typed_dicts',
        'named_tuple',
        'non_standard_types',
        'nested',
        'custom_types',
        'text_ref',
        'constants',
        'generics',
        'not_resolved_generics',
    ],
)
def test_annotation_parser(cls, f, params, required, logger):
    annotation = AnnotationParser.parse_method(cls, 'f', f)
    schema = annotation['params'].repr()
    logger.debug(annotation)
    logger.debug(schema)
    compile_schema(schema)
    assert schema['type'] == 'object'
    assert schema['properties'] == params
    assert schema['required'] == required


def test_args_kws_parser(logger):
    annotation = AnnotationParser.parse_method(_TestClass, 'f', _TestClass.args_kws)
    schema = annotation['params'].repr()
    compile_schema(schema)
    logger.debug(annotation)
    logger.debug(schema)
    assert schema['additionalProperties'] is True
    assert schema['properties'] == {'a': {'type': 'integer'}, 'b': {'type': 'string', 'default': None}}
    assert schema['required'] == ['a']


def test_positional_only_raises_error(logger):
    with pytest.raises(MethodSignatureError):
        AnnotationParser.parse_method(_TestClass, 'f', _TestClass.positional_only)


@pytest.mark.parametrize(
    ['f', 'returns'],
    (
        (_TestClass.enum_returns, {'enum': ['ENUM_VALUE'], 'title': '_Enum.value'}),
        (
            _TestClass.enum_type_returns,
            {'enum': ['ENUM_VALUE', 'OTHER_ENUM_VALUE'], 'title': '_Enum', 'description': 'Enum info.'},
        ),
    ),
    ids=['enum_returns', 'enum_type_returns'],
)
def test_annotation_return_parser(f, returns, logger):
    annotation = AnnotationParser.parse_method(_TestClass, 'f', f)
    schema = annotation['returns'].repr()
    compile_schema(schema)
    logger.debug(annotation)
    logger.debug(schema)
    assert schema == returns
