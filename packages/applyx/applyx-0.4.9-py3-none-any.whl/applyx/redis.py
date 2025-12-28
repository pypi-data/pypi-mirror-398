# coding=utf-8

import threading
from typing import Any
from importlib import import_module

import redis
from loguru import logger

from applyx.conf import settings
from applyx.utils import check_connection


class RedisManager:

    _mutex = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        with cls._mutex:
            if cls._instance is None:
                cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def setup(cls):
        cls._instance = cls()

    @classmethod
    def instance(cls):
        return cls._instance

    def __init__(self):
        self.engines: dict[str, redis.StrictRedis | Any] = {}

    def get(self, alias):
        return self.engines.get(alias)

    def init_redis(self, alias: str):
        if not settings.get('redis'):
            return
        config = settings.get('redis').get(alias)
        if not config:
            return

        if alias in self.engines:
            return

        if not config.get('startup_nodes'):
            if not check_connection(config.host, config.port):
                logger.error(f'redis server {config.host}:{config.port} connection refused')
                return

            self.engines[alias] = redis.StrictRedis(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                max_connections=config.max_connections,
                decode_responses=config.decode_responses,
            )
        else:
            rediscluster = import_module('rediscluster')
            self.engines[alias] = rediscluster.RedisCluster(
                startup_nodes=config.startup_nodes,
                max_connections=config.max_connections,
            )

        logger.info(f'redis [{alias}] ready.')

    def close_redis(self, alias):
        if alias not in self.engines:
            return
        pool = self.engines[alias].connection_pool
        pool.disconnect()
        self.engines.pop(alias)

        logger.info(f'redis [{alias}] closed.')

    def init_all_redis(self):
        if not settings.get('redis'):
            return
        for alias in settings.get('redis'):
            self.init_redis(alias)

    def close_all_redis(self):
        if not settings.get('redis'):
            return
        for alias in settings.get('redis'):
            self.close_redis(alias)
