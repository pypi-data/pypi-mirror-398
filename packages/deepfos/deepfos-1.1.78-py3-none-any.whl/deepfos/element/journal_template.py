import re
from enum import Enum
from typing import Union, Type, Dict, List, Any, Tuple, Set, TYPE_CHECKING

import pandas as pd
from loguru import logger

from deepfos.api.journal_template import JournalTemplateAPI
from deepfos.api.models.journal_template import *
from deepfos.element.apvlprocess import ApprovalProcess, AsyncApprovalProcess
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.element.datatable import (
    DataTableMySQL, AsyncDataTableMySQL, get_table_class,
    T_AsyncDatatableClass, T_DatatableClass
)
from deepfos.element.rolestrategy import RoleStrategy, AsyncRoleStrategy
from deepfos.lib.asynchronous import future_property
from deepfos.lib.decorator import cached_property

__all__ = ['AsyncJournalTemplate', 'JournalTemplate', 'FullPostingParameter']


ORDER_TYPE = "orderType"
FILTER_VALUE = "filterValue"
FILTER_TYPE = "filterType"
FIELD_TYPE = "fieldType"
TABLE_TYPE = "tableType"
COLUMN_CODE = "columnCode"
COMMON_PARAMETERS = 'Common_parameters'


class Order(Enum):
    asc = "asc"
    desc = "desc"


def _valid_and_maybe_join_value(where):
    type_error = {}
    for dim, value in where.items():
        if isinstance(value, list):
            where[dim] = ",".join([str(v) for v in value])
        elif isinstance(value, str):
            pass
        else:
            type_error[dim] = value

    if type_error:
        raise ValueError(
            "\n".join(
                [f"参数: {dim}的值需为维度成员或维度成员组成的列表，实际值: {value}"
                 for dim, value in type_error.items()
                 ]
            ))

    return where


class FullPostingParameter:
    """完整过账筛选信息类

    将根据提供的过账参数类别自动生成与参数类别名一致的成员变量，并可通过成员变量设置该类别的过账筛选条件

    Args:
        param_categories: 过账参数类别

    """

    def __init__(self, param_categories: Union[List, Tuple, Set]):
        if not isinstance(param_categories, (List, Tuple, Set)):
            raise TypeError("预期参数类别为列表、元组或集合")

        self._all_categories = {}

        for c in set(list(param_categories)):
            if c.startswith('_'):
                raise ValueError(f'参数类别不可以下划线开头:{c}')
            self._all_categories[c] = {}

    def __setattr__(self, name: str, value: Dict[str, Union[str, List[str]]]):
        if name == '_all_categories':
            super().__setattr__(name, value)
        else:
            if name not in self._all_categories:
                raise ValueError(f'成员: {name} 未设置为已知参数类别，'
                                 f'已有参数类别：\n{set(self._all_categories.keys())}')
            self._all_categories[name] = value


