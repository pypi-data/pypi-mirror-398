# coding=utf-8

from applyx.command.base import BaseScript
from applyx.utils import get_store_dir


class Script(BaseScript):
    """
    demo script
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store_dir = get_store_dir()

    def run(self):
        print(self.store_dir)
