# coding=utf-8

import gridfs
from pymongo import MongoClient

from applyx.conf import settings


class GridFS(gridfs.GridFS):
    """
    source = open('README.md', mode='rb')
    grid_fs = GridFS('write')
    file_id = grid_fs.put(
                source,
                filename='README.md',
                content_type='text/plain',
                metadata={'author': 'AUTHOR'})
    source.close()

    grid_fs = GridFS('read')
    grid_out = grid_fs.get(file_id)
    content = grid_out.read().decode('utf8')
    grid_out.close()
    """

    def __init__(self, alias: str, **kwargs):
        config = settings.get('gridfs')
        if config is None:
            raise Exception('missing settings for gridfs')

        uri = 'mongodb://{host}:{port}/{name}'.format(**config[alias])
        if config[alias].get('username') and config[alias].get('password'):
            uri = 'mongodb://{username}:{password}@{host}:{port}/{name}'.format(**config[alias])

        self.client = MongoClient(uri)
        database = getattr(self.client, config[alias]['name'])
        collection_name = kwargs.pop('collection', 'fs')
        super().__init__(database, collection_name, **kwargs)

    def close(self):
        self.client.close()


class GridFSBucket(gridfs.GridFSBucket):
    """
    source = open('README.md', mode='rb')
    grid_fs_bucket = GridFSBucket('write')
    file_id = grid_fs_bucket.upload_from_stream(
                filename='README.md',
                source=source,
                metadata={'author': 'AUTHOR'})
    source.close()

    destination = open('README.md.out', mode='wb')
    grid_fs_bucket = GridFSBucket('read')
    grid_fs_bucket.download_to_stream(file_id, destination)
    destination.close()
    """

    def __init__(self, alias: str, **kwargs):
        config = settings.get('gridfs')
        if config is None:
            raise Exception('missing settings for gridfs')

        uri = 'mongodb://{host}:{port}/{name}'.format(**config[alias])
        if config[alias].get('username') and config[alias].get('password'):
            uri = 'mongodb://{username}:{password}@{host}:{port}/{name}'.format(**config[alias])

        self.client = MongoClient(uri)
        database = getattr(self.client, config[alias]['name'])
        bucket_name = kwargs.pop('bucket_name', 'fs')
        super().__init__(database, bucket_name, **kwargs)

    def close(self):
        self.client.close()