class ColumnNode:
    """组织批量筛选信息中的字段部分，可进一步使用其中的成员方法表示筛选字段的表达式

    Args:
        column_code: 字段编码
        table_type: 表类型编码
        field_type: 字段类型编码

    See Also:
        :class:`QueryBuilder` , :class:`Table`

    """

    def __init__(self, column_code, table_type, field_type):
        self.column_code = column_code
        self.filter_type = None
        self.filter_value = None
        self.field_type = field_type
        self.table_type = table_type
        self.order = Order.asc.value

    def is_in(self, values: Union[List[str], str]) -> 'ColumnNode':
        """在列表中"""
        if isinstance(values, List):
            values = ",".join([str(v) for v in values])

        self.filter_type = "in"
        self.filter_value = values
        return self

    def not_in(self, values: Union[List[str], str]) -> 'ColumnNode':
        """不在列表中"""
        if isinstance(values, List):
            values = ",".join([str(v) for v in values])

        self.filter_type = "not in"
        self.filter_value = values
        return self

    def eq(self, other) -> 'ColumnNode':
        """等于"""
        self.filter_type = "="
        self.filter_value = other
        return self

    def ne(self, other) -> 'ColumnNode':
        """不等于"""
        self.filter_type = "!="
        self.filter_value = other
        return self

    def contains(self, value) -> 'ColumnNode':
        """包含"""
        self.filter_type = "like"
        self.filter_value = value
        return self

    def gt(self, other) -> 'ColumnNode':
        """大于或晚于"""
        self.filter_type = ">"
        self.filter_value = other
        return self

    def gte(self, other) -> 'ColumnNode':
        """大于等于"""
        self.filter_type = ">="
        self.filter_value = other
        return self

    def lt(self, other) -> 'ColumnNode':
        """小于或早于"""
        self.filter_type = "<"
        self.filter_value = other
        return self

    def lte(self, other) -> 'ColumnNode':
        """小于等于"""
        self.filter_type = "<="
        self.filter_value = other
        return self

    latter_than = gt

    earlier_than = lt

    def asc(self) -> 'ColumnNode':
        """升序"""
        self.order = Order.asc.value
        return self

    def desc(self) -> 'ColumnNode':
        """降序"""
        self.order = Order.desc.value
        return self

    def to_columns(self) -> Dict[str, Union[str, int]]:
        return {COLUMN_CODE: self.column_code,
                TABLE_TYPE: self.table_type,
                FIELD_TYPE: self.field_type}

    def to_where(self) -> Dict[str, Union[str, int]]:
        return {COLUMN_CODE: self.column_code,
                FILTER_TYPE: self.filter_type,
                FILTER_VALUE: self.filter_value,
                TABLE_TYPE: self.table_type,
                FIELD_TYPE: self.field_type}

    def to_orderby(self) -> Dict[str, str]:
        return {COLUMN_CODE: self.column_code,
                ORDER_TYPE: self.order}


class Table:
    """组织批量筛选信息中的表，从中访问成员等同于指定表的某列，将获得以相应成员名命名的 :class:`ColumnNode` 对象

    Args:
        field_type: 单据模型元素内的主表和子表的字段信息字典，键为字段编码，值为主子表标识与字段类型标识的元组

    See Also:
        :class:`QueryBuilder` , :class:`ColumnNode`

    """

    def __init__(self, field_type):
        self._field_type = field_type

    def __getattr__(self, item) -> ColumnNode:
        if item not in self._field_type:
            raise ValueError(f"字段名需为当前单据模板表中字段，现有字段: {list(self._field_type.keys())}")
        return ColumnNode(item, *self._field_type[item])


class QueryBuilder:
    """组织批量筛选信息的主体

    Args:
        field_type: 单据模型元素内的主表和子表的字段信息字典，键为字段编码，值为主子表标识与字段类型标识的元组

    See Also:
        :class:`Table` , :class:`ColumnNode`

    """

    def __init__(self, field_type):
        self._field_type = field_type
        self._columns = []
        self._filters = []
        self._orderby = []

    def columns(self, cols: List[Union[ColumnNode, str]]):
        """提供结果列信息"""
        for col in cols:
            if not isinstance(col, (ColumnNode, str)):
                raise ValueError("需提供ColumnNode类的对象或字段名组成的列表作为列信息，ColumnNode可从Table对象创建")

            if isinstance(col, ColumnNode):
                self._columns.append(col.to_columns())
            else:
                if col not in self._field_type:
                    raise ValueError(f"字段名需为当前单据模板表中字段，现有字段: {list(self._field_type.keys())}")
                self._columns.append({
                    COLUMN_CODE: col,
                    TABLE_TYPE: self._field_type[col][0],
                    FIELD_TYPE: self._field_type[col][1]
                })
        return self

    def where(self, filter_list: List[ColumnNode]):
        """提供筛选列信息"""
        for col in filter_list:
            if not isinstance(col, ColumnNode):
                raise ValueError("需提供ColumnNode类的对象作为筛选条件，ColumnNode可从Table对象创建")
            self._filters.append(col.to_where())
        return self

    def order_by(self, by: List[ColumnNode]):
        """提供排序列信息"""
        for col in by:
            if not isinstance(col, ColumnNode):
                raise ValueError("需提供ColumnNode类的对象作为排序信息，ColumnNode可从Table对象创建")
            self._orderby.append(col.to_orderby())
        return self

    def get_payload(self):
        """从当前Query组织内容中获得组织结果"""
        if len(self._columns) == 0:
            for (column_code, (table_type, field_type)) in self._field_type.items():
                self._columns.append({
                    COLUMN_CODE: column_code,
                    FIELD_TYPE: field_type,
                    TABLE_TYPE: table_type
                })
        return {
            'headerParams': self._filters,
            'columnParams': self._columns,
            'orderColumns': self._orderby
        }


