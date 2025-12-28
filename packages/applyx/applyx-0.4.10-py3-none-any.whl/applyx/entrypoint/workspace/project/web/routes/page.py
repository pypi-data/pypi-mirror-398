# coding=utf-8

import requests

from fastapi import APIRouter, Request


router = APIRouter(
    tags=['default'],
    responses={
        404: dict(description='Not found'),
    },
)


@router.get('/')
async def default(request: Request):
    return 'hello world'


@router.get('/ping')
async def ping_pong(request: Request):
    agent = request.headers.get('user-agent', '')
    url = 'https://ipconfig.com/api/ip-query'
    params = {
        'ip': request.state.real_ip,
        'lang': 'zh',
    }
    headers = {
        'origin': 'https://ipconfig.com',
        'user-agent': agent,
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != requests.codes.ok:
        return dict(ip=request.state.real_ip, error='Unable to fetch IP information.')

    result = response.json()
    return dict(agent=agent, **result['data'])
