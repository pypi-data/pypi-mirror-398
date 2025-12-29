from base64 import b64encode
from time import time

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.rpc import JSONRPCServer
from kaiju_tools.http import RPCClientService, JSONRPCView, HTTPService
from kaiju_tools.sessions import TokenClientService
from kaiju_tools.exceptions import InvalidParams

from kaiju_tools.tests.fixtures import get_app

__all__ = ['TestRPCClientService']


@pytest.mark.asyncio
class TestRPCClientService:
    class _MockTokenClient(TokenClientService):
        def _get_exp_time(self, token: str) -> int:
            return int(time() + 1000)

    @pytest.fixture
    def _sessions(self, mock_sessions):
        return mock_sessions

    @pytest_asyncio.fixture
    async def _server(
        self, app, rpc, mock_rpc_service, mock_login, _sessions, aiohttp_server, mock_session
    ) -> JSONRPCServer:
        app.router.add_route('*', '/public/rpc', JSONRPCView)
        server = await aiohttp_server(app, port=20020)  # TODO: random port ?
        async with server:
            async with app.services:
                yield rpc

    @pytest_asyncio.fixture
    async def _client(self, _server, mock_users, scheduler, logger):
        app = get_app(logger)
        transport = HTTPService(app=app, host='http://localhost:20020')
        app.services.add_service(transport)
        client = RPCClientService(app=app, transport=transport)
        app.services.add_service(client)
        token_client = self._MockTokenClient(
            app=app, rpc_client=client, username=mock_users.username, password=mock_users.password, scheduler=scheduler
        )
        app.services.add_service(token_client)
        client._token_client = token_client
        async with app.services:
            yield client

    async def test_request(self, _server: JSONRPCServer, _client: RPCClientService, rpc):
        rpc._enable_permissions = False
        result = await _client.call('do.echo', {'data': True})
        assert result is True

    async def test_request_error(self, _server: JSONRPCServer, _client: RPCClientService, rpc):
        rpc._enable_permissions = False
        with pytest.raises(InvalidParams):
            await _client.call('do.echo', {'not_data': True})

    async def test_request_with_basic_auth(self, _server, _client, rpc, mock_users):
        code = b64encode(f'{mock_users.username}:{mock_users.password}'.encode()).decode('utf-8')
        _client._auth_str = f'Basic {code}'
        result = await _client.call('do.echo', {'data': True})
        assert result is True

    async def test_request_with_token_auth(self, _server: JSONRPCServer, _client: RPCClientService, rpc):
        result = await _client.call('do.echo', {'data': True})
        assert result is True

    async def test_batch_request(self, _server: JSONRPCServer, _client: RPCClientService, rpc):
        rpc._enable_permissions = False
        result = await _client.call_multiple(
            (
                {'method': 'do.echo', 'params': {'data': 1}},
                {'method': 'do.echo', 'params': {'data': 2}},
                {'method': 'do.echo', 'params': {'data': 3}},
            )
        )
        assert result == [1, 2, 3]
