# coding=utf-8

import argparse
from typing import Any

from applyx.conf import settings
from applyx.command.base import BaseCommand


class Command(BaseCommand):
    def register(self, subparser: Any):
        subparser.add_parser('shell', help='open python shell')

    def invoke(self, args: argparse.Namespace):
        import IPython
        from applyx.redis import RedisManager
        from applyx.mongo import MongoManager
        from applyx.mysql import MySQLManager

        RedisManager.setup()
        RedisManager.instance().init_all_redis()
        MongoManager.setup()
        MongoManager.instance().init_all_mongo()
        MySQLManager.setup()
        MySQLManager.instance().init_all_mysql()

        banner = f"\nIPython shell for {settings.get('project.name')}\n"
        context = {'REDIS': RedisManager.instance().engines}
        IPython.embed(banner1=banner, user_ns=context, using=False)
