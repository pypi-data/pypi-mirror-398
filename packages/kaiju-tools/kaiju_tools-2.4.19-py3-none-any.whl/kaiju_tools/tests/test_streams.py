import asyncio
import uuid

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.streams import Listener, StreamRPCClient
from kaiju_tools.rpc import JSONRPCHeaders

__all__ = ['TestStreamServer', 'TestStreamClient']


@pytest.mark.asyncio
class TestStreamServer:
    @pytest_asyncio.fixture
    async def _listener(self, app, mock_listener, mock_rpc_service, mock_sessions, mock_session):
        async with app.services:
            yield mock_listener

    @pytest.fixture
    def _queue(self, mock_listener) -> asyncio.Queue:
        return mock_listener._transport.get_stream(mock_listener._key)  # noqa

    async def test_valid_requests(self, rpc, _listener: Listener, _queue, mock_rpc_service):
        rpc._enable_permissions = False
        value = str(uuid.uuid4())
        _queue.put_nowait((('do.store', {'data': value}), {}))
        await _queue.join()
        assert mock_rpc_service.stored == value

    async def test_authentication_header(self, _listener: Listener, _queue, mock_rpc_service, mock_auth, mock_users):
        mock_auth.enable_basic_auth = True
        value = str(uuid.uuid4())
        _queue.put_nowait(
            (
                ('do.store', {'data': value}),
                {JSONRPCHeaders.AUTHORIZATION: f'Basic {mock_users.username}:{mock_users.password}'},
            )
        )
        await _queue.join()
        assert mock_rpc_service.stored == value

    async def test_session_header(self, _listener: Listener, _queue, mock_session, mock_rpc_service):
        _listener._use_sessions = True
        value = str(uuid.uuid4())
        _queue.put_nowait((('do.store', {'data': value}), {JSONRPCHeaders.SESSION_ID_HEADER: mock_session.id}))
        await _queue.join()
        assert mock_rpc_service.stored == value

    @pytest.mark.parametrize(
        'req, headers',
        [
            (('do.echo', 'wrong'), {}),
            (('do.fail', None), {}),
        ],
        ids=['failed pre-request', 'failed request'],
    )
    async def test_invalid_requests(self, _listener: Listener, _queue, mock_rpc_service, req, headers):
        _queue.put_nowait((req, headers))
        await _queue.join()


@pytest.mark.asyncio
class TestStreamClient:
    @pytest_asyncio.fixture
    async def _client(
        self, app, mock_listener, mock_rpc_service, mock_sessions, mock_session, mock_stream_client
    ) -> StreamRPCClient:
        async with app.services:
            yield mock_stream_client

    @pytest.fixture
    def _queue(self, mock_listener) -> asyncio.Queue:
        return mock_listener._transport.get_stream(mock_listener._key)  # noqa

    async def test_valid_request(self, _client, _queue, mock_rpc_service, mock_session):
        value = str(uuid.uuid4())
        await _client.call('do.store', {'data': value})
        await _queue.join()
        assert mock_rpc_service.stored == value

    @pytest.mark.parametrize(
        'req',
        [{'method': 'do.echo', 'params': 'wrong'}, {'method': 'do.fail', 'params': None}],
        ids=['failed pre-request', 'failed request'],
    )
    async def test_invalid_requests(self, _client, _queue, mock_rpc_service, mock_session, req):
        await _client.call(req['method'], req['params'], app='pytest', topic='rpc')  # noqa
        await _queue.join()
