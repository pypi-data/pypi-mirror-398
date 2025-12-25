# coding=utf-8

import os
from io import BytesIO
from importlib import import_module
from typing import cast

import requests
from loguru import logger

from applyx.conf import settings
from applyx.utils import get_store_dir


def init_storage():
    parts = settings.get('storage.class_path').split('.')
    module_path = '.'.join(parts[:-1])
    module = import_module(module_path)
    storage_class = getattr(module, parts[-1])
    storage_instance = storage_class()
    storage_instance = cast(BaseStorage, storage_instance)
    return storage_instance


class BaseStorage:
    def path(self, filename: str):
        return filename

    def url(self, filename: str):
        if not self.exists(filename):
            raise Exception(f'{filename} not exists')

        return f"{settings.get('storage.uri_prefix')}/{settings.get('project.folder.store')}/{filename}"

    def exists(self, filename: str):
        raise NotImplementedError

    def size(self, filename: str):
        raise NotImplementedError

    def delete(self, filename: str):
        raise NotImplementedError

    def open(self, filename: str):
        raise NotImplementedError

    def save(self, filename: str, content: BytesIO, overwrite=True, **kwargs):
        raise NotImplementedError


class LocalStorage(BaseStorage):
    def path(self, filename: str):
        return os.path.join(get_store_dir(), filename)

    def exists(self, filename: str):
        return os.path.exists(self.path(filename))

    def size(self, filename: str):
        if not self.exists(filename):
            raise Exception(f'{filename} not exists')

        return os.path.getsize(self.path(filename))

    def delete(self, filename: str):
        if not self.exists(filename):
            return

        os.remove(self.path(filename))

    def open(self, filename: str):
        if not self.exists(filename):
            return None

        def chunks(src, chunk_size=1024 * 512):
            src.seek(0)
            while True:
                data = src.read(chunk_size)
                if not data:
                    break
                yield data

        content = BytesIO()
        with open(self.path(filename), 'rb') as fp:
            for chunk in chunks(fp):
                content.write(chunk)

        return content

    def save(self, filename: str, content: BytesIO, overwrite=False, **kwargs):
        if self.exists(filename) and not overwrite:
            raise Exception(f'{filename} exists')

        path = self.path(filename)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        def chunks(src, chunk_size=1024 * 512):
            src.seek(0)
            while True:
                data = src.read(chunk_size)
                if not data:
                    break
                yield data

        content.seek(0)
        with open(path, 'wb') as fp:
            for chunk in chunks(content):
                fp.write(chunk)


class AliyunStorage(BaseStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = settings.get('aliyun')
        if self.config is None:
            raise Exception('missing settings for aliyun')

        import oss2

        auth = oss2.Auth(self.config['key_id'], self.config['key_secret'])
        endpoint = f"http://{self.config['host']}"
        self.bucket = oss2.Bucket(auth, endpoint, self.config['oss']['bucket'])

    def path(self, filename: str):
        return os.path.join(settings.get('project.folder.store'), filename)

    def exists(self, filename: str):
        return self.bucket.object_exists(self.path(filename))

    def size(self, filename: str):
        if not self.exists(filename):
            raise Exception(f'{filename} not exists')

        res = self.bucket.head_object(self.path(filename))
        headers = dict([item for item in res.headers.raw_items()])
        return int(headers.get('Content-Length', '0'))

    def delete(self, filename: str):
        if not self.exists(filename):
            return

        self.bucket.delete_object(self.path(filename))

    def open(self, filename: str):
        if not self.exists(filename):
            return None

        res = self.bucket.get_object(self.path(filename))
        content = BytesIO()
        content.write(res.read())
        content.seek(0)
        return content

    def save(self, filename: str, content: BytesIO, overwrite=False, **kwargs):
        if self.exists(filename) and not overwrite:
            raise Exception(f'{filename} exists')

        headers = {
            'Cache-Control': f"max-age={self.config['cache_age']}",
        }

        # 当无法确定待上传的数据长度时，progress_callback的第二个参数（total_bytes）为 None
        def callback(consumed_bytes: int, total_bytes: int):
            if total_bytes:
                percentage = int((float(consumed_bytes) / float(total_bytes)) * 100)
                logger.debug(f'oss upload : {percentage}%%')

        path = self.path(filename)
        content.seek(0)
        res = self.bucket.put_object(
            path, content, headers=headers, progress_callback=callback
        )
        logger.info(f'aliyun : {res.request_id} - {res.status}')
        if res.status != requests.codes.ok:
            raise Exception('aliyun save failure')


class AwsStorage(BaseStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = settings.get('aws')
        if self.config is None:
            raise Exception('missing settings for aws')

        import boto3
        from botocore.config import Config

        self.client = boto3.client(
            's3',
            region_name=self.config['region_name'],
            aws_access_key_id=self.config['access_key_id'],
            aws_secret_access_key=self.config['secret_access_key'],
            config=Config(proxies=self.config['proxies'])
            if self.config.get('proxies')
            else None,
        )
        self.bucket = self.config['s3']['bucket']

    def path(self, filename: str):
        return os.path.join(settings.get('project.folder.store'), filename)

    def exists(self, filename: str):
        try:
            res = self.client.head_object(Bucket=self.bucket, Key=self.path(filename))
        except Exception:
            return False

        return res['ResponseMetadata']['HTTPStatusCode'] == requests.codes.ok

    def size(self, filename: str):
        if not self.exists(filename):
            return

        res = self.bucket.head_object(Bucket=self.bucket, Key=self.path(filename))
        headers = res['ResponseMetadata']['HTTPHeaders']
        return int(headers.get('content-length', 0))

    def delete(self, filename: str):
        if not self.exists(filename):
            return

        res = self.client.delete_objects(Bucket=self.bucket, Key=self.path(filename))
        if res['ResponseMetadata']['HTTPStatusCode'] != 204:
            raise Exception(f'delete {filename} failure')

    def open(self, filename: str):
        if not self.exists(filename):
            return None

        res = self.client.get_object(Bucket=self.bucket, Key=self.path(filename))
        content = BytesIO()
        content.write(res['Body'].read())
        content.seek(0)
        return content

    def save(self, filename: str, content: BytesIO, overwrite=False, **kwargs):
        if self.exists(filename) and not overwrite:
            raise Exception(f'{filename} exists')

        extras = {
            'CacheControl': 'max-age={60*60*24*30}',  # 30 days
        }

        headers = kwargs.get('headers')
        if headers:
            for key, value in headers.items():
                words = key.split('-')
                name = ''.join([word.capitalize() for word in words])
                extras[name] = value

        path = self.path(filename)
        content.seek(0)
        res = self.client.put_object(
            Bucket=self.bucket,
            Body=content,
            Key=path,
            ACL=self.config['s3']['acl'],
            **extras,
        )

        logger.info(f"aws : {res['ResponseMetadata']['RequestId']} - {res['ResponseMetadata']['HTTPStatusCode']}")
        if res['ResponseMetadata']['HTTPStatusCode'] != requests.codes.ok:
            raise Exception('aws save failure')
