from deepfos.lib.asynchronous import future_property
from typing import List, Dict, Union, TYPE_CHECKING

from deepfos.element.base import ElementBase, SyncMeta
from deepfos.api.accounting_engines import AccountingEnginesAPI, BillEnginesAPI, AccountingEventTypeAPI
from deepfos.lib.utils import CIEnum
from deepfos.api.models.accounting_engines import (
    AccountingControlRequestDTO,
    AccountingEnginesDTO,
    AccountingEnginesRequestDTO,
    DataDTO,
    AccountingEnginesExecCallbackPythonDTO as CallbackInfo,
    AccEventTypeTableDTO,
    AccEventTypeElementDTO,
)

__all__ = [
    "AccountingEngines",
    "AsyncAccountingEngines",
    "BillEngines",
    "AsyncBillEngines",
    "CallbackInfo"
]

DEFAULT_CALLBACK_PARAMS = {"controlTableInfo", "success", "batchNumber"}
DEFAULT_CALLBACK_SERVERNAME = "python-server2-0"


class Status(CIEnum):
    failure = "failure"
    success = "success"
    delete = "delete"

    @classmethod
    def mapping(cls, status: Union["Status", str]) -> str:
        status = cls[status]
        if status is cls.failure:
            return "0"
        elif status is cls.success:
            return "1"
        else:
            return "2"


