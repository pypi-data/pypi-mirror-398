from xml.etree import ElementTree

from loguru import logger

from deepfos import OPTION
from deepfos.lib.discovery import ServiceDiscovery
from deepfos.lib.httpcli import AioHttpCli
from deepfos.lib.utils import concat_url

__all__ = ['Eureka']


def http(ins):
    port = ins.find('port')
    enabled = port.get('enabled').lower() == "true"
    if enabled:
        ip = ins.find('ipAddr').text
        return f"http://{ip}:{port.text}"


def https(ins):
    port = ins.find('securePort')
    enabled = port.get('enabled').lower() == "true"
    if enabled:
        ip = ins.find('ipAddr').text
        return f"https://{ip}:{port.text}"


class EurekaCli(ServiceDiscovery):
    def __init__(self):
        super().__init__()
        self.versions_delta = ''  # 增量更新的versions_delta
        self.apps_hashcode = ''  # 增量更新的apps_hashcode
        self.setup()

    # noinspection PyAttributeOutsideInit
    def setup(self):
        from deepfos.lib.discovery import CACHE_STRATEGY, RankedCache
        base_url = CACHE_STRATEGY.get(
            OPTION.discovery.cache_strategy, RankedCache
        )()
        for url in OPTION.server.eureka.split(','):
            base_url.add(url)
        self.base_url = base_url

    async def on_interval(self):
        if self.server_cache:  # 有全量数据时-保持增量更新，否则-全量更新
            await self.get_delta_apps()
        else:
            await self._get_full_apps()

    async def on_startup(self):
        await self._get_full_apps()

    async def get_url(self, server_name: str, include_cb: bool = False):
        system_env = OPTION.general.task_info.get('system_env') or ''
        server_name = f"{system_env}{server_name}"
        return await super().get_url(server_name.upper(), include_cb)

    def sync_get_url(self, server_name: str, include_cb: bool = False):
        system_env = OPTION.general.task_info.get('system_env') or ''
        server_name = f"{system_env}{server_name}"
        return super().sync_get_url(server_name.upper(), include_cb)

    async def update_service_cache(self, server_name: str):
        await self.get_delta_apps()

    async def update_instance_cache(self, server_name: str):
        pass

    async def _get_xml(self, end_point: str):
        if not self.base_url:
            # Maybe all deleted by punish
            self.setup()

        url = self.base_url.pick_best()
        try:
            resp = await AioHttpCli.get(concat_url(url, end_point))
            raw_xml = await resp.text()
            xml = ElementTree.fromstring(raw_xml)
        except Exception:
            self.base_url.punish(url)
            raise
        else:
            self.base_url.reward(url)
        return xml

    async def _get_full_apps(self):
        """全量获取eureka服务列表，并更新到缓存中"""
        xml = await self._get_xml('apps')

        # 全量更新：确保拿到数据后，先清缓存
        if xml.find('apps__hashcode').text:
            self.server_cache.clear()
        server_memo = self.server_cache

        for app in xml.iter('application'):
            app_name = app.find('name').text.upper()
            for instance in app.iter('instance'):
                status = instance.find('status')
                if status.text.upper() != "UP":
                    continue

                addr = http(instance) or https(instance)

                if addr is not None:
                    server_memo[app_name].add(addr)  # 全量更新缓存

        logger.opt(lazy=True).debug("FULL-XML cache updated.")
        return server_memo

    async def get_delta_apps(self):
        """增量获取eureka服务列表，并更新到缓存中"""
        xml = await self._get_xml('apps/delta')

        server_memo = self.server_cache
        if (
            xml.find('versions__delta').text == self.versions_delta
            and xml.find('apps__hashcode').text == self.apps_hashcode
        ):
            # 如果versions__delta和apps__hashcode完全一样，则不必更新
            return server_memo

        # versions__delta和apps__hashcode赋值为最新
        self.versions_delta = xml.find('versions__delta').text
        self.apps_hashcode = xml.find('apps__hashcode').text

        for app in xml.iter('application'):
            app_name = app.find('name').text.upper()
            for instance in app.iter('instance'):
                addr = http(instance) or https(instance)
                if not addr:
                    continue
                # instance的操作类型：ADDED，MODIFIED，DELETED；instacce的状态：UP,...
                # 处理逻辑：只有操作类型在ADDED，MODIFIED中，并且状态是UP的才更新缓存，其他情况都删除
                if (
                    instance.find('actionType').text in ('ADDED', 'MODIFIED')
                    and instance.find('status').text.upper() == "UP"
                ):
                    # 增量更新缓存
                    server_memo[app_name].add(addr)
                else:
                    server_memo[app_name].delete(addr)

        # 增量更新后 - 计算此时全量 apps__hashcode与本次增量请求获取到的的apps__hashcode是否相等
        up_count = 0
        for server_obj in list(server_memo.values()):
            up_count += len(server_obj)
        now_apps_hashcode = f'UP_{up_count}_'
        if now_apps_hashcode != self.apps_hashcode:  # 如果不相等，做全量更新
            self.server_cache = await self._get_full_apps()
        logger.opt(lazy=True).debug("DELTA-XML cache updated.")
        return server_memo


Eureka = EurekaCli()
