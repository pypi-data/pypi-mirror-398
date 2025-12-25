import uuid
from datetime import datetime
from time import time
from typing import Collection, Generator

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.interfaces import DataStore

__all__ = ['TestDataStore', 'TestDataStoreCompKey']


@pytest.mark.asyncio
class TestDataStore:
    """Test data store service."""

    primary_key = 'id'

    @staticmethod
    def get_rows(num: int) -> Generator[dict, None, None]:
        for n in range(num):
            yield {
                'id': uuid.uuid4().hex,
                'uuid': uuid.uuid4(),
                'name': f'row_{n}',
                'value': n,
                'enabled': True,
                'timestamp': int(time()),
                'created': datetime.now(),
            }

    def get_pkey(self, row: dict):
        if isinstance(self.primary_key, (list, tuple)):
            return tuple(row[k] for k in self.primary_key)
        else:
            return row[self.primary_key]

    @pytest_asyncio.fixture
    async def _store(self, app, mock_data_store) -> DataStore:
        async with app.services:
            mock_data_store.primary_key = self.primary_key
            yield mock_data_store

    @pytest.fixture
    def _row(self) -> dict:
        return next(self.get_rows(1))

    @pytest.fixture
    def _rows(self) -> Collection[dict]:
        return tuple(self.get_rows(10))

    @staticmethod
    def update_value() -> dict:
        """Get update values for m_update."""
        return {'enabled': False}

    @staticmethod
    def update_condition() -> dict:
        """Get conditions for m_update."""
        return {'enabled': True}

    @staticmethod
    def check_update(row: dict) -> bool:
        """Validate m_update output."""
        return row['enabled'] is False

    async def test_singular(self, _store, _row):
        row_id = self.get_pkey(_row)
        _data = await _store.create(_row)
        assert await _store.exists(row_id)
        _data = await _store.update(row_id, self.update_value())
        assert self.check_update(_data)
        await _store.delete(row_id)
        assert not await _store.exists(row_id)

    async def test_multi(self, _store, _rows):
        row_id = [self.get_pkey(_row) for _row in _rows]
        _data = await _store.m_create(_rows, columns=['id'])
        assert set(row_id) == await _store.m_exists(row_id)
        _data = await _store.m_update(row_id, self.update_value())
        assert all(self.check_update(r) for r in _data)
        await _store.m_delete(row_id)
        assert not await _store.m_exists(row_id)

    async def test_conditionals(self, _store, _rows):
        row_id = [self.get_pkey(_row) for _row in _rows]
        await _store.m_create(_rows)
        _data = await _store.m_update([], self.update_value(), conditions=self.update_condition())
        assert all(self.check_update(r) for r in _data)
        await _store.m_delete([], conditions=self.update_value())
        assert not await _store.m_exists(row_id)


class TestDataStoreCompKey(TestDataStore):
    primary_key = ['id', 'uuid']
