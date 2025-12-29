import asyncio
from time import time

import pytest  # noqa: pycharm
import pytest_asyncio

from kaiju_tools.rpc import JSONRPCHeaders, AbstractRPCCompatible, JSONRPCServer
from kaiju_tools.exceptions import Aborted, RequestTimeout

__all__ = ['TestRPCServer']


@pytest.mark.asyncio
class TestRPCServer:
    @pytest_asyncio.fixture
    async def _rpc(self, app, rpc, mock_rpc_service, mock_sessions, mock_session, mock_auth):
        async with app.services:
            yield rpc

    @pytest.mark.parametrize('method', ['api', 'status', 'tasks'])
    async def test_inspect_methods(self, _rpc: JSONRPCServer, mock_session, method: str):
        _rpc._enable_permissions = False
        _, response = await _rpc.call({'method': f'rpc.{method}'}, {})
        _rpc.logger.debug(response)
        assert response['result']

    async def test_authentication(self, _rpc: JSONRPCServer, mock_users):
        req = {'method': 'do.echo', 'params': {'data': True}}
        req_headers = {JSONRPCHeaders.AUTHORIZATION: f'Basic {mock_users.username}:{mock_users.password}'}
        headers, response = await _rpc.call(req, req_headers)
        assert response['result'] is True

    @pytest.mark.parametrize(
        'result, req',
        [
            (True, {'jsonrpc': '2.0', 'id': 421, 'method': 'do.echo', 'params': {'data': True}}),
            (True, {'id': 421, 'method': 'do.echo', 'params': {'data': True}}),
            (True, {'method': 'do.echo', 'params': {'data': True}}),
            (None, {'method': 'do.echo'}),
            (None, {'method': 'do.echo', 'params': None}),
            ('mock_session', {'method': 'do.echo_session'}),
            ((None, {'a': True}), {'method': 'do.echo_var_args', 'params': {'a': True}}),
        ],
        ids=['normal', 'no protocol', 'default id', 'no params', 'null params', 'session context', 'variable args'],
    )
    async def test_valid_calls(self, _rpc: JSONRPCServer, mock_session, req, result):
        req_headers = {JSONRPCHeaders.CORRELATION_ID_HEADER: 'ffffffff'}
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert headers[JSONRPCHeaders.CORRELATION_ID_HEADER] == req_headers[JSONRPCHeaders.CORRELATION_ID_HEADER]
        assert response['result'] == result

    async def test_retries(self, _rpc: JSONRPCServer, mock_session, logger):
        req_headers = {JSONRPCHeaders.RETRIES: 3}
        req = {'method': 'do.retry', 'params': {'n': 3}}
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert response['result'] is True

    async def test_local_callback(self, _rpc: JSONRPCServer, mock_session):
        counter = 0

        async def _do_callback(mock_session, headers, response):  # noqa: expected
            nonlocal counter
            counter += response['result']

        req = {'id': None, 'method': 'do.echo', 'params': {'data': 1}}
        headers = {}
        await _rpc.call(req, headers, callback=_do_callback, session_id=mock_session.id)
        await asyncio.sleep(0.1)
        assert counter == 1

    async def test_session_store(self, _rpc: JSONRPCServer, mock_session):
        req = {'method': 'do.write_session', 'params': {'data': {'value': 1}}}
        headers = {}
        headers, response = await _rpc.call(req, headers, session_id=mock_session.id)
        assert 'result' in response
        existing = await _rpc._sessions.load_session(mock_session.id)
        assert 'value' in existing.data, 'value must be stored in the session'

    @pytest.mark.parametrize(
        'result, req',
        [
            (
                [1, 2, 3],
                [
                    {'method': 'do.echo', 'params': {'data': 1}},
                    {'method': 'do.echo', 'params': {'data': 2}},
                    {'method': 'do.echo', 'params': {'data': 3}},
                ],
            )
        ],
        ids=['batch request'],
    )
    async def test_batch_calls(self, _rpc: JSONRPCServer, mock_session, req, result):
        req_headers = {}
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert type(response) is list
        assert [r['result'] for r in response] == result
        assert [r['id'] for r in response] == list(range(len(req)))

    async def test_batch_abort_on_error(self, _rpc: JSONRPCServer, mock_session):
        req = [
            {'method': 'do.echo', 'params': {'data': True}},
            {'method': 'do.fail'},
            {'method': 'do.echo', 'params': {'data': True}},
        ]
        req_headers = {JSONRPCHeaders.ABORT_ON_ERROR: '?1'}
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert type(response[2]['error']) is Aborted

    async def test_batch_abort_on_timeout(self, _rpc: JSONRPCServer, mock_session):
        req = [
            {'method': 'do.echo', 'params': {'t': 0}},
            {'method': 'do.echo', 'params': {'t': 3}},
            {'method': 'do.echo', 'params': {'t': 0}},
        ]
        req_headers = {JSONRPCHeaders.REQUEST_TIMEOUT_HEADER: 1}
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert type(response[1]['error']) is RequestTimeout
        assert type(response[2]['error']) is RequestTimeout

    @pytest.mark.parametrize(
        'error, req',
        [
            ('InvalidParams', {'method': 'do.echo', 'params': {'not_data': True}}),
            ('MethodNotFound', {}),
            ('MethodNotFound', {'method': 'do._non_existent'}),
            ('MethodNotFound', {'method': 'do.call_system_method'}),
            ('MethodNotFound', {'id': None, 'method': 'do.call_system_method'}),
            ('RequestTimeout', {'method': 'do.echo', 'params': {'t': 3}}),
        ],
        ids=[
            'wrong input param',
            'no method name',
            'calling non-existent method',
            'insufficient permissions',
            'notify request pre-check',
            'request timeout',
        ],
    )
    async def test_errors(self, _rpc: JSONRPCServer, mock_session, req, error, logger):
        req_headers = {
            JSONRPCHeaders.CORRELATION_ID_HEADER: 'ffffffff',
            JSONRPCHeaders.REQUEST_TIMEOUT_HEADER: 1,
        }
        headers, response = await _rpc.call(req, req_headers, session_id=mock_session.id)
        assert headers[JSONRPCHeaders.CORRELATION_ID_HEADER] == req_headers[JSONRPCHeaders.CORRELATION_ID_HEADER]
        assert 'error' in response
        logger.debug(response)
        assert response['error'].repr()['data']['type'] == error

    @pytest.mark.parametrize(
        'result, req',
        [(1, [{'method': 'do.echo', 'params': {'data': 1}}, {'method': 'do.echo', 'params': {'data': '[0]'}}])],
    )
    async def test_batch_templates(self, _rpc: JSONRPCServer, mock_session, req, result, logger):
        headers = {JSONRPCHeaders.USE_TEMPLATE: '?1'}
        headers, response = await _rpc.call(req, headers, session_id=mock_session.id)
        logger.debug(response)
        assert response[-1]['result'] == result

    @pytest.mark.benchmark
    async def test_performance(self, rpc):
        requests, parallel, n = 25000, 128, 5
        counter = 0

        async def _do_call(_rpc):
            nonlocal counter
            data = {'id': 0, 'method': 'do.sleep', 'params': {'test': True}}
            while counter < requests:
                await _rpc.call(data, {})
                counter += 1

        class _Service(AbstractRPCCompatible):
            @property
            def routes(self) -> dict:
                return {'sleep': self.do_sleep}

            @staticmethod
            async def do_sleep(test: bool):
                return test

        print(f'\nJSON RPC Queued Service simple benchmark (best of {n}).')
        print(f'{parallel} connections\n')

        async with rpc:
            rpc._debug = False
            rpc._request_logs = False
            rpc._response_logs = False
            rpc._enable_permissions = False
            rpc.register_service('do', _Service())
            tasks = [asyncio.create_task(_do_call(rpc)) for _ in range(parallel)]
            t0 = time()
            while counter < requests:
                await asyncio.sleep(0.1)
            t1 = time()
            await asyncio.gather(*tasks)

        dt = t1 - t0
        rps = round(counter / dt)
        print(f'{dt}')
        print(f'{counter} requests')
        print(f'{rps} req/sec')
