# coding=utf-8

from loguru import logger

from applyx.celery.base import BaseTask, taskclass
from applyx.utils import get_store_dir


@taskclass
class Task(BaseTask):
    """
    demo task
    """

    def __init__(self):
        super().__init__()
        self.store_dir = get_store_dir()

    def run(self, *args, **kwargs):
        print(self.store_dir)
        logger.info('task done')