class AsyncAccountingEngines(ElementBase[AccountingEnginesAPI]):
    """会计引擎"""
    @future_property
    async def meta(self) -> AccountingEnginesDTO:
        """会计引擎的元数据信息"""
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        return await api.engines.get_accounting_info_by_name_type(
            elementType=element_info.elementType,
            elementName=self.element_name,
            folderId=element_info.folderId,
        )

    async def execute(
        self,
        filter_scope: Dict[str, str] = None,
        callback: Union[Dict, CallbackInfo] = None,
        sync: bool = False,
    ) -> Union[DataDTO, None]:
        """
        执行会计/单据引擎

        Args:
            filter_scope: 执行参数，键值对分别表示执行时源数据的数据选择字段和对应范围
            callback: 回调脚本配置信息，若为None，则引擎在结束后不会调用脚本，如果配置了回调，
                则不论引擎是否执行成功，都将在结束后调用回调脚本
            sync: 调用执行接口的类型，同步（True）/异步（False），默认为异步，异步执行接口会
                在收到执行请求时立刻响应，同步执行接口会等执行完成后才响应，并返回执行信息，如果
                设置为同步，当数据量过大导致引擎执行时间过长时，可能因超出SDK的接口响应超时时间而报错

        Returns:
            调用同步接口时返回执行信息（批次号和执行成功条数），调用异步接口时则返回None

        .. admonition:: 示例

            1.以自定义数据选取参数执行

            .. code-block:: python

                engines = AccountingEngines('engines_example')
                # engines = BillEngines('engines_example')
                engines.execute(filter_scope={"year": "2022", "period": "10"})

            2.以默认参数执行

            .. code-block:: python

                engines.execute()

            3.执行并在结束后调用回调脚本

            .. code-block:: python

                callback = CallbackInfo(
                    path="/Python",
                    elementName="test_callback",
                    serverName="python-server2-0",
                    callbackParams={"key1":"value1", "key2":"value2"},
                )
                # callback = {
                #     "path": "/Python",
                #     "elementName": "test_callback",
                #     "serverName": "python-server2-0",
                #     "callbackParams": {"key1":"value1", "key2":"value2"},
                # }
                engines.execute(callback=callback)


        Hint:
            - ``filter_scope`` 参数中传入的键，若为会计引擎全局配置中已配置的字段，则在
              执行时其值会覆盖配置字段的默认值，否则，该键值对会被忽略。
            - ``filter_scope`` 参数中不存在而会计引擎全局配置中已配置的字段，在执行时会
              取配置字段的默认值。
            - ``filter_scope`` 参数可以不传，此时数据选择范围为会计引擎中配置的默认值。

        Attention:
            ``callback`` 可接受字典和CallbackInfo类两种参数，以CallbackInfo类为例，
              其在初始化时支持6个配置参数，如下表所示

            +----------------+----------------+------------------------------------------------------------------------+
            | 参数           | 类型           | 说明                                                                   |
            +================+================+========================================================================+
            | path           | Optional[str]  | 调用元素所在路径，与folderId二选一                                     |
            +----------------+----------------+------------------------------------------------------------------------+
            | folderId       | Optional[str]  | 调用元素所在文件夹ID，与path二选一                                     |
            +----------------+----------------+------------------------------------------------------------------------+
            | elementName    | str            | 调用元素的元素名                                                       |
            +----------------+----------------+------------------------------------------------------------------------+
            | elementType    | Optional[str]  | 元素类型，默认None时指代PY，目前仅支持PY                               |
            +----------------+----------------+------------------------------------------------------------------------+
            | serverName     | Optional[str]  | 元素服务名，默认None时指代python-server2-0，目前仅支持python-server2-0 |
            +----------------+----------------+------------------------------------------------------------------------+
            | callbackParams | Optional[Dict] | 传给回调脚本的额外参数                                                 |
            +----------------+----------------+------------------------------------------------------------------------+

            以示例3的回调参数为例，回调脚本接收到参数为

                .. code-block:: python

                    p2 = {
                        "controlTableInfo": { # 状态控制表信息
                            "id": "0a43f4f1-b7b4-4d32-8b6a-c89b58a9b75c",
                            "elementName": "accounting_control",
                            "elementType": "DAT_MYSQL",
                            "folderId": "DIRa020ede38a99",
                            "serverName": None,
                            "path": "\\test\\",
                            "absoluteTag": False,
                            "relativePath": None,
                            "remark": None,
                            "actualTableName": "tb001_accounting_control",
                        },
                        "success": True, # 引擎是否执行成功
                        "key1": "value1", # 自定义参数
                        "key2": "value2", # 自定义参数
                        "batchNumber": "127559e5-de2a-42c2-95d9-1c84e1a6483b_20221129173222", # 批次号
                    }

            自定义参数的名称不应当为controlTableInfo、success或batchNumber，以免和回调脚本传入的默认参数冲突

        """
        if callback:
            if isinstance(callback, Dict):
                callback = CallbackInfo(**callback)
            if not callback.serverName:
                callback.serverName = DEFAULT_CALLBACK_SERVERNAME
            if conflicts := DEFAULT_CALLBACK_PARAMS.intersection(callback.callbackParams or []):
                raise ValueError(
                    f"Name: {conflicts} are reserved thus cannot be used "
                    f"as callback parameter names."
                )
        request_body = AccountingEnginesRequestDTO(
            elementName=self.element_name,
            folderId=self.element_info.folderId,
            elementType=self.element_info.elementType,
            paramValueMap=filter_scope,
            callbackInfo=callback,
        )
        if sync:
            return await self.async_api.engines.exec_by_id(request_body)
        else:
            return await self.async_api.engines.sync_exec_by_id(request_body)

    async def update_status(self, key: List[str], status: Union[Status, str]) -> None:
        """修改执行状态

        Args:
            key: 目标模型主表的业务主键的值
            status: 执行状态，字符串类型

        .. admonition:: 示例

            .. code-block:: python

                engines.update_status(key=["A_2022_8_0046", "100001"], status='delete')

        Hint:
            - ``key`` 参数表示目标模型中需要修改执行状态的业务主键字段的值。
            - ``status`` 参数表示需要修改成的执行状态，一般业务场景下设置为delete，
              表示执行状态改为删除。

        Attention:
            - status执行状态可选参数如下：

            +---------+----------------------+
            | 参数    | 说明                 |
            +=========+======================+
            | failure | 修改执行状态为失败。 |
            +---------+----------------------+
            | success | 修改执行状态为成功。 |
            +---------+----------------------+
            | delete  | 修改执行状态为删除。 |
            +---------+----------------------+

            - 会计/单据引擎组件在内部会维护一张源对象和目标模型的主键映射表，并记录其执行状态。

            +------------+------------------+----------+
            | 源对象主键 | 目标模型主表主键 | 执行状态 |
            +============+==================+==========+
            | A_000001   | A_2022_8_0046    | success  |
            +------------+------------------+----------+
            | A_000002   | A_2022_8_0046    | success  |
            +------------+------------------+----------+
            | A_000003   | A_2022_8_0047    | delete   |
            +------------+------------------+----------+

            - 对于执行状态为成功的目标模型数据，其关联的源对象数据在再次执行会计/单据引擎时不
              会二次计算。因此，当目标模型中会计/单据引擎生成的数据被通过非会计/单据引擎组件提供的
              手段被删除时，必须主动将被删除数据的执行状态修改为delete（删除）。
            - 如果有其他业务场景，需要修改源对象和目标模型的主键映射表的执行状态为failure
              或success，也可以调用该接口。
        """

        return await self.async_api.engines.update_control_status(
            AccountingControlRequestDTO(
                elementName=self.element_name,
                folderId=self.element_info.folderId,
                elementType=self.element_info.elementType,
                status=Status.mapping(status),
                targetElementDataIdList=key,
            )
        )


