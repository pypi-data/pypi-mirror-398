# coding=utf-8

import sys
import os
from types import ModuleType
from typing import Callable
import yaml
import logging
import traceback
from importlib import import_module
from logging.handlers import RotatingFileHandler

# from celery import Celery
from loguru import logger
from addict import Dict
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi import FastAPI, APIRouter, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from applyx.conf import settings
from applyx.exception import InternalException
from applyx.jinja2 import FILTERS, TESTS
from applyx.web.middlewares import RequestMiddleware, RedisSessionMiddleware
from applyx.utils import get_log_dir


class FastAPIBuilder:
    @classmethod
    def get_app(cls, project: ModuleType, debug=False):
        module_path = f'{project.__package__}.web.builder'
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            builder_cls = cls
        else:
            builder_cls = getattr(module, 'Builder', None)
            if builder_cls is None or not issubclass(builder_cls, cls):
                print(f'Invalid fastapi builder path {module_path}.Builder')
                return None

        builder = builder_cls(project, debug)
        builder.make()
        return builder.app

    def __init__(self, project: ModuleType, debug=False):
        self.project = project
        self.debug = debug
        self.server_dir = os.path.realpath(os.path.join(project.__path__[0], 'web'))
        self.config = Dict()
        self.app = None

    def make(self):
        self.init_config()
        self.init_logging()

        if self.debug:
            logger.warning('Debug mode is on.')

        fastapi_kwargs = dict(debug=self.debug)
        if self.debug:
            fastapi_kwargs.update(
                openapi_url=self.config.get('openapi_url', '/openapi.json'),
                docs_url=self.config.get('docs_url' '/docs'),
                redoc_url=self.config.get('redoc_url', '/redoc'),
            )
        else:
            fastapi_kwargs.update(openapi_url=None, docs_url=None, redoc_url=None)

        self.app = FastAPI(title=settings.get('project.name'), **fastapi_kwargs)
        self.app.globals = Dict()

        if self.config.get('static_dir'):
            path = os.path.realpath(os.path.join(settings.get('project.workspace'), self.project.__name__, self.config.static_dir))
            if os.path.exists(path):
                self.app.mount('/static', StaticFiles(directory=path), name='static')

        self.setup_jinja2()
        self.setup_exception_handlers()
        self.setup_event_handlers()
        self.setup_middlewares()
        self.setup_routes()

    def init_config(self):
        default_yaml = os.path.realpath(os.path.join(os.path.dirname(__file__), 'default.yaml'))
        with open(default_yaml, 'r') as fp:
            content = fp.read()

        default_config = Dict(yaml.safe_load(content))
        self.config = default_config.get('web')
        self.config.update(settings.get('web'))

    def init_logging(self):
        sink = RotatingFileHandler(
            filename=os.path.join(get_log_dir(), 'server-web.log'),
            maxBytes=settings.get('logging.handlers.file.rotate.max_bytes'),
            backupCount=settings.get('logging.handlers.file.rotate.backup_count'),
            encoding='utf8',
        )
        logging_level = logging.DEBUG if self.debug else settings.get('logging.level')

        logger.remove()
        logger.configure(extra={'mdc': 'x'})
        logger.add(sink=sys.stderr, level=logging_level, format=settings.get('logging.format.web'))
        logger.add(sink=sink, level=logging_level, format=settings.get('logging.format.web'))

    def setup_jinja2(self):
        path = os.path.join(self.server_dir, self.config.get('template_dir'))
        if not os.path.exists(path):
            return

        self.app.jinja_templates = Jinja2Templates(directory=path)
        env = self.app.jinja_templates.env
        env.filters.update(FILTERS)
        env.tests.update(TESTS)
        env.globals.update({'GLOBALS': settings.get('web.jinja.globals')})

    def setup_middlewares(self):
        if self.config.gzip.get('enable'):
            self.app.add_middleware(GZipMiddleware, minimum_size=self.config.gzip.get('minimum_size', 1000))

        if self.config.cors.get('enable'):
            self.app.add_middleware(
                CORSMiddleware,
                max_age=self.config.cors.access_control.get('max_age', 60),
                allow_credentials=self.config.cors.access_control.get('allow_credentials', True),
                allow_origins=self.config.cors.access_control.get('allow_origins', ['*']),
                allow_methods=self.config.cors.access_control.get('allow_methods', ['*']),
                allow_headers=self.config.cors.access_control.get('allow_headers', ['*']),
            )

        if self.config.session.get('enable'):
            if settings.get('redis') and self.config.session.get('redis_alias') in settings.get('redis'):
                self.app.add_middleware(RedisSessionMiddleware, config=self.config.session)
            else:
                self.app.add_middleware(SessionMiddleware, secret_key=self.config.session.get('secret_key', 'secret-key'))

        self.app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=self.config.proxy.get('trusted_hosts', ['*']))
        self.app.add_middleware(RequestMiddleware)

    def setup_exception_handlers(self):
        self.app.add_exception_handler(Exception, self.wrap_handler(self.generic_exception_handler))
        self.app.add_exception_handler(InternalException, self.wrap_handler(self.generic_exception_handler))
        self.app.add_exception_handler(RequestValidationError, self.wrap_handler(self.request_validation_error_handler))
        self.app.add_exception_handler(HTTPException, self.wrap_handler(self.http_exception_handler))

    def wrap_handler(self, func: Callable[[Request, Exception], Response]):
        def wrapped_func(request: Request, exec: Exception):
            if request.url.path.startswith('/static'):
                response = func(request, exec)
                return response

            with logger.contextualize(mdc=request.state.id):
                endpoint = request.scope.get('endpoint')
                if endpoint is None:
                    logger.warning('[endpoint] no endpoint found')
                else:
                    logger.error(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

                response = func(request, exec)

            response.headers['X-Request-Id'] = request.state.id
            return response

        return wrapped_func

    def generic_exception_handler(self, request: Request, exc: Exception):
        stack = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(stack)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=dict(err=1, msg=str(exc)),
        )

    def request_validation_error_handler(self, request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=dict(err=1, msg='Request Validation Error.', data=jsonable_encoder(exc.errors())),
        )

    def http_exception_handler(self, request: Request, exc: HTTPException):
        return HTMLResponse(status_code=exc.status_code, content=f'{exc.status_code} - {exc.detail}')

    def setup_event_handlers(self):
        self.app.add_event_handler('startup', self.on_startup)
        self.app.add_event_handler('shutdown', self.on_shutdown)

    async def on_startup(self):
        # if settings.get('celery.broker.url'):
        #     self.app.celery = Celery()
        #     try:
        #         config = import_module(f'{self.project.__package__}.celery.config')
        #         self.app.celery.config_from_object(config)
        #     except Exception as e:
        #         logger.exception('Celery init error', exc_info=e)
        pass

    async def on_shutdown(self):
        pass

    def setup_routes(self):
        base_path = os.path.join(self.server_dir, 'routes')
        package_dir = os.path.realpath(os.path.join(self.project.__path__[0], os.pardir))
        for filename in os.listdir(base_path):
            full_pathname = os.path.join(base_path, filename)
            if not filename.endswith('.py') or not os.path.isfile(full_pathname):
                continue

            module_path = full_pathname[len(package_dir) + 1: -len('.py')].replace(os.sep, '.')
            module = import_module(module_path)
            router = getattr(module, 'router', None)
            if router is None or not isinstance(router, APIRouter):
                continue

            self.app.include_router(router)

            py_path = full_pathname[len(package_dir) + 1:]
            for route in router.routes:
                for method in route.methods:
                    logger.info(f'{method} {route.path} => {py_path}:{route.name}')