class AsyncJournalTemplate(ElementBase[JournalTemplateAPI]):
    """单据模板"""
    @future_property
    async def meta(self) -> JournalTemplateDetail:
        """元信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.journaltemplate.query_detail(
            JournalTemplateQuery.construct_from(
                ele_info
            )
        )

    @cached_property
    def basic_info(self) -> JournalTemplateBaseInfo:
        """基本信息"""
        return self.meta.journalTemplateInfo.baseInfo

    @cached_property
    def posting_info(self) -> PostingInfoDto:
        """过账信息"""
        return self.meta.postingInfo

    @cached_property
    def _datatable_class(self) -> T_AsyncDatatableClass:
        if (server_name := self.basic_info.approveRecord.serverName) is None:
            return AsyncDataTableMySQL

        return get_table_class(server_name, sync=False)

    @cached_property
    def approval_record(self):
        """审批记录数据表元素"""
        if self.basic_info.approveRecord is None:
            raise ValueError('无审批记录表')

        return self._datatable_class(
            element_name=self.basic_info.approveRecord.dbName,
            folder_id=self.basic_info.approveRecord.folderId,
            path=self.basic_info.approveRecord.dbPath,
            table_name=self.basic_info.approveRecord.actualTableName
        )

    @cached_property
    def close_account(self):
        """关账流程数据表元素"""
        if self.basic_info.closeAccountDB is None:
            raise ValueError('无关账流程表')

        return self._datatable_class(
            element_name=self.basic_info.closeAccountDB.dbName,
            folder_id=self.basic_info.closeAccountDB.folderId,
            path=self.basic_info.closeAccountDB.dbPath,
            table_name=self.basic_info.closeAccountDB.actualTableName
        )

    @cached_property
    def approval_process(self) -> AsyncApprovalProcess:
        """审批流元素"""
        approval_info = self.meta.journalTemplateInfo.approvalProcessInfo

        if approval_info is None or approval_info.elementDetail is None:
            raise ValueError('无审批流元素信息')

        approval_ele = approval_info.elementDetail

        return AsyncApprovalProcess(element_name=approval_ele.elementName,
                                    folder_id=approval_ele.folderId,
                                    path=approval_ele.path)

    @cached_property
    def role_strategy(self) -> AsyncRoleStrategy:
        """角色方案元素"""
        if (rs_detail := self.basic_info.rsElementDetail) is None:
            raise ValueError('无角色方案元素信息')

        return AsyncRoleStrategy(
            element_name=rs_detail.elementName,
            folder_id=rs_detail.folderId,
            path=rs_detail.path,
            server_name=rs_detail.serverName
        )

    @future_property
    async def posting_params(self) -> PostingParam:
        """过账参数信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        res = await api.posting.query_posting_param(
            PostingParamQueryDto.construct_from(ele_info)
        )
        return res.params

    @cached_property
    def fixed_posting_dims(self):
        res = {}
        for cate, dim_list in self.posting_params.items():
            res[cate] = set([detail['dimensionCode'] for detail in dim_list])
        return res

    @cached_property
    def header_info(self) -> JournalTemplateAreaInfo:
        """日记账头信息"""
        return self.meta.journalTemplateInfo.headerInfo

    @cached_property
    def header_columns(self):
        """日记账头列信息"""
        return [
            col.dataTableInfo.columnCode
            for col in self.header_info.columns
        ]

    @cached_property
    def body_info(self) -> JournalTemplateAreaInfo:
        """日记账体信息"""
        return self.meta.journalTemplateInfo.bodyInfo

    @cached_property
    def body_columns(self):
        """日记账体列信息"""
        return [
            col.dataTableInfo.columnCode
            for col in self.body_info.columns
        ]

    @cached_property
    def foot_info(self) -> JournalTemplateAreaInfo:
        """单据尾信息"""
        return self.meta.journalTemplateInfo.footInfo

    @cached_property
    def foot_columns(self):
        """单据列信息"""
        return [
            col.dataTableInfo.columnCode
            for col in self.foot_info.columns
        ]

    @cached_property
    def field_type(self):
        """字段信息"""
        field_type = {col.dataTableInfo.columnCode: (1, col.logicInfo.valueType)
                      for col in self.header_info.columns}
        field_type.update({col.dataTableInfo.columnCode: (2, col.logicInfo.valueType)
                           for col in self.body_info.columns})
        return field_type

    @cached_property
    def table(self) -> Table:
        """组织批量筛选信息中的表对象"""
        return Table(self.field_type)

    def new_query(self) -> QueryBuilder:
        """获得新的组织批量筛选信息的对象"""
        return QueryBuilder(self.field_type)

    def _gen_single_data(self, main_row, body, main_column, body_column):
        main_index = main_row.name
        if isinstance(body.loc[main_index], pd.DataFrame):
            body_data = JournalBodyData(
                bodyActualTableName=self.body_info.dataTableBaseInfo.actualTableName,
                data=body.loc[main_index][body_column].to_dict(orient='records'),
                delEntryCode=[])
        else:
            body_data = JournalBodyData(
                bodyActualTableName=self.body_info.dataTableBaseInfo.actualTableName,
                data=[body.loc[main_index][body_column].to_dict()],
                delEntryCode=[])
        single_data = JournalData(
            mainData=JournalMainData(
                journalCode='',
                columnCode='',
                mainActualTableName=self.header_info.dataTableBaseInfo.actualTableName,
                data=main_row[main_column].to_dict()
            ),
            bodyData=body_data)

        return single_data

    @staticmethod
    def _yield_data(data: List[JournalData], chunksize: int):
        for start in range(0, len(data), chunksize):
            yield data[start: start + chunksize]

    async def batch_save(
        self,
        main: pd.DataFrame,
        body: pd.DataFrame,
        columns: List[str] = None,
        chunksize: int = 1000
    ):
        """批量保存日记账头和日记账体数据

        Args:
            main: 日记账头数据Dataframe
            body: 日记账体数据Dataframe
            columns: 日记账头和日记账体的关联列，如提供，将以此作为日记账头和日记账体的索引，并关联组织批量保存的数据
            chunksize: 保存单批次数据大小(以单行日记账头为单位)


        .. admonition:: 示例

            #. 初始化日记账元素

                .. code-block:: python

                    from deepfos.element.journal_template import JournalTemplate
                    jt = JournalTemplate('Journal_elimadj')


            #. 准备日记账头和日记账体数据

                .. code-block:: python

                    main = pd.DataFrame([
                        {"journal_name": "foo", "year": "2022", "period": "1", "entity": "JH", "rate": 1},
                        {"journal_name": "bar", "year": "2021", "period": "2", "entity": "JH", "rate": 2}
                    ])

                    body = pd.DataFrame([
                         {"ICP": "HC", "account": "101", "rate": 1, "original_credit": 222, "credit": 222},
                         {"ICP": "HCX", "account": "o1", "rate": 2, "original_credit": 111, "credit": 111},
                         {"ICP": "HC", "account": "102", "rate": 1, "original_credit": 222, "credit": 222},
                         {"ICP": "HCX", "account": "o2", "rate": 2, "original_credit": 111, "credit": 111}
                         ]
                    )

            #. 在传入 `batch_save` 方法前，通过设定日记账头和日记账体的index的方式准备关联关系，然后传入 `batch_save` 方法

                .. code-block:: python

                    main = main.set_index(['rate'], drop=False)
                    body = body.set_index(['rate'], drop=False)

                    jt.batch_save(main, body)

            #. 对于关联列为相同列名时，亦可直接在 `batch_save` 的入参中提供列信息，将以该列信息做后续关联

                .. code-block:: python

                    jt.batch_save(main, body, columns=['rate'])

            #. 这两种写法在当前例子中等价

            保存的batchData：

            .. code-block:: python

                [
                    JournalData(
                        mainData=JournalMainData(
                            mainActualTableName='main_table_actual_name',
                            data={'journal_name': 'foo', 'entity': 'JH', 'period': '1', 'year': '2022'}
                        ),
                        bodyData=JournalBodyData(
                            bodyActualTableName='body_table_actual_name',
                            data=[
                                {'original_credit': '222', 'account': '101', 'ICP': 'HC', 'credit': '222', 'rate': '1'},
                                {'original_credit': '222', 'account': '102', 'ICP': 'HC', 'credit': '222', 'rate': '1'}
                            ]
                        )
                    ),
                    JournalData(
                        mainData=JournalMainData(
                            mainActualTableName='main_table_actual_name',
                            data={'journal_name': 'bar', 'entity': 'JH', 'period': '2', 'year': '2021'}
                        ),
                        bodyData=JournalBodyData(
                            bodyActualTableName='body_table_actual_name',
                            data=[
                                {'original_credit': '111', 'account': 'o1', 'ICP': 'HCX', 'credit': '111', 'rate': '2'},
                                {'original_credit': '111', 'account': 'o2', 'ICP': 'HCX', 'credit': '111', 'rate': '2'}
                            ]
                        )
                    )
                ]

        """
        if columns is not None:
            if set(columns)-set(main.columns) != set() or set(columns)-set(body.columns) != set():
                raise ValueError("关联列不同时属于提供的主表和子表DataFrame")

            main = main.set_index(columns, drop=False)
            body = body.set_index(columns, drop=False)

        main = main.fillna('').astype(str)
        body = body.fillna('').astype(str)

        try:
            main_column = list(set(main.columns).intersection(self.header_columns))
            body_column = list(set(body.columns).intersection(self.body_columns))
            batch_data = main.apply(self._gen_single_data,
                                    body=body, main_column=main_column, body_column=body_column,
                                    axis=1).to_list()
        except KeyError:
            logger.exception('组织日记账头与日记账体中发生错误')
            raise ValueError('日记账头与日记账体无法正确关联')

        for part in self._yield_data(batch_data, chunksize):
            await self.async_api.journal.batch_save(
                JournalBatchDataDTO(
                    path=self._path,
                    folderId=self.element_info.folderId,
                    templateCode=self.element_name,
                    isNew=True,
                    batchData=part
                )
            )

    async def delete(self, where: Union[pd.DataFrame, Dict[str, List]]) -> DataTableCustomSqlResultDTO:
        """按条件删除日记账数据

        Args:
            where: 日记账头内字段与值的列表组成的字典，或需删除的数据所组成的dataFrame


        """
        if isinstance(where, pd.DataFrame):
            where = where.fillna('')
            where = where.astype(str)
            where = where.to_dict(orient='list')

        if len(set(self.header_columns).union(where.keys())) != len(set(self.header_columns)):
            raise ValueError(f'筛选字段需为日记账头内字段，日记账头字段: {self.header_columns}')

        for k, v in where.items():
            where[k] = [e for e in set(v) if e != '']

        return await self.async_api.journal.delete_by_filter(
            JournalDataBatchDel(
                templateCode=self.element_name,
                path=self._path,
                folderId=self.element_info.folderId,
                memberInfo=where
            )
        )

    def _get_posting_payload(self, where) -> PostingRequestDto:
        param_body = self.posting_params
        fixed_para_category = None

        if len(param_body) == 1:
            fixed_para_category = list(param_body.keys())[0]
        else:
            if not isinstance(where, FullPostingParameter):
                if COMMON_PARAMETERS in param_body:
                    fixed_para_category = COMMON_PARAMETERS
                else:
                    raise ValueError('过账参数类别不唯一，且无“共有参数”，需提供具体过账类别信息，'
                                     f'当前已有过账类别：[{list(param_body.keys())}]\n'
                                     f'具体过账参数信息可通过 posting_params 和 posting_info 查看')

        where_with_category = {}

        not_pov_dim = set()

        if isinstance(where, FullPostingParameter):
            for category, value in where._all_categories.items():  # noqa
                value = _valid_and_maybe_join_value(value)
                where_with_category[category] = value
                not_pov_dim = not_pov_dim.union(set(value.keys())-self.fixed_posting_dims[category])
        else:
            where = _valid_and_maybe_join_value(where)
            where_with_category[fixed_para_category] = where
            not_pov_dim = set(where.keys()) - self.fixed_posting_dims[fixed_para_category]

        if unknown_param := (set(where_with_category.keys()) - set(param_body.keys())):
            raise ValueError(f"参数类型: {unknown_param} 不在当前日记账模板中")

        if not_pov_dim:
            raise ValueError(f"{not_pov_dim} 不在过账筛选的固定维度中")

        for category, where in where_with_category.items():
            for dim_filter in param_body[category]:
                if (dim := dim_filter['dimensionCode']) in where:
                    dim_filter['defaultValue'] = where[dim]

        return PostingRequestDto(
            templateQuery=JournalTemplateQuery.construct_from(self.element_info),
            postingInfoParam=PostingParam(params=param_body)
        )

    async def get_posting(
        self,
        where: Union[Dict[str, Union[str, List[str]]], FullPostingParameter]
    ) -> Any:
        """按条件选取过账

        Args:
            where: 筛选条件，如仅提供字段名与值组成的字典，则在共有参数中进行筛选，
                如需增加其他内存财务模型中特有的参数，请使用FullPostingParameter类构造特有参数信息

        See Also:
            :class:`FullPostingParameter`

        """
        return await self.async_api.posting.get_posting(self._get_posting_payload(where))

    async def cancel_posting(
        self,
        where: Union[Dict[str, Union[str, List[str]]], FullPostingParameter]
    ) -> Any:
        """按条件选取取消过账

        Args:
            where: 筛选条件，如仅提供字段名与值组成的字典，则在共有参数中进行筛选，
                如需增加其他内存财务模型中特有的参数，请使用FullPostingParameter类构造特有参数信息

        See Also:
            :class:`FullPostingParameter`

        """
        return await self.async_api.posting.cancel_posting(self._get_posting_payload(where))

    async def batch_query_raw(
        self,
        query: QueryBuilder,
        show_detail: bool = False,
        need_desc: bool = False
    ) -> List[Dict]:
        """批量查询日记账数据

        Args:
            query: QueryBuilder类的对象，表示了筛选条件全信息
            show_detail: 在涉及维度筛选时，是否包括其下明细，默认为False
            need_desc: 返回数据是否包括描述，默认为False

        Returns:
            日记账查询的原始数据

        .. admonition:: 示例

            #. 初始化

                .. code-block:: python

                    from deepfos.element.journal_template import JournalTemplate
                    jt = JournalTemplate('Journal_elimadj')
                    t = jt.table
                    q = jt.query


            #. 在不提供列信息时，等同于查询所有列，返回值将包括符合条件的所有非全空列数据

                .. code-block:: python

                    # 查询account字段等于1001001且ICP字段不等于1.0的所有非全空列数据
                    # 以period倒序，posting_status倒序的方式排序
                    q = jt.new_query()
                    data = jt.batch_query_raw(
                            q.where([
                                    t.account.eq("1001001"),
                                    t.ICP.ne("1.0"),
                                    ])
                             .order_by([t.period.desc(), t.posting_status.desc()])
                    )

            #. 在提供列信息时，将查询指定列

                .. code-block:: python

                    # 查询ICP字段等于HC且period大于2的posting_status、invalid_status、data_status、remark列非全空列数据
                    q = jt.new_query()
                    data = jt.batch_query_raw(
                            q.columns([t.posting_status, t.invalid_status, t.data_status, t.remark])
                             .where([
                                    t.ICP.eq("HC"),
                                    t.period.gt("2"),
                                    ]
                             )
                    )

        See Also:
            :meth:`new_query`，如果希望返回 ``DataFrame`` 的数据，可以使用 :meth:`batch_query`

        """
        if not isinstance(query, QueryBuilder):
            raise TypeError("该方法的query参数应为QueryBuilder类的对象")

        payload = JournalOrderDataBatchQuery(
            templateCode=self.element_name,
            folderId=self.element_info.folderId,
            path=self._path,
            needDesc=need_desc,
            showDetail=show_detail,
            **query.get_payload()
        )
        res = await self.async_api.journal.get_batch_data(payload)
        return res.selectResult

    async def batch_query(
        self,
        query: QueryBuilder,
        show_detail: bool = False
    ) -> pd.DataFrame:
        """批量查询日记账数据

        Args:
            query: QueryBuilder类的对象，表示了筛选条件全信息
            show_detail: 在涉及维度筛选时，是否包括其下明细，为True则包括

        Returns:
            日记账查询的结果DataFrame

        .. admonition:: 示例

            #. 初始化

                .. code-block:: python

                    from deepfos.element.journal_template import JournalTemplate
                    jt = JournalTemplate('Journal_elimadj')
                    t = jt.table


            #. 在不提供列信息时，等同于查询所有列，返回值将包括符合条件的所有非全空列数据

                .. code-block:: python

                    # 查询account字段等于1001001且ICP字段不等于1.0的所有非全空列数据
                    # 以period倒序，posting_status倒序的方式排序
                    q = jt.new_query()
                    data = jt.batch_query(
                            q.where([
                                    t.account.eq("1001001"),
                                    t.ICP.ne("1.0"),
                                    ])
                             .order_by([t.period.desc(), t.posting_status.desc()])
                    )

            #. 在提供列信息时，将查询指定列

                .. code-block:: python

                    # 查询ICP字段等于HC且period大于2的posting_status、invalid_status、data_status、remark列非全空列数据
                    q = jt.new_query()
                    data = jt.batch_query(
                            q.columns([t.posting_status, t.invalid_status, t.data_status, t.remark])
                             .where([
                                    t.ICP.eq("HC"),
                                    t.period.gt("2"),
                                    ]
                             )
                    )

        See Also:
            :meth:`new_query`，如果希望返回原始数据，可以使用 :meth:`batch_query_raw`

        """
        raw = await self.batch_query_raw(query, show_detail)
        return pd.DataFrame(raw)


