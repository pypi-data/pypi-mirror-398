import asyncio

import pytest  # noqa: pycharm

__all__ = ['TestScheduler']


@pytest.mark.asyncio
class TestScheduler:
    counter = 0

    async def _call(self, t: float = None):
        if t:
            await asyncio.sleep(t)
        self.counter += 1

    async def test_scheduler_execution(self, scheduler):
        scheduler.schedule_task(self._call, interval=0.1, name='task_1')
        scheduler.schedule_task(self._call, interval=0.1, name='task_2')
        async with scheduler.app.services:
            await asyncio.sleep(0.15)
            assert self.counter == 2, 'both tasks must be completed'

    async def test_scheduler_repeat(self, scheduler):
        scheduler.schedule_task(self._call, interval=0.1, name='task_1')
        async with scheduler.app.services:
            await asyncio.sleep(0.5)
            assert self.counter > 1, 'must repeat task'

    async def test_scheduler_policy_wait(self, scheduler):
        scheduler.schedule_task(self._call, params={'t': 0.1}, interval=0.1, policy=scheduler.ExecPolicy.WAIT)
        async with scheduler.app.services:
            await asyncio.sleep(0.35)
            assert self.counter == 1, 'must wait, i.e. only one increment must happen'

    async def test_scheduler_policy_cancel(self, scheduler):
        scheduler.schedule_task(self._call, params={'t': 0.1}, interval=0.1, policy=scheduler.ExecPolicy.CANCEL)
        async with scheduler.app.services:
            await asyncio.sleep(0.35)
            assert self.counter == 0, 'no execution must happen due to cancellation'
