# coding=utf-8

from fastapi import APIRouter, Request

from applyx.utils import get_store_dir


STORE_DIR = get_store_dir()

router = APIRouter(
    prefix='/api',
    tags=['demo'],
    responses={
        404: dict(description='Not found'),
    },
)


@router.get('/demo/get')
async def get_handler(request: Request):
    return dict(err=0, msg='success', data={'hello': 'world'})


@router.post('/demo/post')
async def post_handler(request: Request):
    return dict(err=0, msg='success', data={'hello': 'world'})
