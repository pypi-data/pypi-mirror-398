# coding=utf-8

import json
import threading
from typing import Any
from zoneinfo import ZoneInfo

import mongoengine as me
from mongoengine import Document as MongoDocument
from addict import Dict
from loguru import logger

from applyx.conf import settings
from applyx.utils import check_connection
from applyx.redis import RedisManager


class Document(MongoDocument):
    def __init__(self, *args, **kwargs):
        self._only_fields = kwargs.get('__only_fields', [])
        super().__init__(*args, **kwargs)

    def dict(self):
        record = {}
        for name, field in self._fields.items():
            if self._only_fields and name not in self._only_fields:
                continue
            value = getattr(self, name)
            record[name] = value
            if isinstance(field, me.ObjectIdField):
                record[name] = str(value)
            elif isinstance(field, me.DateField):
                if value is not None:
                    record[name] = value.strftime('%Y-%m-%d')
            elif isinstance(field, me.DateTimeField):
                if value is not None:
                    record[name] = value.strftime('%Y-%m-%d %H:%M:%S')

        if 'id' not in record:
            record['id'] = str(self.id)

        return record

    meta = {
        'abstract': True,
    }


class MongoIterator:
    def __init__(self, query_set):
        self.query_set = query_set
        self.only_fields = self.query_set.only_fields

    def __iter__(self):
        return self

    def __next__(self):
        try:
            doc = self.query_set.next()
            doc_json = doc.dump()
            if not self.only_fields:
                return doc_json

            _fields = list(doc_json.keys())
            for _field in _fields:
                if _field != 'id' and _field not in self.only_fields:
                    doc_json.pop(_field)

            return doc_json
        except StopIteration as e:
            raise e


class MongoCache:
    def __init__(self, alias: str, model=None):
        self.redis = RedisManager.instance().get(alias)
        self.model = model

    def get(self, doc_id: str, fields: list[str]=[]):
        doc_name = self.model.__name__.lower()
        doc_key = f'cache:{doc_name}:{doc_id}'
        if not self.redis.exists(doc_key):
            return None

        if not fields:
            hash_json = self.redis.hgetall(doc_key)
        else:
            if 'id' not in fields:
                fields.append('id')
            values = self.redis.hmget(doc_key, *fields)
            hash_json = dict(zip(fields, values))

        doc_json = {'id': hash_json['id']}
        doc_fields = getattr(self.model, '_fields')

        for key in doc_fields:
            if fields and key not in fields:
                continue

            field = doc_fields[key]
            value = hash_json.get(key)
            if value is None:
                doc_json[key] = field.default
                continue

            elif isinstance(field, (me.IntField, me.FloatField)):
                value = eval(value)

            elif isinstance(field, me.DictField):
                value = json.loads(value)

            elif isinstance(field, me.ListField):
                value = self.redis.lrange(value, 0, -1)

            doc_json[key] = value

        return doc_json

    def set(self, doc_id: str, expire=600):
        doc_name = self.model.__name__.lower()
        doc_key = f'cache:{doc_name}:{doc_id}'
        self.redis.delete(doc_key)

        doc = self.model.objects.with_id(doc_id)
        if not doc:
            return None
        doc_json = doc.dump()

        doc_fields = getattr(self.model, '_fields')

        hash_json = {}
        list_field_keys = []
        for key in doc_fields:
            field = doc_fields[key]
            value = doc_json.get(key, field.default)
            if value is None:
                continue

            elif isinstance(value, dict):
                value = str(value)

            elif isinstance(value, list):
                field_key = f'cache:{doc_name}:{doc_id}:{key}'
                self.redis.rpush(field_key, *value)
                list_field_keys.append(field_key)
                value = field_key

            hash_json[key] = value

        self.redis.hmset(doc_key, hash_json)
        self.redis.expire(doc_key, expire)

        for key in list_field_keys:
            # delay 1s for retrieve
            self.redis.expire(key, expire + 1)

        return doc_key

    def unset(self, doc_id: str):
        doc_name = self.model.__name__.lower()
        doc_key = f'cache:{doc_name}:{doc_id}'
        self.redis.delete(doc_key)


class MongoManager:

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
        self.engines: dict[str, Any] = {}

    def init_all_mongo(self):
        if not settings.get('mongodb'):
            return
        for name in settings.get('mongodb'):
            config = settings.get('mongodb').get(name)
            config.update(Dict({'name': name}))
            config.tz_aware = True
            config.tzinfo = ZoneInfo(settings.get('project.timezone'))

            if not check_connection(config.host, config.port):
                logger.error(f'mongo server {config.host}:{config.port} connection refused')
                continue

            self.engines[name] = me.connect(**config)
            logger.info(f'mongodb [{name}] ready.')

    def close_all_mongo(self):
        if not settings.get('mongodb'):
            return
        for name in settings.get('mongodb'):
            me.connection.disconnect(name)
            self.engines.pop(name)
            logger.info(f'mongodb [{name}] closed.')
