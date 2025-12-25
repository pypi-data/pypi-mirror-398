# coding=utf-8

import re
import json

import shortuuid
from loguru import logger
from bson import ObjectId
from addict import Dict
from itsdangerous import TimestampSigner
from starlette.requests import HTTPConnection
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import UploadFile
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from fastapi import status


class RequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app, dispatch=None)
        self.uuid = shortuuid.ShortUUID(alphabet='0123456789ABCDEF')

    async def dispatch(self, request, call_next):
        request.state.is_mobile = self.is_mobile(request)
        request.state.is_weixin = self.is_weixin(request)
        request.state.real_ip = self.get_real_ip(request)
        request.state.id = self.uuid.random(length=4)

        with logger.contextualize(mdc=request.state.id):
            await self.hook_before_request(request)
            response = await call_next(request)
            await self.hook_after_request(request, response)

        response.headers['X-Request-Id'] = request.state.id
        return response

    async def parse_post(self, request: Request):
        if 'Content-Type' not in request.headers:
            return

        if request.headers['Content-Type'].startswith('application/json'):
            data = await request.json()
            request.state.post = data
            logger.info(f'[data] {data}')
        elif request.headers['Content-Type'].startswith('application/x-www-form-urlencoded'):
            form = await request.form()
            request.state.post = form
            logger.info(f'[form] {dict(form)}')
        elif request.headers['Content-Type'].startswith('multipart/form-data'):
            form = await request.form()
            request.state.post = form

            data = {}
            for key in form.keys():
                # value = form.getlist(key)
                value = form.get(key)
                if isinstance(value, UploadFile):
                    data[key] = f'{value.filename};{value.content_type}'
                else:
                    data[key] = value

            if data:
                logger.info(f'[form] {data}')

    async def hook_before_request(self, request: Request):
        if request.url.path.startswith('/static'):
            return

        logger.info(f'[uri] {request.method} {request.url.path}')

        if request.url.query:
            logger.info(f'[query] {request.url.query}')

        logger.debug(f'[headers] {dict(request.headers)}')

    async def hook_after_request(self, request: Request, response: Response):
        if request.url.path.startswith('/static'):
            if request.url.path.endswith('.ejs'):
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response

        endpoint = request.scope.get('endpoint')
        if endpoint:
            logger.info(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

        agent = request.headers.get('user-agent', '')
        if agent:
            logger.info(f'[user-agent] {agent}')

        ip = request.state.real_ip
        if ip:
            logger.info(f'[ip] {ip}')

        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(f'[http] {response.status_code}')
        elif status.HTTP_300_MULTIPLE_CHOICES <= response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.warning(f'[http] {response.status_code}')
        else:
            logger.info(f'[http] {response.status_code}')

    def is_mobile(self, request: Request):
        agent = request.headers.get('User-Agent')
        if not agent:
            return False
        features = [
            'android',
            'iphone',
            'ipad',
            'ipod',
            'windows phone',
            'symbian',
            'blackberry',
        ]
        matcher = re.search('|'.join(features), agent, re.I)
        return matcher is not None

    def is_weixin(self, request: Request):
        agent = request.headers.get('User-Agent')
        if not agent:
            return False
        matcher = re.search('micromessenger', agent, re.I)
        return matcher is not None

    def get_real_ip(self, request: Request):
        forwarded_for_ips = [item.strip() for item in request.headers.get('x-forwarded-for', '').split(',')]
        real_ip = request.headers.get('x-real-ip', '')
        client_ip = request.client.host or ''
        if forwarded_for_ips:
            return forwarded_for_ips[0]
        return real_ip or client_ip


class RedisSessionMiddleware:
    def __init__(self, app: ASGIApp, config: Dict):
        self.app = app
        self.config = config
        self.signer = TimestampSigner(config.secret_key)

        from applyx.redis import RedisManager

        redis_mgr = RedisManager.instance()
        redis_mgr.init_redis(config.redis_alias)
        self.redis = redis_mgr.get(config.redis_alias)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] not in ('http', 'websocket'):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        is_empty_session = True

        scope['session'] = {}
        if self.config.cookie.name in connection.cookies:
            session_id = connection.cookies[self.config.cookie.name]
            redis_key = f'{self.config.key_prefix}:{session_id}'
            scope['session'] = json.loads(self.redis.get(redis_key))
            scope['session_id'] = session_id
            is_empty_session = False

        async def send_wrapper(message: Message, **kwargs) -> None:
            if message['type'] == 'http.response.start':
                session_id = scope.pop('session_id', str(ObjectId()))
                redis_key = f'{self.config.key_prefix}:{session_id}'

                if scope['session']:
                    self.redis.set(redis_key, json.dumps(scope['session']))
                    self.redis.expire(redis_key, self.config.cookie.maxage)
                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(session_id=session_id, clear=False)
                    headers.append('Set-Cookie', header_value)

                elif not is_empty_session:
                    self.redis.delete(redis_key)
                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(clear=True)
                    headers.append('Set-Cookie', header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _construct_cookie(self, session_id: str, clear=False):
        cookie_expire = 'Thu, 01 Jan 1970 00:00:00 GMT'
        cookie_max_age = 0 if clear else self.config.cookie.maxage

        cookie = f'{self.config.cookie.name}={session_id};'
        cookie += ' Path=/;'
        cookie += f' Max-Age={cookie_max_age};'
        if clear:
            cookie += f' Expires={cookie_expire};'

        if self.config.cookie.httponly:
            cookie += ' httponly;'
        if self.config.cookie.secure:
            cookie += ' secure;'
        if self.config.cookie.samesite:
            cookie += f' samesite={self.config.cookie.samesite};'
        if self.config.cookie.domain:
            cookie += f' Domain={self.config.cookie.domain};'

        return cookie
