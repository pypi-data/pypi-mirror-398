import asyncio
import uuid

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.locks import BaseLocksService, NotLockOwnerError, LockTimeout, LockExistsError, Locks

__all__ = ['TestLocks']


@pytest.mark.asyncio
class TestLocks:
    @staticmethod
    def get_key():
        return str(uuid.uuid4())

    @pytest_asyncio.fixture
    async def _locks(self, app, mock_locks):
        mock_locks.WAIT_RELEASE_REFRESH_INTERVAL = 0.1
        mock_locks._refresh_interval = 0.1
        mock_locks.namespace = app.namespace / 'pytest_locks'
        async with app.services:
            yield mock_locks

    @pytest.fixture
    def _ns(self, app):
        return app.namespace / 'pytest_locks'

    async def test_acquire_release(self, _locks: BaseLocksService, _ns):
        key = _ns.get_key(self.get_key())
        lock_id = await _locks.acquire(key, ttl=1)
        existing = await _locks.m_exists([key])
        assert key in existing
        await _locks.release(key, lock_id)

    async def test_release_with_wrong_lock_id(self, _locks: BaseLocksService, _ns):
        key = _ns.get_key(self.get_key())
        await _locks.acquire(key, ttl=1)
        with pytest.raises(NotLockOwnerError):
            await _locks.release(key, Locks.LockId('Wrong!'))

    async def test_acquire_timeout(self, _locks: BaseLocksService, _ns):
        key = _ns.get_key(self.get_key())
        await _locks.acquire(key, ttl=3)
        with pytest.raises(LockTimeout):
            await _locks.acquire(key, ttl=1, timeout=1)

    async def test_acquire_lock_exists(self, _locks: BaseLocksService, _ns):
        key = _ns.get_key(self.get_key())
        await _locks.acquire(key, ttl=1)
        with pytest.raises(LockExistsError):
            await _locks.acquire(key, ttl=3, wait=False)

    async def test_for_parallel_acquire(self, _locks: BaseLocksService, _ns):
        key = _ns.get_key(self.get_key())
        commands = [_locks.acquire(key, ttl=1, wait=False) for _ in range(5)]
        results = await asyncio.gather(*commands, return_exceptions=True)
        counter = sum(1 for r in results if isinstance(r, LockExistsError))
        assert counter == len(commands) - 1, 'all but one should fail'
