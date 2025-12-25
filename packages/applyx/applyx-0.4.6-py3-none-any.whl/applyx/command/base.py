# coding=utf-8

import sys
import os
import json
import logging
import argparse
import traceback
from types import ModuleType
from typing import Any, cast
from importlib import import_module
from logging import FileHandler

from loguru import logger

from applyx.conf import settings
from applyx.utils import check_connection, get_log_dir


class BaseScript:
    def __init__(self, variables: dict[str, Any]={}, debug=False, **kwargs):
        self.variables = variables
        self.debug = debug

    def init_logger(self):
        _, _, name = self.__class__.__module__.split('.')
        sink = FileHandler(filename=os.path.join(get_log_dir(), f'scripts.{name}.log'), encoding='utf8')
        logging_level = logging.DEBUG if self.debug else settings.get('logging.level')
        logger.add(sink=sink, level=logging_level, format=os.environ.get('LOGURU_FORMAT'))

    def run(self):
        raise NotImplementedError


class KafkaScript(BaseScript):
    topic = ''
    group_id: str | None = None
    message: str | None = None
    consumer = None

    def get_logging_format(self):
        logging_format = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> '
            '<level>{level.icon}</level> '
            '<cyan>({process},{thread})</cyan> '
            '- <level>[{extra[offset]}] {message}</level>'
        )
        logger.configure(extra={'offset': 'x'})
        return logging_format

    def run(self):
        config = settings.get('kafka')
        if config is None:
            raise Exception('missing settings for kafka')

        for server in config['servers']:
            host, port = server.split(':')
            if not check_connection(host, int(port)):
                logger.error(f'kafka server {host}:{port} connection refused')
                sys.exit(0)

        import kafka
        self.consumer = kafka.KafkaConsumer(
            self.topic,
            group_id=self.group_id,
            bootstrap_servers=config['servers'],
            auto_offset_reset='latest',
            value_deserializer=json.loads,
        )

        logger.info(f'listening on {self.topic}')

        try:
            for message in self.consumer:
                self.message = message
                logger.info(f'[payload] {message.value}')
                with logger.contextualize(offset=message.offset):
                    self.on_message()
        except Exception:
            logger.error(traceback.format_exc())

    def on_message(self):
        raise NotImplementedError


class BaseCommand:
    def __init__(self, project: ModuleType):
        self.project = project

    def register(self, subparser: Any):
        raise NotImplementedError

    def invoke(self, args: argparse.Namespace):
        raise NotImplementedError


class Manager:
    def __init__(self, project, mask=None):
        self.project = project
        if mask:
            os.umask(mask)  # consider to set mask = stat.S_IRWXG | stat.S_IRWXO for security

        project_config_path = os.path.join(project.__path__[0], 'conf/settings.yaml')
        settings.from_yaml(project_config_path)
        self.setup_logger()

    def setup_logger(self):
        os.makedirs(get_log_dir(), exist_ok=True)
        logger.level('DEBUG', icon='D')
        logger.level('INFO', icon='I')
        logger.level('SUCCESS', icon='S')
        logger.level('WARNING', icon='W')
        logger.level('ERROR', icon='E')
        logger.level('CRITICAL', icon='C')

        os.environ.setdefault('LOGURU_FORMAT', settings.get('logging.format.simple'))
        logger.remove()
        logger.add(sys.stderr, format=os.environ.get('LOGURU_FORMAT'))

    def run(self,):
        parser = argparse.ArgumentParser(description=f"help for {settings.get('project.name')} entrypoint")
        parser.add_argument('-v', '--version', action='version', version=settings.get('project.version'))
        subparser = parser.add_subparsers(dest='cmd')
        cmd_module_names = ['web', 'mcp', 'gunicorn', 'script', 'shell', 'clean']
        commands: dict[str, BaseCommand] = {}
        for cmd in cmd_module_names:
            cmd_module = import_module(f'applyx.command.{cmd}')
            cmd_class = getattr(cmd_module, 'Command', None)
            if cmd_class is not None:
                cmd_instance = cmd_class(self.project)
                cmd_instance = cast(BaseCommand, cmd_instance)
                cmd_instance.register(subparser)
                commands[cmd] = cmd_instance

        argv = sys.argv[1:] if sys.argv[1:] else ['-h']
        args = parser.parse_args(argv)
        cmd = args.__dict__.pop('cmd')

        try:
            commands[cmd].invoke(args)
        except KeyboardInterrupt:
            sys.exit(0)
