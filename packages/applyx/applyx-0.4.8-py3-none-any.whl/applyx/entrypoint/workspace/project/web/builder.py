# coding=utf-8

from loguru import logger

from applyx.web.builder import FastAPIBuilder


class Builder(FastAPIBuilder):
    async def on_startup(self):
        logger.info('Startup')

    async def on_shutdown(self):
        logger.info('Shutdown')
