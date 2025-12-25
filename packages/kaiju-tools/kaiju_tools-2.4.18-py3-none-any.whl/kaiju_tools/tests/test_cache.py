import uuid

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.interfaces import Cache

__all__ = ['TestCache']


@pytest.mark.asyncio
class TestCache:
    @staticmethod
    def get_key():
        return str(uuid.uuid4())

    @staticmethod
    def get_value():
        return {'arg_1': True, 'arg_2': str(uuid.uuid4())}

    @pytest_asyncio.fixture
    async def _cache(self, app, mock_cache):
        async with app.services:
            yield mock_cache

    @pytest.fixture
    def _ns(self, app):
        return app.namespace / 'pytest_cache'

    async def test_singular_keys(self, _cache: Cache, _ns):
        key, value = self.get_key(), self.get_value()
        key = _ns.get_key(key)
        await _cache.set(key, value, ttl=1)
        exists = await _cache.exists(key)
        assert exists
        _value = await _cache.get(key)
        assert _value == value
        await _cache.delete(key)
        exists = await _cache.exists(key)
        assert not exists

    async def test_multi_keys(self, _cache: Cache, _ns):
        key_1 = _ns.get_key(self.get_key())
        key_2 = _ns.get_key(self.get_key())
        data = {key_1: self.get_value(), key_2: self.get_value()}
        await _cache.m_set(data, ttl=1)
        exists = await _cache.m_exists(data.keys())
        assert set(exists) == set(data)
        _data = await _cache.m_get(data.keys())
        assert _data == data
        await _cache.m_delete(data.keys())
        exists = await _cache.m_exists(data.keys())
        assert not exists
