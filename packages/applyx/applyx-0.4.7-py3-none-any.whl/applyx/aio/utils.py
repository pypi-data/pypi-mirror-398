# coding=utf-8

import asyncio


async def check_connection(host: str, port: int):
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(asyncio.Protocol, host, port)

    try:
        await asyncio.wait_for(coro, timeout=1)
    except asyncio.TimeoutError:
        return False
    except ConnectionRefusedError:
        return False
    else:
        return True
