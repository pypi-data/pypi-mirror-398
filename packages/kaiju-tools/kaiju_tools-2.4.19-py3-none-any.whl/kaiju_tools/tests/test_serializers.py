from datetime import datetime, date
from decimal import Decimal
from typing import TypedDict, NamedTuple
from uuid import UUID

import pytest
import msgspec

from kaiju_tools.encoding import loads, dumps, msgpack_loads, msgpack_dumps, Serializable


class _TypedDict(TypedDict):
    a: int


class _NamedTuple(NamedTuple):
    a: int


class _Serializable(Serializable):

    def __init__(self, a: int):
        self.a = a

    def repr(self) -> dict:
        return {'a': self.a}


class Struct(msgspec.Struct):
    a: int


# id | initial value | expected json value | expected msgpack value
# use ellipsis in expected to skip the case for a particular encoder
DATA = [
    # simple types
    ('bool', True, True, True),
    ('int', 42, 42, 42),
    ('float', 42.0, 42.0, 42.0),
    ('str', 'test', 'test', 'test'),
    ('null', None, None, None),
    (
        'uuid-string',
        '4f36fe31-33df-46f1-8677-5859d9fa1293',
        '4f36fe31-33df-46f1-8677-5859d9fa1293',
        '4f36fe31-33df-46f1-8677-5859d9fa1293',
    ),
    # simple collections
    ('list', ['a', 1, True], ['a', 1, True], ['a', 1, True]),
    ('tuple', ('a', 1, True), ['a', 1, True], ['a', 1, True]),
    ('set', {'a'}, ['a'], ['a']),
    ('frozenset', frozenset({'a'}), ['a'], ['a']),
    ('dict', {'a': 1}, {'a': 1}, {'a': 1}),
    # additional types
    ('decimal', Decimal('42.0'), '42.0', '42.0'),
    (
        'uuid',
        UUID('4f36fe31-33df-46f1-8677-5859d9fa1293'),
        '4f36fe31-33df-46f1-8677-5859d9fa1293',
        '4f36fe31-33df-46f1-8677-5859d9fa1293',
    ),
    ('date', date(2050, 1, 1), '2050-01-01', '2050-01-01'),
    ('datetime', datetime(2050, 1, 1), '2050-01-01T00:00:00', '2050-01-01T00:00:00'),
    # complex types
    ('typed_dict', _TypedDict(a=1), {'a': 1}, {'a': 1}),
    ('named_tuple', _NamedTuple(a=1), [1], [1]),
    ('serializable', _Serializable(a=1), {'a': 1}, {'a': 1}),
    ('struct', Struct(a=1), {'a': 1}, {'a': 1}),
]

_ids = [row[0] for row in DATA]


@pytest.mark.parametrize('value, expected', [(row[1], row[2]) for row in DATA if row[2] is not ...], ids=_ids)
def test_json_serializer(value, expected):
    new_value = loads(dumps(value))
    assert new_value == expected


@pytest.mark.parametrize('value, expected', [(row[1], row[3]) for row in DATA if row[3] is not ...], ids=_ids)
def test_msgpack_serializer(value, expected):
    new_value = msgpack_loads(msgpack_dumps(value))
    assert new_value == expected
