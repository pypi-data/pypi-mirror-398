# coding=utf-8

import os
from types import ModuleType
from importlib import import_module

from fastmcp import FastMCP


class FastMCPBuilder:
    @classmethod
    def get_app(cls, project: ModuleType, transport=''):
        module_path = f'{project.__package__}.mcp.builder'
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            builder_cls = cls
        else:
            builder_cls = getattr(module, 'Builder', None)
            if builder_cls is None or not issubclass(builder_cls, cls):
                print(f'Invalid mcp builder path {module_path}.Builder')
                return None

        builder = builder_cls(project, transport)
        builder.make()
        return builder.app

    def __init__(self, project: ModuleType, transport=''):
        self.project = project
        self.transport = transport
        self.server_dir = os.path.realpath(os.path.join(project.__path__[0], 'mcp'))
        self.app = None

    def make(self):
        self.app = FastMCP('main-mcp')
        self.setup_tools()

    def setup_tools(self):
        base_path = os.path.join(self.server_dir, 'tools')
        package_dir = os.path.realpath(os.path.join(self.project.__path__[0], os.pardir))
        for filename in os.listdir(base_path):
            full_pathname = os.path.join(base_path, filename)
            if not filename.endswith('.py') or not os.path.isfile(full_pathname):
                continue

            module_path = full_pathname[len(package_dir) + 1: -len('.py')].replace(os.sep, '.')
            module = import_module(module_path)
            mcp = getattr(module, 'mcp', None)
            if mcp is None or not isinstance(mcp, FastMCP):
                continue

            self.app.mount(mcp, prefix='')
