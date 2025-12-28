# coding=utf-8

import threading

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from addict import Dict
from loguru import logger

from applyx.conf import settings
from applyx.utils import check_connection


Base = declarative_base()


class MySQLManager:

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
        self.engines: dict[str, sqlalchemy.Engine] = {}

    def init_all_mysql(self):
        if not settings.get('mysql'):
            return
        for name in settings.get('mysql'):
            config = settings.get('mysql').get(name)
            config.update(Dict({'name': name}))
            if not check_connection(config.host, config.port):
                logger.error(f'mysql server {config.host}:{config.port} connection refused')
                continue

            connection_string = 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'.format(**config)
            self.engines[name] = sqlalchemy.create_engine(
                connection_string,
                echo=True,
                max_overflow=0,
                pool_size=config.pool.size,
                pool_timeout=config.pool.timeout,
                pool_recycle=config.pool.recycle,
            )
            # from sqlalchemy.orm import sessionmaker
            # session_cls = sessionmaker(bind=engine)
            # session = session_cls()

            logger.info(f'mysql [{name}] ready.')

    def close_all_mysql(self):
        if not settings.get('mysql'):
            return
        for name in settings.MYSQL:
            engine = self.engines[name]
            engine.dispose()
            self.engines.pop(name)
            logger.info(f'mysql [{name}] closed.')
