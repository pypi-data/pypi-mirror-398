from functools import partial
from typing import List, Union, Optional, TYPE_CHECKING

from deepfos.lib.asynchronous import future_property
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.options import OPTION
from deepfos.api.role_strategy import RoleStrategyAPI
from deepfos.api.models.role_strategy import (
    QueryRoleSchemeDTO, RoleSchemeInfoVO, UserDTO,
    UserGroupListDTO, RoleDetailVO, RoleGroupDetailVO, ElementDetailVO
)
from deepfos.api.models.base import BaseModel
from deepfos.lib.utils import fetch_all_pages

__all__ = [
    'RoleStrategyRecord',
    'RoleStrategyInfo',
    'AsyncRoleStrategy',
    'RoleStrategy'
]


# -----------------------------------------------------------------------------
# utils
class RoleStrategyRecord(BaseModel):
    #: 用户
    users: Optional[List[Union[UserDTO, str]]] = None
    #: 用户组
    user_groups: Optional[List[Union[UserGroupListDTO, str]]] = None
    #: 角色
    roles: Optional[List[Union[RoleDetailVO, str]]] = None
    #: 角色组
    role_groups: Optional[List[Union[RoleGroupDetailVO, str]]] = None
    #: 维度表达式
    dim_expr: List[Optional[str]]


class RoleStrategyInfo(BaseModel):
    records: List[RoleStrategyRecord]
    dimensions: List[ElementDetailVO]


def _get_record_count(response: RoleSchemeInfoVO):
    return len(response.roleScheme['list'])


def ensure_list(maybe_list: Union[str, List[str]]):
    if isinstance(maybe_list, str):
        return [maybe_list]
    else:
        return maybe_list


class AsyncRoleStrategy(ElementBase[RoleStrategyAPI]):
    """权限方案"""
    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        self.current_user = OPTION.api.header['user']
        self.__meta = None
        super().__init__(element_name, folder_id, path, server_name)

    @future_property
    async def meta(self):
        """当前用户的权限方案元信息"""
        if self.__meta is None:
            await self.wait_for('async_api')
            self.__meta = await self._query(user=self.current_user)
        return self.__meta

    async def _query(
        self,
        user: Union[str, List[str]] = None,
        user_group: Union[str, List[str]] = None,
        role: Union[str, List[str]] = None,
        role_group: Union[str, List[str]] = None
    ) -> RoleStrategyInfo:
        """查询角色方案信息

        根据给定的筛选条件查询权限方案
        不同参数的查询条件间为 **或** 的关系。

        Args:
            user: 用户id
            user_group: 用户组id
            role: 角色
            role_group: 角色组

        .. admonition:: 示例

            .. code-block:: python

                rs = RoleStrategy("test")
                r = rs.query(user='1234-5678')
                # 维度列表
                r.dimensions
                # 权限方案记录列表
                r.records

        Note:
            - 当不提供任何参数时，会使用当前用户作为查询条件。
            - 如果要查询所有的权限方案，可以显式传入 ``user=[]``

        Returns:
            权限方案信息

        """
        if all(item is None for item in (user, user_group, role, role_group)):
            user = [self.current_user]
            query_current_user = True
        elif user is None:
            query_current_user = False
        else:
            user = ensure_list(user)
            query_current_user = (
                not any((user_group, role, role_group)) and
                len(user) == 1 and
                user[0] == self.current_user
            )

        user_group = ensure_list(user_group)
        role = ensure_list(role)
        role_group = ensure_list(role_group)

        if query_current_user and self.__meta is not None:
            return self.__meta

        fn = partial(
            self._query_impl,
            users=user,
            user_groups=user_group,
            roles=role,
            role_groups=role_group
        )

        pages = await fetch_all_pages(
            fn,
            count_getter=_get_record_count,
            page_size=200,
            page_no_key='page_no',
            page_size_key='page_size'
        )
        if not pages:
            dimensions = []
        else:
            dimensions = [seg.elementDetail for seg in pages[0].segments]

        rs_info = []

        for page in pages:
            for record in page.roleScheme['list']:
                rs_info.append(RoleStrategyRecord(
                    users=record['users'],
                    user_groups=record['userGroups'],
                    roles=record['roles'],
                    role_groups=record['roleGroups'],
                    dim_expr=[
                        record[f'segment{i}']
                        for i in range(1, len(dimensions) + 1)
                    ]
                ))

        r = RoleStrategyInfo(records=rs_info, dimensions=dimensions)
        return r

    query = _query

    async def _query_impl(
        self,
        page_size: int,
        page_no: int,
        users: List[str] = None,
        user_groups: List[str] = None,
        roles: List[str] = None,
        role_groups: List[str] = None
    ):
        payload = QueryRoleSchemeDTO(
            elementName=self.element_name,
            elementType=self.api_class.module_type,
            folderId=self.element_info.folderId,
            pageSize=page_size,
            pageNo=page_no,
            userIds=users or [],
            userGroupIds=user_groups or [],
            roleNames=roles or [],
            roleGroupNames=role_groups or [],
        )

        return await self.async_api.rolestrategy.info_list(payload)

    async def _query_records(self, user):
        if user is None or user == self.current_user:
            meta = self.meta
            records = meta.records
            return records
        else:
            res = await self.query(user=user)
            records = res.records
            return records

    async def query_roles(self, user: str = None) -> List[RoleDetailVO]:
        """查询用户所属的角色

        Args:
            user: 用户id，默认使用当前用户

        """
        records = await self._query_records(user)
        return sum((r.roles for r in records), [])

    async def query_role_groups(self, user: str = None) -> List[RoleGroupDetailVO]:
        """查询用户所属的角色组

        Args:
            user: 用户id，默认使用当前用户

        """
        records = await self._query_records(user)
        return sum((r.role_groups for r in records), [])


class RoleStrategy(AsyncRoleStrategy, metaclass=SyncMeta):
    synchronize = ('query', 'query_roles', 'query_role_groups')

    if TYPE_CHECKING:
        def query(
                self,
                user: Union[str, List[str]] = None,
                user_group: Union[str, List[str]] = None,
                role: Union[str, List[str]] = None,
                role_group: Union[str, List[str]] = None
        ) -> RoleStrategyInfo:  # pragma: no cover
            ...

        def query_roles(self, user: str = None) -> List[RoleGroupDetailVO]:  # pragma: no cover
            ...

        def query_role_groups(self, user: str = None) -> List[RoleGroupDetailVO]:  # pragma: no cover
            ...
