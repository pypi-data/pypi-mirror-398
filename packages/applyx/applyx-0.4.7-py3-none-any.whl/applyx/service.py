# coding=utf-8

import time
import base64
from typing import Any

import requests
from loguru import logger
from mongoengine import Q

from applyx.conf import settings
from applyx.exception import InternalException
from applyx.mongo import MongoCache


class BaseService:
    pass


class HttpService(BaseService):
    def http(self, method: str, url: str, headers: dict[str, str]={}, timeout=30, **kwargs):
        logger.info(f'[http] {method} {url}')

        user_agent = f"{settings.get('project.name')}/{settings.get('project.version')}"
        headers.update({'User-Agent': user_agent})

        if headers:
            logger.info(f'[http] HEADERS {str(headers)}')

        params_data = kwargs.get('params', {})
        if params_data:
            logger.info(f'[http] PARAMS {str(params_data)}')

        json_data = kwargs.get('json', {})
        if json_data:
            logger.info(f'[http] JSON {str(json_data)}')

        try:
            response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
        except Exception as e:
            logger.error(f'[http] {e.__class__.__name__} {str(e)}')
            raise InternalException('外部服务不可用')

        status = response.status_code
        reason = response.reason
        if requests.codes.ok <= status <= requests.codes.partial_content:
            logger.info(f'[http] {status} - {reason}')
            result = response.json()
            return result

        logger.error(f'[http] {status} - {reason}')
        raise InternalException('外部服务不可用')


class ProxyService(HttpService):
    def __init__(self, endpoint=''):
        self.endpoint = endpoint

    def get(self, path, **kwargs):
        return self.make_request('GET', path, **kwargs)

    def post(self, path, **kwargs):
        return self.make_request('POST', path, **kwargs)

    def put(self, path, **kwargs):
        return self.make_request('PUT', path, **kwargs)

    def delete(self, path, **kwargs):
        return self.make_request('DELETE', path, **kwargs)

    def options(self, path, **kwargs):
        return self.make_request('OPTIONS', path, **kwargs)

    def head(self, path, **kwargs):
        return self.make_request('HEAD', path, **kwargs)

    def make_request(self, method, path, **kwargs):
        url = self.endpoint + path
        result = self.http(method, url, **kwargs)
        return result


class KongService(ProxyService):
    def __init__(self, service=''):
        if not service:
            raise InternalException('外部服务未指定')

        self.config = settings.get('kong.services').get(service)
        if not self.config:
            raise InternalException('外部服务配置不存在')

        gateway = settings.get('kong.gateway')
        version = self.config.version
        endpoint = f'http://{gateway}/{service}/v{version}'
        super().__init__(endpoint=endpoint)

    def make_request(self, method: str, path: str, **kwargs):
        auth_headers = self.make_auth_headers()
        headers = kwargs.pop('headers', {})
        headers.update(auth_headers)
        return super().make_request(method, path, headers=headers, **kwargs)

    def make_auth_headers(self):
        username = self.config['auth']['username']
        password = self.config['auth']['password']
        origin_auth = f'{username}:{password}'
        base64_auth = base64.b64encode(origin_auth.encode('utf8')).decode('utf8')
        return {'Authorization': f'Basic {base64_auth}'}


