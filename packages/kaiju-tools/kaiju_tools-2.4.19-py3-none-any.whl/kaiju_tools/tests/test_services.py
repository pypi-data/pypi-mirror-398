import pytest

from kaiju_tools.app import Service, ContextableService, ServiceNotAvailableError


class _Service(Service):
    """Simple service."""

    service_name = '_service'


class _OtherService(Service):
    pass


class _ContextableService(ContextableService):
    """Simple contextable service."""

    service_name = '_ctx_service'

    def __init__(self, *args, dependency=None, **kws):
        super().__init__(*args, **kws)
        self.ready = False
        self.dependency = dependency
        self.dep_required = True
        self.dep_type = _Service
        self.kws = kws

    async def init(self):
        self.dependency = self.discover_service(self.dependency, cls=self.dep_type, required=self.dep_required)
        self.ready = True

    async def close(self):
        self.ready = False


@pytest.mark.asyncio
async def test_services_init(app):
    ctx_service = _ContextableService(app=app)
    ctx_service.dep_required = False
    app.services.add_service(ctx_service)
    async with app.services:
        assert ctx_service.ready
    assert not ctx_service.ready


@pytest.mark.asyncio
@pytest.mark.parametrize('dep', [_Service.service_name, None], ids=['by name', 'by type'])
async def test_discover_dependency(app, dep):
    service = _Service(app=app)
    ctx_service = _ContextableService(app=app, dependency=dep)
    app.services.add_service(service)
    app.services.add_service(ctx_service)
    async with app.services:
        assert ctx_service.ready
        assert ctx_service.dependency is service


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'kws',
    [
        {'dependency': 'other_service'},
        {'dep_type': _OtherService},
        {'dependency': _Service.service_name, 'dep_type': _OtherService},
    ],
    ids=['wrong name', 'wrong type', 'type mismatch'],
)
async def test_discover_dependency_errors(app, kws):
    service = _Service(app=app)
    ctx_service = _ContextableService(app=app)
    for key, value in kws.items():
        setattr(ctx_service, key, value)
    app.services.add_service(service)
    app.services.add_service(ctx_service)
    with pytest.raises(ServiceNotAvailableError):
        async with app.services:
            pass
