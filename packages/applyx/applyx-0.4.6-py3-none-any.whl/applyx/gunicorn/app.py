# coding=utf-8

import sys
import os
import yaml
from types import ModuleType
from importlib import import_module

import gunicorn
from gunicorn.app.base import BaseApplication
from loguru import logger
from addict import Dict

from applyx.conf import settings
from applyx.web.builder import FastAPIBuilder
from applyx.utils import get_log_dir


class GunicornApplication(BaseApplication):
    @classmethod
    def get_app(cls, project: ModuleType):
        module_path = f'{project.__package__}.api.gunicorn'
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            return cls(project)

        app_cls = getattr(module, 'Application', None)
        if app_cls is None or not issubclass(app_cls, cls):
            print(f'Invalid flask application path {module_path}:APP')
            return None

        return app_cls(project)

    def __init__(self, project: ModuleType):
        super().__init__()
        gunicorn.SERVER_SOFTWARE = 'Linux'
        self.app = FastAPIBuilder.get_app(project)
        self.project = project
        self.logger = logger
        if self.app is None:
            sys.exit(1)

    def init(self, parser, opts, args):
        pass

    def load(self):
        return self.app

    def load_config(self):
        self.cfg.set('on_starting', self.on_starting)
        self.cfg.set('when_ready', self.when_ready)
        self.cfg.set('post_worker_init', self.post_worker_init)
        self.cfg.set('worker_int', self.worker_int)
        self.cfg.set('worker_abort', self.worker_abort)

        default_yaml = os.path.realpath(os.path.join(os.path.dirname(__file__), 'default.yaml'))
        with open(default_yaml, 'r') as fp:
            content = fp.read()

        default_config = Dict(yaml.safe_load(content))
        config = default_config.get('gunicorn')
        config.update(settings.get('gunicorn'))
        for key in config:
            self.cfg.set(key, config[key])

    def run(self):
        if self.cfg.daemon:
            gunicorn.util.daemonize(self.cfg.enable_stdio_inheritance)
        super().run()

    def on_starting(self, server):
        self.logger.info('gunicorn is starting')
        os.makedirs(get_log_dir(), exist_ok=True)

    def when_ready(self, server):
        self.logger.info('gunicorn is ready')

    def post_worker_init(self, worker):
        self.logger.info('gunicorn worker inited')

    def worker_int(self, worker):
        pass

    def worker_abort(self, worker):
        pass
