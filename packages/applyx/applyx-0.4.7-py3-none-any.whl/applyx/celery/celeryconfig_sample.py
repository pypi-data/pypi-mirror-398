# coding=utf-8

import os
from celery.schedules import crontab

from applyx.conf import settings
settings.from_yaml(os.path.join(__file__, '../../conf/settings.yaml'))

# from applyx.celery.base import setup_signals
# setup_signals()


enable_utc = settings.get('celery.utc')
timezone = settings.get('celery.timezone')
broker_url = settings.get('celery.broker.url')
result_backend = settings.get('celery.result.backend')
result_expires = settings.get('celery.result.expires')
result_persistent = settings.get('celery.result.persistent')

worker_log_format = settings.get('celery.worker.log_format')
worker_task_log_format = settings.get('celery.worker.task_log_format')


imports = [
    'project.tasks.hello',
    'project.tasks.world',
]

task_routes = {
    'project.tasks.hello': {'queue': 'async'},
    'project.tasks.world': {'queue': 'cron'},
}

beat_schedule = {
    'world': {
        'task': 'project.tasks.world',
        'schedule': crontab(minute='*'),
    },
}