class MongoService(BaseService):
    model = None
    cache = None

    def secure_pick_fields(self, fields: list[str]=[], ref: list[str]=[]):
        ref = ref or list(self.model._fields.keys())
        return list(set(fields) & set(ref))

    def secure_sort_fields(self, fields: list[str]=[], ref: list[str]=[]):
        ref = ref or list(self.model._fields.keys())
        for index, field in enumerate(fields):
            if field.startswith('+') or field.startswith('-'):
                fields[index] = field[1:]
        return list(set(fields) & set(ref))

    def restrict_pick_fields(self, doc_json: dict[str, Any]={}, fields: list[str]=[]):
        if 'id' not in fields:
            fields.append('id')
        fields = self.secure_pick_fields(fields)
        restrict_doc_json = {}
        for field in fields:
            if field in doc_json:
                restrict_doc_json[field] = doc_json[field]
        return restrict_doc_json

    def create(self, **kwargs):
        now = int(time.time() * 1000)
        kwargs['created_at'] = now
        kwargs['updated_at'] = now

        doc = self.model(**kwargs)
        doc.switch_db('primary').save()

        doc_json = doc.dump()
        if self.cache:
            MongoCache(self.cache, self.model).set(str(doc.id))

        return doc_json

    def update(self, doc_id: str, **kwargs):
        now = int(time.time() * 1000)
        kwargs['updated_at'] = now
        docs = self.model.objects.scan_offline(id=doc_id)
        count = docs.using('primary').update(**kwargs)
        if not count:
            return 0

        if self.cache:
            MongoCache(self.cache, self.model).set(doc_id)

        return True if count else False

    def delete(self, doc_id: str, force=False):
        count = 0
        docs = self.model.objects.scan_offline(id=doc_id)
        if force:
            count = docs.using('primary').delete()
        else:
            count = docs.using('primary').update(is_deleted=1)

        if self.cache:
            MongoCache(self.cache, self.model).unset(doc_id)

        return True if count else False

    def get(self, doc_id: str, fields: list[str]=[]):
        if self.cache:
            doc_json = MongoCache(self.cache, self.model).get(doc_id, fields=fields)
            if doc_json:
                return doc_json

        docs = self.model.objects.scan_offline(is_deleted=0)
        docs = docs.exclude(*self.model.FIELDS.get('exclude', []))

        doc = docs.scan_offline(id=doc_id).first()
        if not doc:
            return None

        doc_json = doc.dump()
        if self.cache:
            MongoCache(self.cache, self.model).set(doc_id)

        return self.restrict_pick_fields(doc_json, fields=fields)

    def get_many(self, doc_ids: list[str], fields: list[str]=[], bulk=False):
        doc_json_list = []

        uncached_doc_ids = []
        for doc_id in doc_ids:
            doc_json = None
            if self.cache:
                doc_json = MongoCache(self.cache, self.model).get(doc_id, fields=fields)

            if doc_json:
                doc_json = self.restrict_pick_fields(doc_json, fields=fields)
                doc_json_list.append(doc_json)
            else:
                uncached_doc_ids.append(doc_id)

        docs = self.model.objects.scan_offline(is_deleted=0)
        docs = docs.exclude(*self.model.FIELDS.get('exclude', []))
        uncached_docs = docs.scan_offline(id__in=uncached_doc_ids)

        for doc in uncached_docs:
            doc_json = doc.dump()
            doc_json = self.restrict_pick_fields(doc_json, fields=fields)
            doc_json_list.append(doc_json)
            if self.cache:
                MongoCache(self.cache, self.model).set(doc_id)

        if not bulk:
            return doc_json_list

        doc_json_bulk = dict([(doc_json['id'], doc_json) for doc_json in doc_json_list])
        return doc_json_bulk

    def paginate(self, page=1, per_page=10, keyword='', sort: list[str]=[], fields: list[str]=[]):
        docs = self.model.objects.scan_offline(is_deleted=0)
        docs = docs.exclude(*self.model.FIELDS.get('exclude', []))

        if keyword:
            query = Q()
            for field in self.model.FIELDS.get('search', []):
                kwargs = {f'{field}__icontains': keyword}
                query = query | Q(**kwargs)
            docs = docs.scan_offline(query)

        sort = self.secure_sort_fields(sort)
        docs = docs.order_by(*sort)
        total = docs.all_fields().only('id').count()

        page = page if page > 0 else 1
        per_page = per_page if per_page > 0 else 10
        if per_page > 0:
            start_index = (page - 1) * per_page
            end_index = page * per_page
            docs = docs[start_index:end_index]

        doc_ids = [str(doc.id) for doc in docs]
        doc_json_list = self.get_many(doc_ids, fields=fields)
        return total, doc_json_list
