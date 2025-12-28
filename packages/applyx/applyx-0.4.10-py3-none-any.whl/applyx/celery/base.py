# coding=utf-8

import sys
import os
import logging
from logging import FileHandler
from logging.handlers import RotatingFileHandler

import celery
from loguru import logger

from applyx.conf import settings
from applyx.log import LogFormatter
from applyx.utils import get_log_dir


def on_setup_logging(**kwargs):
    os.makedirs(get_log_dir(), exist_ok=True)

    logger.level('DEBUG', icon='D')
    logger.level('INFO', icon='I')
    logger.level('SUCCESS', icon='S')
    logger.level('WARNING', icon='W')
    logger.level('ERROR', icon='E')
    logger.level('CRITICAL', icon='C')

    os.environ.setdefault('LOGURU_FORMAT', settings.get('logging.format.simple'))
    logger.remove()
    logger.add(sys.stderr, format=settings.get('logging.format.simple'))

    celery_logger = kwargs['logger']
    logfile_path = os.path.join(get_log_dir(), 'celery.log')
    logfile_handler = RotatingFileHandler(
        filename=logfile_path,
        maxBytes=settings.get('logging.handlers.file.rotate.max_bytes'),
        backupCount=settings.get('logging.handlers.file.rotate.backup_count'),
        encoding='utf8',
    )
    logfile_handler.setFormatter(LogFormatter(settings.get('logging.format.default')))
    logfile_handler.setLevel(logging.DEBUG)
    celery_logger.addHandler(logfile_handler)


def on_worker_process_init(**kwargs):
    from applyx.redis import RedisManager

    RedisManager.setup()
    RedisManager.instance().init_all_redis()

    from applyx.mongo import MongoManager

    MongoManager.setup()
    MongoManager.instance().init_all_mongo()

    from applyx.mysql import MySQLManager

    MySQLManager.setup()
    MySQLManager.instance().init_all_mysql()


def on_worker_process_shutdown(**kwargs):
    from applyx.redis import RedisManager

    RedisManager.instance().close_all_redis()

    from applyx.mongo import MongoManager

    MongoManager.instance().close_all_mongo()

    from applyx.mysql import MySQLManager

    MySQLManager.instance().close_all_mysql()


def on_task_internal_error(**kwargs):
    logger = logging.getLogger('celery')
    logger.error(kwargs)


def on_task_unknown(**kwargs):
    logger = logging.getLogger('celery')
    logger.error(kwargs)


# https://docs.celeryproject.org/en/latest/userguide/signals.html
def setup_signals():
    celery.signals.after_setup_logger.connect(on_setup_logging)
    celery.signals.worker_process_init.connect(on_worker_process_init)
    celery.signals.worker_process_shutdown.connect(on_worker_process_shutdown)
    celery.signals.task_unknown.connect(on_task_internal_error)
    celery.signals.task_unknown.connect(on_task_unknown)


class BaseTask(celery.Task):
    def __init__(self):
        self.name = self.__module__
        self.logging = {
            'level': logging.DEBUG,
            'format': (
                '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> '
                '<level>{level.icon}</level> '
                '<cyan>({process},{thread})</cyan> '
                '- <level>[{extra[task_id]}] {message}</level>'
            ),
            'persistence': {
                'enable': False,
                'inited': False,
            }
        }

    def enable_logging_persistence(self):
        self.logging['persistence']['enable'] = True
        self.logging['persistence']['inited'] = False

    def check_logging_persistence(self):
        if not self.logging['persistence']['enable']:
            return
        if self.logging['persistence']['inited']:
            return

        task_name = self.name.split('.')[-1]
        sink = FileHandler(
            filename=os.path.join(get_log_dir(), f'celery.{task_name}.log'),
            encoding='utf8',
        )

        logger.configure(extra={'task_id': 'x'})
        logger_filter = lambda record: record['extra'].get('name') == self.name
        logger.add(sink=sink, level=self.logging['level'], format=self.logging['format'], filter=logger_filter)
        self.logging['persistence']['inited'] = True

    def get_app(self):
        return self._get_app()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        with logger.contextualize(name=self.name, task_id=task_id):
            logger.error(einfo)

    def __call__(self, *args, **kwargs):
        self.check_logging_persistence()

        task_id = self.request.id or '-'
        with logger.contextualize(name=self.name, task_id=task_id):
            super().__call__(*args, **kwargs)


def taskclass(name: str | None=None):
    def wrapper(cls):
        if not issubclass(cls, BaseTask):
            raise Exception('Unknown celery task')
        task_name = name or cls.__module__
        func_wrapper = celery.current_app.task(base=cls, name=task_name, bind=True)
        cls.run = func_wrapper(cls.run)
        return cls
    return wrapper
