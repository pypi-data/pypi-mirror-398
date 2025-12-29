import pytest  # noqa: pytest
from typing import cast

from kaiju_tools.mapping import *


@pytest.fixture
def test_mapping():
    def _test_mapping(**kws):
        return {'come': {'get': {**kws}}}

    return _test_mapping


@pytest.fixture
def test_list(test_mapping):
    def _test_list(n=3, **kws):
        return [test_mapping(**kws) for _ in range(n)]

    return _test_list


@pytest.fixture
def test_list_mapping(test_list):
    def _test_list_mapping(*args, **kws):
        return {'data': test_list(*args, **kws)}

    return _test_list_mapping


def test_strip_fields(logger):
    obj = {'_id': 1, 'value': True}
    obj = strip_fields(obj)
    logger.debug(obj)
    assert '_id' not in obj
    assert obj['value'] is True

    obj = [{'_id': 1, 'value': True}, {'_id': 2, 'value': True}]
    obj = strip_fields(obj)
    logger.debug(obj)
    for _obj in obj:
        assert '_id' not in _obj
        assert _obj['value'] is True

    obj = [{'obj': {'_id': 1, 'value': True}}, {'obj': {'_id': 2, 'value': True}}]
    obj = strip_fields(obj)
    logger.debug(obj)
    for _obj in obj:
        assert '_id' not in _obj['obj']
        assert _obj['obj']['value'] is True


def test_flatten(logger, test_mapping, test_list, test_list_mapping):
    obj = test_mapping(some=True)
    _o = flatten(obj)
    logger.debug(_o)
    assert _o['come.get.some'] is True

    _obj = test_list(some=True)
    _o = flatten(_obj)
    logger.debug(_o)
    for o in _o:
        assert o['come.get.some'] is True

    _obj = test_list_mapping(some=True)
    _o = flatten(_obj)
    logger.debug(_o)
    for o in _o['data']:
        assert o['come.get.some'] is True


def test_recursive_update(logger, test_mapping, test_list):
    obj1 = test_mapping(some=True)
    obj2 = test_mapping(another=False)
    recursive_update(obj1, obj2)
    logger.debug(obj1)
    assert obj1['come']['get']['another'] is False

    obj1 = test_list(some=True, another=False)
    obj2 = test_list(n=1, another=True)
    recursive_update(obj1, obj2)
    logger.debug(obj1)
    assert obj1[0]['come']['get']['another'] is True
    assert obj1[1]['come']['get']['another'] is False


def test_filter_fields(logger, test_mapping, test_list, test_list_mapping):
    obj = test_mapping(some=True, another=False)
    _o = filter_fields(obj, ['come.get.some', 'come.get.empty'])
    logger.debug(_o)
    assert _o['come']['get']['some'] is True
    assert 'another' not in _o['come']['get']
    assert _o['come']['get']['empty'] is None

    obj = test_list(some=True, another=False)
    obj = cast(dict, obj)
    _o = filter_fields(obj, ['come.get.some', 'come.get.empty'])
    logger.debug(_o)
    for o in _o:
        assert o['come']['get']['some'] is True
        assert 'another' not in o['come']['get']
        assert o['come']['get']['empty'] is None

    obj = test_list_mapping(some=True, another=False)
    _o = filter_fields(obj, ['data.come.get.some', 'data.come.get.empty'])
    logger.debug(_o)
    for o in _o['data']:
        assert o['come']['get']['some'] is True
        assert 'another' not in o['come']['get']
        assert o['come']['get']['empty'] is None


def test_get_field(logger, test_mapping):
    obj = test_mapping(some=True)
    field = get_field(obj, 'come.get.some')
    assert field is True

    with pytest.raises(KeyError):
        get_field(obj, 'come.get.another')

    field = get_field(obj, 'come.get.another', default=None)
    assert field is None