class JournalTemplate(AsyncJournalTemplate, metaclass=SyncMeta):
    synchronize = ('batch_save', 'batch_query', 'batch_query_raw',
                   'delete', 'get_posting', 'cancel_posting')

    if TYPE_CHECKING:  # pragma: no cover
        def batch_save(self, main: pd.DataFrame, body: pd.DataFrame, columns: List[str] = None, chunksize: int = 1000):
            ...

        def batch_query(
            self,
            query: QueryBuilder,
            show_detail: bool = False
        ) -> pd.DataFrame:
            ...

        def batch_query_raw(
            self,
            query: QueryBuilder,
            show_detail: bool = False,
            need_desc: bool = False
        ) -> List[Dict]:
            ...

        def delete(self, where: Union[pd.DataFrame, Dict[str, List]]) -> DataTableCustomSqlResultDTO:
            ...

        def get_posting(
            self,
            where: Union[Dict[str, Union[str, List[str]]],
                         FullPostingParameter]
        ) -> Any:
            ...

        def cancel_posting(
            self,
            where: Union[Dict[str, Union[str, List[str]]],
                         FullPostingParameter]
        ) -> Any:
            ...

    @cached_property
    def _datatable_class(self) -> T_DatatableClass:
        if (server_name := self.basic_info.approveRecord.serverName) is None:
            return DataTableMySQL

        return get_table_class(server_name)

    @cached_property
    def approval_record(self):
        """审批记录数据表元素"""
        if self.basic_info.approveRecord is None:
            raise ValueError('无审批记录表')

        return self._datatable_class(
            element_name=self.basic_info.approveRecord.dbName,
            folder_id=self.basic_info.approveRecord.folderId,
            path=self.basic_info.approveRecord.dbPath,
            table_name=self.basic_info.approveRecord.actualTableName
        )

    @cached_property
    def close_account(self):
        """关账流程数据表元素"""
        if self.basic_info.closeAccountDB is None:
            raise ValueError('无关账流程表')

        return self._datatable_class(
            element_name=self.basic_info.closeAccountDB.dbName,
            folder_id=self.basic_info.closeAccountDB.folderId,
            path=self.basic_info.closeAccountDB.dbPath,
            table_name=self.basic_info.closeAccountDB.actualTableName
        )

    @cached_property
    def approval_process(self) -> ApprovalProcess:
        """审批流元素"""
        approval_info = self.meta.journalTemplateInfo.approvalProcessInfo

        if approval_info is None or approval_info.elementDetail is None:
            raise ValueError('无审批流元素信息')

        approval_ele = approval_info.elementDetail

        return ApprovalProcess(
            element_name=approval_ele.elementName,
            folder_id=approval_ele.folderId,
            path=approval_ele.path,
            server_name=approval_ele.serverName
        )

    @cached_property
    def role_strategy(self) -> RoleStrategy:
        """角色方案元素"""
        if (rs_detail := self.basic_info.rsElementDetail) is None:
            raise ValueError('无角色方案元素信息')

        return RoleStrategy(
            element_name=rs_detail.elementName,
            folder_id=rs_detail.folderId,
            path=rs_detail.path,
            server_name=rs_detail.serverName
        )
