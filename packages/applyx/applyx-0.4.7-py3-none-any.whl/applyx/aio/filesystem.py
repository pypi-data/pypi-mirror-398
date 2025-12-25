# coding=utf-8

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from applyx.conf import settings


class GridFSBucket(AsyncIOMotorGridFSBucket):

    """
    import aiofiles
    source = aiofiles.open('README.md', mode='rb')
    grid_fs_bucket = GridFSBucket('write')
    file_id = await grid_fs_bucket.upload_from_stream(
                filename='README.md',
                source=source,
                metadata={'author': 'AUTHOR'})
    await source.close()

    destination = aiofiles.open('README.md.out', mode='wb')
    grid_fs_bucket = GridFSBucket('read')
    await grid_fs_bucket.download_to_stream(file_id, destination)
    await destination.close()
    """

    def __init__(self, alias: str, **kwargs):
        config = settings.get('gridfs')
        if config is None:
            raise Exception('missing settings for gridfs')

        uri = 'mongodb://{host}:{port}/{name}'.format(**config[alias])
        if config[alias].get('username') and config[alias].get('password'):
            uri = 'mongodb://{username}:{password}@{host}:{port}/{name}'.format(
                **config[alias]
            )

        self.client = AsyncIOMotorClient(uri)
        database = getattr(self.client, config[alias]['name'])
        collection_name = kwargs.pop('collection', 'fs')
        super().__init__(database, collection_name, **kwargs)

    async def close(self):
        await self.client.close()
