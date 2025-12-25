import asyncio
from enum import Enum
from functools import partial
from typing import Dict, List, Union, Literal, TYPE_CHECKING

from deepfos import OPTION
from deepfos.api.models.system import (
    MessageTemplateListVOResp, MessageTemplateListQueryDto,
    MessageTemplateListVO, MessageTemplateParamResp,
    MessageTemplateParamListQueryDto
)
from deepfos.api.platform import PlatformAPI
from deepfos.api.system import SystemAPI
from deepfos.db.dbkits import SyncMeta
from deepfos.exceptions import MsgCenterError
from deepfos.lib.asynchronous import future_property
from deepfos.lib.decorator import cached_property
from deepfos.lib.utils import fetch_all_pages

__all__ = ['MsgCenter', 'AsyncMsgCenter']


class TemplateType(Enum):
    # 平台公告
    plat = 1
    # 站内消息
    station = 2
    # 短信
    sms = 3
    # 邮箱
    email = 4


def _tpl_list_count(resp: Union[MessageTemplateListVOResp, MessageTemplateParamResp]):
    return len(resp.list)


class AsyncMsgCenter:
    """消息中心"""

    def __init__(self):
        self.__class__.templates.submit(self)
        self.system = SystemAPI(sync=False)
        self.platform = PlatformAPI(sync=False)

    @cached_property
    def type_api_map(self):
        svc = self.system.msg_service
        return {
            TemplateType.plat: (svc.push_plat_notice, svc.push_plat_notice),
            TemplateType.station: (svc.push_station_message, svc.push_station_message),
            TemplateType.email: (svc.push_email_message, svc.send_email),
            TemplateType.sms: (svc.push_sms_message, svc.send_sms),
        }

    @future_property(on_demand=True)
    async def templates(self) -> Dict[str, MessageTemplateListVO]:
        """当前有效的空间消息模板"""

        def impl(api, num, size):
            return api(MessageTemplateListQueryDto(pageNum=num, pageSize=size))

        pages = await fetch_all_pages(
            partial(impl, api=self.system.msg_template.page),
            count_getter=_tpl_list_count,
            page_size=100,
            page_no_key='num',
            page_size_key='size'
        )
        return {vo.templateCode: vo for p in pages if p.list
                for vo in p.list if vo.status == 1}

    async def _params(self, template_id: int) -> List[Dict]:
        def impl(api, num, size):
            return api(MessageTemplateParamListQueryDto(
                pageNum=num, pageSize=size, templateId=template_id
            ))

        pages = await fetch_all_pages(
            partial(impl, api=self.system.msg_template.get_template_param),
            count_getter=_tpl_list_count,
            page_size=100,
            page_no_key='num',
            page_size_key='size'
        )
        return [
            {'name': vo.paramName, 'scope': vo.scope}
            for p in pages if p.list for vo in p.list
        ]

    async def _fit_param(self, tpl_id, scope: Literal[1, 2], param=None):
        if not param:
            param = {}

        valid = {p['name'] for p in (await self._params(tpl_id)) if p['scope'] == scope}
        scope_name = {1: '标题', 2: '内容'}
        if lacked := (valid - param.keys()):
            raise ValueError(f'{scope_name[scope]}参数: {lacked} 缺失')

        return [
            {'paramName': k, 'paramValue': str(param[k]), 'scope': scope}
            for k in valid
        ]

    async def _publish(
        self,
        template: MessageTemplateListVO,
        receivers: List,
        sender: str = None,
        title_param: Dict[str, str] = None,
        content_param: Dict[str, str] = None,
        attachments: Dict[str, Union[str, bytes]] = None,
        cc_email: List = None,
        api_idx: Literal[0, 1] = 0,
        success_rule: Literal['partial', 'all'] = 'all'
    ) -> List:
        payload = {
            'receiver': receivers,
            'sender': sender or OPTION.api.header.get('user'),
            'templateCode': template.templateCode,
            'params': [
                *(await self._fit_param(template.id, 1, title_param)),
                *(await self._fit_param(template.id, 2, content_param)),
            ]
        }
        tpl_type = TemplateType(template.type)
        if cc_email:
            payload['ccEmail'] = cc_email

        if tpl_type in [TemplateType.email, TemplateType.station] and attachments:
            async def _gen_attach(name, file):
                return {
                    'id': (await self.platform.file.upload('DL', name, file)).id,
                    'space': OPTION.api.header.get('space')
                }

            payload['attachment'] = await asyncio.gather(*[
                _gen_attach(name, file) for name, file in attachments.items()
            ])

        api = self.type_api_map[tpl_type][api_idx]
        resp = await api(payload)
        if resp.failure and (
            success_rule == 'all' or (
                success_rule == 'partial' and not resp.success
            )
        ):
            raise MsgCenterError(*resp.failure)
        
        return resp.success

    async def publish(
        self,
        template_code: str,
        receiver_users: List[str] = None,
        receiver_groups: List[str] = None,
        sender: str = None,
        title_param: Dict[str, str] = None,
        content_param: Dict[str, str] = None,
        attachments: Dict[str, Union[str, bytes]] = None,
        success_rule: Literal['partial', 'all'] = 'all',
        cc_users: List[str] = None,
        cc_groups: List[str] = None,
    ) -> List:
        """推送指定消息模版的消息

        Args:
            template_code: 模板编码
            sender: 可选，发送人userid，默认为当前用户id
            receiver_users: 可选，收件人userid列表
            receiver_groups: 可选，收件人groupid列表
            title_param: 可选，标题变量
            content_param: 可选，内容变量
            attachments: 可选，站内消息或邮箱的消息附件，以 文件名: 文件(字符串/bytes) 的字典形式提供
            success_rule: 可选，发送成功规则，'partial' 表示部分成功即可，'all' 表示所有收件人都必须成功
            cc_users: 可选，抄送人userid列表
            cc_groups: 可选，抄送人groupid列表

        .. admonition:: 示例

            .. code-block:: python

                from deepfos.lib.msg import MsgCenter
                msg = MsgCenter()

            #. 推送带附件的站内消息

                .. code-block:: python

                    # demo_station标题如下:
                    # 标题【{var1}】
                    # 内容如下:
                    # 内容【{var1}】
                    #
                    # 发送至1个用户和1个用户组, 并附上2个文件附件

                    msg.publish(
                        'demo_station',
                        receiver_users=['00000000-0000-0000-0000-000000000000'],
                        receiver_groups=['00000000-0000-0000-0000-000000000001'],
                        title_param={'var1': 'a'},
                        content_param={'var1': 'b'},
                        attachments={
                            'file1.txt': 'Some text...',
                            'file2.txt': 'More text...',
                        }
                    )

        See Also:

            :meth:`send_mail`
            :meth:`send_sms`

        """
        template = self.templates.get(template_code)
        if not template:
            raise ValueError('模板编码对应的模板不存在或未启用')

        receivers = []
        if receiver_users:
            receivers.extend([{'id': r, 'type': 'USER'} for r in receiver_users])
        if receiver_groups:
            receivers.extend([{'id': r, 'type': 'GROUP'} for r in receiver_groups])
        cc_email = []
        if cc_users:
            cc_email.extend([{'id': r, 'type': 'USER'} for r in cc_users])
        if cc_groups:
            cc_email.extend([{'id': r, 'type': 'GROUP'} for r in cc_groups])

        if not receivers:
            raise ValueError('需提供receiver_users和receiver_groups中的至少一项')

        return await self._publish(
            template, sender=sender, receivers=receivers,
            title_param=title_param, content_param=content_param,
            attachments=attachments, success_rule=success_rule,
            cc_email=cc_email
        )

    async def send_mail(
        self,
        template_code: str,
        receivers: List[str],
        sender: str = None,
        title_param: Dict[str, str] = None,
        content_param: Dict[str, str] = None,
        attachments: Dict[str, Union[str, bytes]] = None,
        cc_email: List[str] = None,
        success_rule: Literal['partial', 'all'] = 'all'
    ) -> List:
        """发送指定消息模版的邮件

        Args:
            template_code: 模板编码
            receivers: 收件人邮箱列表
            sender: 可选，发送人userid，默认为当前用户id
            title_param: 可选，标题变量
            content_param: 可选，内容变量
            attachments: 可选，附件，以 文件名: 文件(字符串/bytes) 的字典形式提供
            cc_email: 可选，抄送人列表
            success_rule: 可选，发送成功规则，'partial' 表示部分成功即可，'all' 表示所有收件人都必须成功


        .. admonition:: 示例

            .. code-block:: python

                from deepfos.lib.msg import MsgCenter
                msg = MsgCenter()

            #. 发送邮件

                .. code-block:: python

                    # demo_mail标题如下:
                    # 邮件标题【{var2}】
                    # 内容如下:
                    # 邮件内容【{var2}】
                    #
                    # 发送至一个邮箱并抄送另一个邮箱, 并附上2个文件附件

                    msg.send_mail(
                        'demo_mail',
                        receivers=['xxx@a.com'],
                        cc_email=['yyy@b.com'],
                        title_param={'var2': '42'},
                        content_param={'var2': '24'},
                        attachments={
                            'file1.txt': 'Some text...',
                            'file2.txt': 'More text...',
                        }
                    )

        See Also:

            :meth:`publish`
            :meth:`send_sms`

        """
        template = self.templates.get(template_code)
        if not template:
            raise ValueError('模板编码对应的模板不存在或未启用')

        if (tpl_type := TemplateType(template.type)) is not TemplateType.email:
            raise ValueError(f'模板类型[{tpl_type}]非邮箱类型')

        return await self._publish(
            template, sender=sender, receivers=receivers,
            title_param=title_param, content_param=content_param,
            attachments=attachments, cc_email=cc_email,
            api_idx=1, success_rule=success_rule,
        )

    async def send_sms(
        self,
        template_code: str,
        receivers: List[str],
        sender: str = None,
        title_param: Dict[str, str] = None,
        content_param: Dict[str, str] = None,
        success_rule: Literal['partial', 'all'] = 'all'
    ) -> List:
        """发送指定消息模版的短信

        Args:
            template_code: 模板编码
            receivers: 收件人手机号列表
            sender: 可选，发送人userid，默认为当前用户id
            title_param: 可选，标题变量
            content_param: 可选，内容变量
            success_rule: 可选，发送成功规则，'partial' 表示部分成功即可，'all' 表示所有收件人都必须成功


        .. admonition:: 示例

            .. code-block:: python

                from deepfos.lib.msg import MsgCenter
                msg = MsgCenter()

            #. 发送短信

                .. code-block:: python

                    # demo_sms标题如下:
                    # 短信标题【{var3}】
                    # 内容如下:
                    # 短信内容【{var3}】
                    #
                    # 发送至2个手机号

                    msg.send_mail(
                        'demo_sms',
                        receivers=['15000000000', '13000000000'],
                        title_param={'var3': 'Hello'},
                        content_param={'var3': 'World'}
                    )

        See Also:

            :meth:`publish`
            :meth:`send_mail`

        """
        template = self.templates.get(template_code)
        if not template:
            raise ValueError('模板编码对应的模板不存在或未启用')

        if (tpl_type := TemplateType(template.type)) is not TemplateType.sms:
            raise ValueError(f'模板类型[{tpl_type}]非短信类型')

        return await self._publish(
            template, sender=sender, receivers=receivers,
            title_param=title_param, content_param=content_param,
            api_idx=1, success_rule=success_rule,
        )


