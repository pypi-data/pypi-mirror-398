import asyncio
import functools
import json
from collections import defaultdict
from typing import TypedDict, Any, Tuple, Type, Dict

from loguru import logger

from deepfos import OPTION
from deepfos.exceptions import APIResponseError
from deepfos.lib.discovery import ServiceDiscovery
from deepfos.lib.httpcli import AioHttpCli
from deepfos.lib.utils import concat_url

__all__ = ['Nacos']


class InstanceHostInfo(TypedDict, total=False):
    instanceId: str
    ip: str
    port: int
    weight: float
    healthy: bool
    enabled: bool
    ephemeral: bool
    clusterName: str
    serviceName: str
    metadata: dict
    instanceHeartBeatInterval: int
    instanceIdGenerator: str
    instanceHeartBeatTimeOut: int
    ipDeleteTimeout: int


class ResponseChecker:  # pragma: no cover
    @classmethod
    def expect(cls, response: Any) -> bool:
        return True

    @classmethod
    def cast(cls, response: str, endpoint: str):
        return response

    @classmethod
    def validate(cls, response: str, endpoint: str) -> Tuple[bool, Any]:
        casted = cls.cast(response, endpoint)
        return cls.expect(casted), casted


class JsonResponse(ResponseChecker):  # pragma: no cover
    @classmethod
    def cast(cls, response: str, endpoint: str):
        try:
            return json.loads(response)
        except (TypeError, ValueError):
            logger.opt(lazy=True).exception(
                f'Call api: {endpoint} failed. '
                f'Response << {response} >> cannot be decoded as json.'
            )
            raise APIResponseError(
                f'Call api: {endpoint} failed. '
                f'Response << {response} >> cannot be decoded as json.'
            )


class Route:  # pragma: no cover
    def __init__(self, method: str):
        self.method = method

    def __call__(
        self,
        endpoint,
        response_checker: Type[ResponseChecker] = None,
    ):
        def execute(func):
            request = getattr(AioHttpCli, self.method)
            method = self.method.upper()
            is_get = method == 'GET'

            @functools.wraps(func)
            async def call(*args, **kwargs):
                ins = args[0]
                url = concat_url(ins.base_url, endpoint)
                body = func(ins, *args[1::], **kwargs)
                logger.opt(lazy=True).debug(
                    f"Sending request: {method} {url} "
                    f"body: {repr(body)}"
                )
                req_args = {
                    'headers': ins.header,
                    'params' if is_get else 'data': body
                }
                response = await request(url, **req_args)
                text = await response.text()
                if response_checker is not None:
                    ok, result = response_checker.validate(text, endpoint)
                    if not ok:
                        raise APIResponseError(
                            f"Call API: {endpoint} failed. "
                            f"Bad response because status is False. Detail: {text}."
                        )
                    else:
                        return result
                else:
                    return text

            return call

        return execute


get = Route(method='get')


class NacosAPI:
    def __init__(self):  # noqa
        nacos_server: str = OPTION.nacos.server.lower()
        if nacos_server.rstrip('/').endswith('nacos'):
            base_url = nacos_server
        else:
            base_url = concat_url(nacos_server, 'nacos')

        self.base_url = concat_url(base_url, 'v1')
        self.header = {"Content-Type": "application/x-www-form-urlencoded"}

    @get('ns/service/list', JsonResponse)
    def list_service(self):  # pragma: no cover
        return {
            'pageNo': 1,
            'pageSize': 1000000,
        }

    @get('ns/instance/list', JsonResponse)
    def list_instance(
        self,
        service_name: str,
        group: str = 'DEFAULT_GROUP',
        namespace: str = 'public',
        cluster: str = 'DEFAULT',
    ):  # pragma: no cover
        return {
            'serviceName': service_name,
            'groupName': group,
            'namespaceId': namespace,
            'clusters': cluster,
        }


class NacosCli(ServiceDiscovery):
    def __init__(self):
        super().__init__()
        self._instance_lock: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._server_lock = asyncio.Lock()
        self._api = NacosAPI()
        self._cares = set()
        self._group = OPTION.nacos.group
        self._ns = OPTION.nacos.namespace
        self._cluster = OPTION.nacos.cluster

    async def on_close(self):
        self._cares.clear()
        self.server_cache.clear()
        self._instance_lock.clear()

    async def on_startup(self):
        pass

    async def on_interval(self):
        await self._update_cache()

    async def _update_cache(self):
        logger.opt(lazy=True).debug(f"Update cache for instance: {self._cares}")

        await asyncio.gather(*(
            self.update_instance_for_service(sn)
            for sn in self._cares
        ))

    async def update_service_cache(self, server_name: str):
        async with self._server_lock:
            if server_name not in self.server_cache:
                await self.update_services()

    async def update_instance_cache(self, server_name):
        self._cares.add(server_name)
        await self.update_instance_for_service(server_name)

    async def update_services(self):
        new_services = frozenset((await self._api.list_service())['doms'])
        cur_services = frozenset(self.server_cache.keys())

        if added := new_services - cur_services:
            for srv in added:
                self.server_cache.__getitem__(srv)
            logger.opt(lazy=True).debug(f"Added services: {added}")

        if removed := cur_services - new_services:
            for srv in removed:
                self.server_cache.pop(srv)
                self._instance_lock.pop(srv, None)  # noqa
            logger.opt(lazy=True).debug(f"Removed services: {removed}")

    async def update_instance_for_service(self, server_name: str):
        async with self._instance_lock[server_name]:
            instance_info = await self._api.list_instance(
                server_name,
                group=self._group,
                namespace=self._ns,
                cluster=self._cluster
            )

        host: InstanceHostInfo
        cache = self.server_cache[server_name]

        for host in instance_info['hosts']:
            if not host['enabled']:
                continue

            addr = f"http://{host['ip']}:{host['port']}"
            cache.add(addr)
            if not host['healthy']:
                cache.punish(addr)


Nacos = NacosCli()