class AccountingEngines(AsyncAccountingEngines, metaclass=SyncMeta):
    synchronize = (
        'execute',
        'update_status'
    )
    if TYPE_CHECKING:  # pragma: no cover
        def execute(
                self,
                filter_scope: Dict[str, str] = None,
                callback: Union[Dict, CallbackInfo] = None,
                sync: bool = False,
        ) -> Union[DataDTO, None]:
            ...

        def update_status(self, key: List[str], status: Union[Status, str]) -> None:
            ...


class AsyncBillEngines(AsyncAccountingEngines):
    """单据引擎"""

    api_class = BillEnginesAPI
    api: BillEnginesAPI


class BillEngines(AccountingEngines):
    """单据引擎"""

    api_class = BillEnginesAPI
    api: BillEnginesAPI


class AsyncAccountingEventType(ElementBase[AccountingEventTypeAPI]):
    """会计事件类型"""
    @future_property
    async def meta(self) -> AccEventTypeElementDTO:
        """会计事件类型元数据信息"""
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        return await api.engines.get_info_by_name(
            elementType=element_info.elementType,
            elementName=self.element_name,
            folderId=element_info.folderId
        )

    async def insert_to_event_table(self, object_id_list: List[str]) -> None:
        """业务主健插入会计事件表

        Args:
            object_id_list: 业务主键ID集合

         .. admonition:: 示例

            1.实例化会计事件类型

            .. code-block:: python

                from deepfos.element.accounting import AccountingEventType
                # 1. 根据元素编码 进行实例化
                eventType = AccountingEventType('zhy_0104_001')

                # 2. 根据元素编码和路径 进行实例化
                eventType = AccountingEventType(element_name='zhy_0104_001',path="/zhy_test/event")

                # 3. 根据元素编码和文件夹ID，进行实例化
                eventType = AccountingEventType(element_name='zhy_0104_001',folder_id='DIR1b7e6f8b5bc3')


            2.业务主健插入会计事件表

            .. code-block:: python

                # 1. 指定参数名 object_id_list，并传业务ID集合
                eventType.insert_to_event_table(object_id_list=["A00000002","A00000003"])

                # 2. 不指定参数名，直接传业务ID集合
                eventType.insert_to_event_table(["A00000004","A00000005"])

        Hint:
            - ``object_id_list`` 业务主键ID集合，
              表示将业务主键集合，插入到会计事件类型元素（zhy_0104_001）对应的事件表中。

        """

        return await self.async_api.engines.insert_to_event_table(
            AccEventTypeTableDTO(
                elementName=self.element_name,
                folderId=self.element_info.folderId,
                objectIdList=object_id_list
            )
        )


class AccountingEventType(AsyncAccountingEventType, metaclass=SyncMeta):
    synchronize = (
        'insert_to_event_table',
    )
    if TYPE_CHECKING:  # pragma: no cover
        def insert_to_event_table(self, object_id_list: List[str]) -> None:
            ...