class MsgCenter(AsyncMsgCenter, metaclass=SyncMeta):
    synchronize = ('publish', 'send_mail', 'send_sms',)

    if TYPE_CHECKING:  # pragma: no cover
        def publish(
            self,
            template_code: str,
            receiver_users: List[str] = None,
            receiver_groups: List[str] = None,
            sender: str = None,
            title_param: Dict[str, str] = None,
            content_param: Dict[str, str] = None,
            attachments: Dict[str, Union[str, bytes]] = None,
            success_rule: Literal['partial', 'all'] = 'all',
            cc_users: List[str] = None,
            cc_groups: List[str] = None,
        ) -> List:
            ...

        def send_mail(
            self,
            template_code: str,
            receivers: List[str],
            sender: str = None,
            title_param: Dict[str, str] = None,
            content_param: Dict[str, str] = None,
            attachments: Dict[str, Union[str, bytes]] = None,
            cc_email: List[str] = None,
            success_rule: Literal['partial', 'all'] = 'all'
        ) -> List:
            ...

        def send_sms(
            self,
            template_code: str,
            receivers: List[str],
            sender: str = None,
            title_param: Dict[str, str] = None,
            content_param: Dict[str, str] = None,
            success_rule: Literal['partial', 'all'] = 'all'
        ) -> List:
            ...
