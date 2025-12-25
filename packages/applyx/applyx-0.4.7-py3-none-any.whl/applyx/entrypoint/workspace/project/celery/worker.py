# coding=utf-8

import os

from applyx.conf import settings
settings.from_yaml(os.path.join(__file__, '../../conf/settings.yaml'))

from applyx.celery.base import setup_signals
setup_signals()

enable_utc = settings.get('celery.utc')
timezone = settings.get('celery.timezone')
broker_url = settings.get('celery.broker.url')
broker_connection_retry_on_startup = settings.get('celery.broker.connection.retry_on_startup')


imports = [
    'project.celery.tasks.demo',
]
