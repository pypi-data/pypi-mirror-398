import inspect
import re
from pathlib import Path
from typing import Collection, Union

from jinja2 import Environment

from kaiju_tools.rpc import JSONRPCServer
from kaiju_tools.services import Service


__all__ = ['RPCClientCodeGenerator']


module_template = """import uuid
from typing import *

from kaiju_tools.types import *
from {{ module_name }} import {{ class_name }}

RowType = TypeVar('RowType', bound=dict)


class {{ app_name }}Client({{ class_name }}):
    {{ service_doc }}

    {% for method in methods %}
    async def {{ method['name'] }}({{ method['signature'] }}, _max_timeout: int = None, _nowait: bool = False):
        {{ method['doc'] }}
        return await self.call(
            method='{{ method['rpc_name'] }}',
            params={{ method['params'] }},
            max_timeout=_max_timeout,
            nowait=_nowait
        )
    {% endfor %}

"""

_doc_remove_underscored = re.compile(r'\s*:param _[A-z_]+:[^\n]*\n')


client_types = {
    'http': {'cls': 'HTTPRPCClient', 'module': 'kaiju_tools.http'},
    'stream': {'cls': 'StreamRPCClient', 'module': 'kaiju_tools.streams'},
}


class RPCClientCodeGenerator(Service):
    """It can generate python code for an RPC application client."""

    def __init__(self, *args, template_path: Union[str, Path] = None, **kws):
        """Initialize."""
        super().__init__(*args, **kws)
        if template_path is None:
            self._template = module_template
        else:
            with open(template_path) as f:
                self._template = f.read()

    def generate_clients(self, services: Collection[str] = None):
        """Create all RPC clients."""
        for key, value in client_types.items():
            filename = Path('./client_{key}.py')
            self.generate_source_file(value['cls'], value['module'], filename, services=services)

    def generate_source_file(
        self, cls: str, module: str, output: Union[str, Path], services: Collection[str] = None
    ) -> None:
        """Create source files for a client from application services."""
        app_name = self._reformat_app_name(self.app.name)
        service_doc = f'"""Auto-generated {app_name} RPC client."""'
        rpc = self.discover_service(None, cls=JSONRPCServer)
        if services:
            services = frozenset(services)
        methods = []
        for method_name, method_info in rpc._methods.items():  # noqa
            if services is not None and method_info.service_name not in services:
                continue
            f = method_info['f']
            sig = inspect.signature(f)
            sig_text = ['self']
            sig_text.extend([str(value) for key, value in sig.parameters.items() if not key.startswith('_')])
            sig_text = ', '.join(sig_text)
            params = ', '.join(f'{key}={key}' for key in sig.parameters.keys() if not key.startswith('_'))
            service_name = self._reformat_service_name(method_info['service_name'])
            name = f'{service_name}_{f.__name__}'
            method_data = {
                'rpc_name': method_name,
                'name': name,
                'doc': f'"""{self._format_docstring(f.__doc__)}"""' if f.__doc__ else f'"""Call {method_name}."""',
                'signature': sig_text,
                'params': f'dict({params})',
            }
            methods.append(method_data)

        template = Environment().from_string(module_template)
        code = template.render(
            app_name=app_name, service_doc=service_doc, methods=methods, module_name=module, class_name=cls
        )
        with open(output, 'w') as f:
            f.write(code)

    @staticmethod
    def _format_docstring(doc: str) -> str:
        doc = _doc_remove_underscored.sub('\n', doc)
        doc += '\n\t:param _max_timeout: max request timeout in sec (None == server default)\n'
        doc += '\t:param _nowait: do not wait for the response (equivalent to id: null in JSONRPC)\n\n'
        return doc

    @staticmethod
    def _reformat_app_name(name: str) -> str:
        name = name.replace('-', '_').split('_')
        name = ''.join(part.capitalize() for part in name)
        return name

    @staticmethod
    def _reformat_service_name(name: str) -> str:
        name_parts = re.findall('[A-Z][^A-Z]*', name)
        if name_parts:
            name = '_'.join(part.lower() for part in name_parts)
        return name.replace('.', '_')
