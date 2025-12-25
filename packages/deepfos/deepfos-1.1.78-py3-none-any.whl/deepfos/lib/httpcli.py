"""HTTP客户端"""

import atexit
import threading
import asyncio
import aiohttp
import requests
from .utils import auto_setup
from .asynchronous import register_on_loop_shutdown
from deepfos.options import OPTION


class AioHttpCli:
    session = {}

    @classmethod
    async def get_session(cls):
        tid = threading.get_ident()
        if (
            (session := cls.session.get(tid)) is None
            or session.closed
            or session._loop.is_closed()  # noqa
        ):
            cls.session[tid] = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
            register_on_loop_shutdown(cls.close_current)
        return cls.session[tid]

    @classmethod
    async def get(cls, url, *, allow_redirects=True, **kwargs):
        session = await cls.get_session()
        return await session.get(
            url,
            allow_redirects=allow_redirects,
            verify_ssl=OPTION.api.verify_ssl,
            timeout=OPTION.api.timeout,
            **kwargs
        )

    @classmethod
    async def post(cls, url, *, data=None, **kwargs):
        session = await cls.get_session()
        return await session.post(
            url,
            data=data,
            verify_ssl=OPTION.api.verify_ssl,
            timeout=OPTION.api.timeout,
            **kwargs
        )

    @classmethod
    async def close(cls):
        for session in cls.session.values():
            await session.close()
            await asyncio.sleep(0)
            del session
        cls.session = {}

    @classmethod
    async def close_current(cls):
        tid = threading.get_ident()
        session = cls.session.pop(tid, None)
        if session is not None:
            await session.close()
            await asyncio.sleep(0)
            del session


class SyncHttpCli:
    """同步HTTP客户端"""
    session: requests.Session = None

    @classmethod
    def setup(cls):
        if cls.session is None:
            session = requests.Session()
            cls.session = session

    @classmethod
    @auto_setup
    def post(cls, url, headers=None, **kwargs):
        return cls.session.post(
            url,
            headers=headers,
            timeout=(4, 180),
            verify=OPTION.api.verify_ssl,
            **kwargs
        )

    @classmethod
    @auto_setup
    def get(cls, url, params=None, headers=None):
        return cls.session.get(
            url,
            params=params,
            headers=headers,
            timeout=(4, 180),
            verify=OPTION.api.verify_ssl,
        )


def _close_session(): # pragma: no cover
    if SyncHttpCli.session is not None:
        SyncHttpCli.session.close()


atexit.register(_close_session)
