# coding=utf-8

import os
import argparse
from typing import Any

from applyx.command.base import BaseCommand
from applyx.utils import get_log_dir


class Command(BaseCommand):
    def register(self, subparser: Any):
        parser = subparser.add_parser('web', help='run fastapi application')
        parser.add_argument(
            '--host',
            type=str,
            dest='host',
            default='0.0.0.0',
            help='specify server host',
        )
        parser.add_argument(
            '--port',
            type=int,
            dest='port',
            default=8000,
            help='specify server port',
        )
        parser.add_argument(
            '--workers',
            type=int,
            dest='workers',
            default=os.cpu_count(),
            help='specify concurrency workers',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            dest='debug',
            default=False,
            help='enable the Uvicorn debugger',
        )

    def invoke(self, args: argparse.Namespace):
        import logging
        from uvicorn import Config, Server
        from applyx.conf import settings
        from applyx.web.builder import FastAPIBuilder

        fastapi_app = FastAPIBuilder.get_app(self.project, args.debug)
        if fastapi_app is None:
            return

        log_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    '()': 'uvicorn.logging.DefaultFormatter',
                    'fmt': settings.get('logging.format.default'),
                    'use_colors': False,
                },
                'access': {
                    '()': 'uvicorn.logging.AccessFormatter',
                    'fmt': settings.get('logging.format.uvicorn'),
                    'use_colors': False,
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stderr',
                    'formatter': 'default',
                },
                'default': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'default',
                    'filename': os.path.join(get_log_dir(), 'uvicorn.error.log'),
                    'maxBytes': settings.get('logging.handlers.file.rotate.max_bytes'),
                    'backupCount': settings.get('logging.handlers.file.rotate.backup_count'),
                    'encoding': 'utf8',
                },
                'access': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'access',
                    'filename': os.path.join(get_log_dir(), 'uvicorn.access.log'),
                    'maxBytes': settings.get('logging.handlers.file.rotate.max_bytes'),
                    'backupCount': settings.get('logging.handlers.file.rotate.backup_count'),
                    'encoding': 'utf8',
                },
            },
            'loggers': {
                'uvicorn': {
                    'handlers': ['console', 'default'],
                    'level': logging.INFO,
                },
                'uvicorn.error': {
                    'handlers': ['console', 'default'],
                    'level': logging.INFO,
                    'propagate': False,
                },
                'uvicorn.access': {
                    'handlers': ['access'],
                    'level': logging.INFO,
                    'propagate': False,
                },
            },
        }

        config = Config(
            fastapi_app,
            host=args.host,
            port=args.port,
            reload=args.debug,
            workers=args.workers,
            log_config=log_config,
            server_header=False,
        )
        Server(config=config).run()
