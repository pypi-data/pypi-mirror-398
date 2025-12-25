import datetime
import uuid

import pytest
from fastjsonschema import JsonSchemaException

import kaiju_tools.jsonschema as j


@pytest.mark.parametrize(
    'schema, data',
    [
        (j.String(minLength=1, maxLength=5), 'test'),
        (j.Enumerated(enum=['a', 'b', 'c']), 'a'),
        (j.Integer(minimum=1), 10),
        (j.Number(minimum=1), 10),
        (j.Boolean(), True),
        (j.Constant(42), 42),
        (j.Null(), None),
        (j.Date(), datetime.datetime.now().date()),
        (j.DateTime(), datetime.datetime.now()),
        (j.GUID(), uuid.uuid4()),
        (j.Nullable(j.Integer()), None),
        (j.Nullable(j.Integer()), 42),
        (j.OneOf(j.String(), j.Integer()), 'test'),
        (j.AnyOf(j.String(), j.Integer()), 'test'),
        (j.Not(j.String()), 42),
        (j.Array(j.String()), ['test']),
    ],
    ids=[
        'string',
        'enum',
        'integer',
        'number',
        'boolean',
        'const',
        'null',
        'date',
        'datetime',
        'uuid',
        'nullable null',
        'nullable value',
        'one of',
        'any of',
        'not',
        'array',
    ],
)
def test_valid_results(schema, data):
    validator = j.compile_schema(schema)
    validator(data)


@pytest.mark.parametrize(
    'schema, data',
    [
        (j.String(), 123),
        (j.Enumerated(enum=['a', 'b', 'c']), 'd'),
        (j.Integer(minimum=1), 1.2),
        (j.Number(minimum=1), 0),
        (j.Boolean(), 'something'),
        (j.Constant(42), 43),
        (j.Null(), False),
        (j.Date(), 'wrong'),
        (j.DateTime(), 'wrong'),
        (j.GUID(), 'wrong'),
        (j.OneOf(j.String(), j.Integer()), 1.2),
        (j.AnyOf(j.String(), j.Integer()), None),
        (j.Not(j.String()), '42'),
        (j.Array(j.String()), 'test'),
    ],
    ids=[
        'string',
        'enum',
        'integer',
        'number',
        'boolean',
        'const',
        'null',
        'date',
        'datetime',
        'uuid',
        'not',
        'one of',
        'any of',
        'array',
    ],
)
def test_invalid_results(schema, data):
    validator = j.compile_schema(schema)
    with pytest.raises(JsonSchemaException):
        validator(data)
