# coding=utf-8

import argparse
from typing import Any

from applyx.command.base import BaseCommand


class Command(BaseCommand):
    def register(self, subparser: Any):
        parser = subparser.add_parser('gunicorn', help='run gunicorn application')
        parser.add_argument(
            '--daemon',
            action='store_true',
            dest='daemon',
            default=False,
            help='enable daemon mode',
        )

    def invoke(self, args: argparse.Namespace):
        from uvicorn.workers import UvicornH11Worker
        from applyx.gunicorn.app import GunicornApplication

        UvicornH11Worker.CONFIG_KWARGS.update({'headers': [('Server', 'Linux')]})

        gunicorn_app = GunicornApplication.get_app(self.project)
        if gunicorn_app is None:
            return

        gunicorn_app.cfg.set('daemon', args.daemon)
        gunicorn_app.run()
