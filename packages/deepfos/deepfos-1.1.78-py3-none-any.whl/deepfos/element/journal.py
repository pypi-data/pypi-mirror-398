import uuid

from deepfos.api.models import compat_parse_obj_as as parse_obj_as
from deepfos.element.datatable import get_table_class
from deepfos.exceptions import (
    JournalModelSaveError, JournalModelCheckError, JournalModelPostingError
)
from deepfos.lib.asynchronous import future_property
from typing import List, Union, TYPE_CHECKING, Tuple, Dict, Literal
from pypika.terms import Term, EmptyCriterion
from pypika import Table
from deepfos.lib.decorator import cached_property
import pandas as pd
import numpy as np
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.api.journal_model import JournalModelAPI
from deepfos.api.models.journal_model import (
    ModelDataQueryVO,
    CheckStandardVO,
    JmPostParamVO,
    JmPostResultVO,
    JournalModelExecCallbackPythonDTO as CallbackInfo,
    CommonResultDTO,
    ModelDataBatchDTO,
    ModelDataDeleteDTO,
    JournalModelConfig,
    JournalSortConfig
)

__all__ = [
    "JournalModel",
    "AsyncJournalModel"
]

MAIN_ID = '_main_id'
DEFAULT_CALLBACK_SERVER_NAME = "python-server2-0"

_escape_table = {
    ord('\\'): u'\\\\',
    ord('.'): u'\\.',
    ord('('): u'\\(',
    ord(')'): u'\\)',
    ord('['): u'\\[',
    ord(']'): u'\\]',
    ord('{'): u'\\{',
    ord('}'): u'\\}',
    ord('*'): u'\\*',
    ord('+'): u'\\+',
    ord('$'): u'\\$',
    ord('?'): u'\\?',
    ord('|'): u'\\|',
    ord('='): u'\\=',
    ord('^'): u'\\^',
    ord(':'): u'\\:',
}


class AsyncJournalModel(ElementBase[JournalModelAPI]):
    """凭证组件"""
    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        self.__tbl_name = None
        super().__init__(element_name, folder_id, path, server_name)

    @future_property
    async def config(self) -> JournalModelConfig:
        """凭证模型的元素信息"""
        api = await self.wait_for('async_api')
        element_info = await self.wait_for('element_info')
        res = await api.journal_model_data.get_config(element_info)
        return res

    @cached_property
    def quote_char(self) -> str:
        try:
            element_type = self.config.logicTable.dataTableInfo.elementDetail.elementType
            dbcls = get_table_class(element_type)
            return dbcls.quote_char
        except Exception: # noqa
            return '`'

    @cached_property
    def table_name(self) -> str:
        """数据表真实表名"""
        if self.__tbl_name is None:
            self.__tbl_name = self.config.logicTable.dataTableInfo.actualTableName
        return self.__tbl_name

    @cached_property
    def table(self) -> Table:
        """pipyka的Table对象

        主要用于创建查询条件

        See Also:
            关于table的更多使用方法，可以查看
            `pypika的github <https://github.com/kayak/pypika#tables-columns-schemas-and-databases>`_

        """
        try:
            element_type = self.config.logicTable.dataTableInfo.elementDetail.elementType
            dbcls = get_table_class(element_type)
            return Table(self.table_name, query_cls=dbcls.query)
        except Exception: # noqa
            return Table(self.table_name)

    def _parse_where(self, where: Union[None, Term, EmptyCriterion]) -> str:
        if isinstance(where, (Term, EmptyCriterion)):
            return where.get_sql(quote_char=self.quote_char)
        if isinstance(where, str):
            return where
        raise TypeError(f"Unsupported type: {type(where)} for where.")

    def _gen_batch_payload(
        self,
        head_df: pd.DataFrame,
        line_df: pd.DataFrame,
        callback: Union[Dict, CallbackInfo] = None,
        relation_field: str = 'journal_id',
        id_col: str = MAIN_ID,
        enable_create: bool = True,
        enable_default_value: bool = True,
        enable_repeat_check: bool = True,
        enable_required: bool = True,
        enable_valid_range: bool = True,
        enable_all_errors: bool = True,
        enable_need_one_line: bool = True,
        header_operate: Literal['EDIT', 'ADD', 'DELETE_ADD'] = 'ADD',
        line_operate: Literal['EDIT', 'ADD', 'DELETE', 'DELETE_ADD'] = 'ADD',
    ):
        errors = set()

        if head_df.empty:
            errors.add('凭证头表数据DataFrame不能为空')
        if line_df.empty:
            errors.add('凭证行表数据DataFrame不能为空')
        if relation_field.strip() == '':
            errors.add('凭证头行表的关联字段relation_field不能为空')

        self._maybe_raise_errors(errors)
        is_editing = not (header_operate == 'ADD' and line_operate == 'ADD')

        if is_editing:
            head_required_fields = [relation_field, '_type', id_col]
            line_required_fields = [relation_field, id_col]
        else:
            head_required_fields = [relation_field, '_type']
            line_required_fields = [relation_field]

        for h_l_df, h_l, req_fields in zip(
            [head_df, line_df], ['头', '行'],
            [head_required_fields, line_required_fields]
        ):
            for field in req_fields:
                if (
                    field not in h_l_df.columns
                    or any(h_l_df[field].isna())
                    or any(h_l_df[field].astype(str, errors='ignore').str.strip() == '')
                ):
                    errors.add(f'凭证{h_l}表字段({field})不存在或有值为空')

        self._maybe_raise_errors(errors)

        if any(dup_ser := head_df[relation_field].duplicated()):
            raise JournalModelSaveError(
                f'凭证头表数据关联字段({relation_field})存在重复的值:\n'
                f'{set(head_df[relation_field][dup_ser])}'
            )

        table_type_pattern = "|".join(
            "(" + t.typeCode.translate(_escape_table) + ")"
            for t in self.config.journalModelType if t.typeCode
        )
        unknown_type = ~head_df['_type'].astype('str', errors='ignore').str.match(
            table_type_pattern
        )
        if unknown_type.any():
            raise JournalModelSaveError(
                f'凭证头表数据中凭证类型:\n'
                f'{set(head_df["_type"][unknown_type])}'
                f'\n在凭证模型中不存在'
            )

        head_data = head_df[head_required_fields]
        # generate headMainId
        if is_editing:
            head_data = head_data.rename(
                columns={"_type": "journalTypeCode", id_col: "headMainId"}
            )
        else:
            head_data = head_data.rename(
                columns={"_type": "journalTypeCode"}
            )
            head_data = head_data.assign(
                headMainId=pd.Series(
                    [uuid.uuid4().hex for _ in head_data.index],
                    index=head_data.index
                )
            )
        head_data = head_data.assign(operateType=header_operate)

        # NB: replace twice in case of infer None to nan happened
        head_df = head_df.replace({None: np.nan})
        head_df = head_df.replace({np.nan: None})

        head_data = head_data.assign(
            data=head_df.drop(columns=['_type']).to_dict(orient='records')
        )
        main_id_pattern = "|".join(
            "(" + str(mid).translate(_escape_table) + ")"
            for mid in head_df[relation_field]
        )

        unrelated_value = ~line_df[relation_field].astype(
            'str', errors='ignore'
        ).str.match(main_id_pattern)
        if unrelated_value.any():
            errors.add(
                f'凭证行表数据关联字段({relation_field})的值:\n'
                f'{set(line_df[relation_field][unrelated_value])}\n在凭证头表中不存在'
            )

        self._maybe_raise_errors(errors)

        line_data = line_df[line_required_fields]
        line_data = line_data.assign(operateType=line_operate)

        # generate lineMainId
        if is_editing:
            line_data = line_data.rename(columns={id_col: "lineMainId"})
        elif "lineMainId" in line_df.columns:
            line_main_id = line_df["lineMainId"]
            line_main_id[line_main_id.isna()] = [uuid.uuid4().hex for _ in
                                                 range(sum(line_main_id.isna()))]
            line_data["lineMainId"] = line_main_id
        else:
            line_data = line_data.assign(
                lineMainId=pd.Series(
                    [uuid.uuid4().hex for _ in line_data.index],
                    index=line_data.index
                )
            )

        # NB: replace twice in case of infer None to nan happened
        line_df = line_df.replace({None: np.nan})
        line_df = line_df.replace({np.nan: None})

        line_data = line_data.assign(data=line_df.to_dict(orient='records'))

        # merge head & line
        line_data = line_data.merge(
            head_data[[relation_field, "headMainId", "journalTypeCode"]],
            on=relation_field
        )

        # relation field is only used for merge
        head_data = head_data.drop(columns=[relation_field])
        line_data = line_data.drop(columns=[relation_field])

        if callback is not None:
            callback = parse_obj_as(CallbackInfo, callback)
            callback.serverName = callback.serverName or DEFAULT_CALLBACK_SERVER_NAME

        data_map = {
            self.config.logicTable.dataTableInfo.name: head_data.to_dict(
                orient='records'
            ),
            self.config.logicTable.children[0].dataTableInfo.name: line_data.to_dict(
                orient='records'
            )
        }
        return ModelDataBatchDTO(
            modelInfo=self.element_info,  # noqa
            callbackInfo=callback,
            dataMap=data_map,
            enableCreate=enable_create,
            enableDefaultValue=enable_default_value,
            enableRepeatCheck=enable_repeat_check,
            enableRequired=enable_required,
            enableValidRange=enable_valid_range,
            enableAllErrors=enable_all_errors,
            enableNeedOneLine=enable_need_one_line
        )

    async def save(
        self,
        head_df: pd.DataFrame,
        line_df: pd.DataFrame,
        callback: Union[Dict, CallbackInfo] = None,
        relation_field: str = 'journal_id',
        enable_create: bool = True,
        enable_default_value: bool = True,
        enable_repeat_check: bool = True,
        enable_required: bool = True,
        enable_valid_range: bool = True,
        enable_all_errors: bool = True,
        enable_need_one_line: bool = True,
        sync: bool = True
    ) -> CommonResultDTO:
        """凭证模型数据新增
        
        Args:
            head_df: 凭证头表的数据（字段名与凭证模型上头表的字段名对应）
            line_df: 凭证行表的数据（字段名与凭证模型上行表的字段名对应）
            callback: 回调脚本配置信息
                若为None，则保存模型数据在结束后不会调用脚本，
                如果配置了回调，则不论保存是否保存成功，都将在结束后调用回调该脚本
            relation_field: 用于指定凭证头、行表的关联字段，
                即通过该字段确定凭证头表对应的凭证行表数据，默认为journal_id
            enable_create: 是否启用创建人、创建时间自动赋值，默认为True
            enable_default_value: 是否启用字段值为空时使用默认值填充，默认为True
            enable_repeat_check: 是否启用业务主键重复的校验，默认为True
            enable_required: 是否启用必填字段的校验，默认为True
            enable_valid_range: 是否启用有效性范围的校验，默认为True
            enable_all_errors: 是否启用一次性校验所有规则和数据，默认为True
            enable_need_one_line: 是否启用凭证行表至少需要一条数据的校验，默认为True
            sync: 调用模型数据保存接口的类型，同步(True)/异步(False)，默认为同步
                异步保存接口会在收到保存请求时立刻响应，同步保存
                接口会等保存数据完成后才响应，并返回保存信息
                如果设置为同步，当数据量过大时可能会时间过长时，可能因超出SDK的接口响应超时时间而报错

        Returns:
           调用同步接口时返回信息（CommonResultDTO的success为true 表示成功，如false 则错误在errors集合里）

        .. admonition:: 示例

            1.以自定义数据选取参数执行

            .. code-block:: python

                # 凭证头表数据（注：_type的值必须对应模型配置的凭证类型代码，
                # journal_id的值在下面的行表中必须有对应的数据）
                head_df = pd.DataFrame([
                    {
                      "_type": "type_account_01", "journal_id": "head_main_id_202306080001",
                      "is_balance": "true", "scenario": "Actual", "version": "Working",
                      "value": "CNY", "entity": "[TotalEntity].[A]", "year": "2023",
                      "period": "12", "approve_time": "2023-05-23 15:56:00",
                      "convert_date": "2023-05-23"
                    },
                    {
                      "_type": "type_account_01", "journal_id": "head_main_id_202306080002",
                      "is_balance": "true", "scenario": "Actual","version": "Working",
                      "value": "CNY","entity": "[TotalEntity].[A]", "year": "2023",
                      "period": "12", "approve_time": "2023-05-23 15:56:00",
                      "convert_date": "2023-05-23"
                    }
                ])

                # 凭证行表数据(注：行表中的 journal_id 的值必须在头表数据中存在，line_no 不允许重复)
                line_df = pd.DataFrame([
                    {
                      "journal_id": "head_main_id_202306080001",
                      "line_no": "1","account": "100101","movement": "OPN",
                      "trx_debit": "130","debit": "130","comment_line": "line1"
                    },
                    {
                      "journal_id": "head_main_id_202306080001",
                      "line_no": "2","account": "100101","movement": "OPN",
                      "trx_credit": "130","credit": "130","comment_line": "line2"
                    },
                    {
                      "journal_id": "head_main_id_202306080002",
                      "line_no": "1","account": "100101","movement": "OPN",
                      "trx_debit": "130","debit": "130","comment_line": "line1"
                    },
                    {
                      "journal_id": "head_main_id_202306080002",
                      "line_no": "2", "account": "100101","movement": "OPN",
                      "trx_credit": "130","credit": "130","comment_line": "line2"
                    }
                ])

                # 回调脚本
                callback_info = {
                    "elementName": "testPy01", "elementType": "PY",
                    "path": "/zhy_test",
                    "callbackParams": {"year": "2023", "period": "03"}
                }
                # 创建凭证组件元素对象
                journal = JournalModel('ZHY_TEST_0613_02')
                # 调用保存
                res = journal.save(
                    head_df=head_df,
                    line_df=line_df,
                    callback=callback_info,
                    enable_create = True,
                    enable_default_value = False,
                    enable_repeat_check= True,
                    enable_required= False,
                    enable_valid_range= True,
                    enable_all_errors = True,
                    enable_need_one_line = True,
                    sync=True
                )


        Attention:

            以示例的回调参数为例，回调脚本接收到参数为

                .. code-block:: python

                # 凭证组件V1.0.6.3版本以前

                p2 = {
                   "batch_id": "b14d943609b",
                   "success": True,
                   "year": "2023",  # 自定义参数
                   "period": "03"   # 自定义参数
                }

                # 凭证组件V1.0.6.3版本及以后

                p2 = {
                   "mainKey": {
                        "journal_id": [
                            "ZDlhYj",
                            "ZWU00005",
                            "ZjY4MG",
                            "NWQ00002",
                            "ZTl00003",
                            "NmNiNW",
                            "YWM5ZG",
                            "M2E00004"
                        ]
                   },
                   "success": True,
                   "year": "2023",  # 自定义参数
                   "period": "03"   # 自定义参数
                }

    """
        batch = self._gen_batch_payload(
            head_df=head_df, line_df=line_df,
            callback=callback, relation_field=relation_field,
            enable_create=enable_create,
            enable_default_value=enable_default_value,
            enable_repeat_check=enable_repeat_check,
            enable_required=enable_required,
            enable_valid_range=enable_valid_range,
            enable_all_errors=enable_all_errors,
            enable_need_one_line=enable_need_one_line
        )
        if sync:
            resp = await self.async_api.journal_model_data.sync_save(batch)
        else:
            resp = await self.async_api.journal_model_data.save(batch)

        if not resp.success:
            raise JournalModelSaveError(
                f"Failed to save journal model.\n"
                f"Detail: {resp}"
            )
        return resp

    async def update(
        self,
        head_df: pd.DataFrame,
        line_df: pd.DataFrame,
        callback: Union[Dict, CallbackInfo] = None,
        relation_field: str = 'journal_id',
        enable_create: bool = True,
        enable_default_value: bool = True,
        enable_repeat_check: bool = True,
        enable_required: bool = True,
        enable_valid_range: bool = True,
        enable_all_errors: bool = True,
        enable_need_one_line: bool = True,
        header_operate: Literal['EDIT', 'DELETE_ADD'] = 'EDIT',
        line_operate: Literal['EDIT', 'ADD', 'DELETE', 'DELETE_ADD'] = 'EDIT',
    ) -> CommonResultDTO:
        """凭证模型数据更新

        只支持头行更新及行插入和删除

        Args:
            head_df: 凭证头表的数据（字段名与凭证模型上头表的字段名对应）
            line_df: 凭证行表的数据（字段名与凭证模型上行表的字段名对应）
            callback: 回调脚本配置信息
                若为None，则保存模型数据在结束后不会调用脚本，
                如果配置了回调，则不论保存是否保存成功，都将在结束后调用回调该脚本
            relation_field: 用于指定凭证头、行表的关联字段，
                即通过该字段确定凭证头表对应的凭证行表数据，默认为journal_id
            enable_create: 是否启用创建人、创建时间自动赋值，默认为True
            enable_default_value: 是否启用字段值为空时使用默认值填充，默认为True
            enable_repeat_check: 是否启用业务主键重复的校验，默认为True
            enable_required: 是否启用必填字段的校验，默认为True
            enable_valid_range: 是否启用有效性范围的校验，默认为True
            enable_all_errors: 是否启用一次性校验所有规则和数据，默认为True
            enable_need_one_line: 是否启用凭证行表至少需要一条数据的校验，默认为True
            header_operate: 凭证头表的操作类型，默认为EDIT
            line_operate: 凭证行表的操作类型，默认为EDIT
                         头表EDIT, 行表可以ADD/EDIT/DELETE
                         头表DELETE_ADD, 头表update，行表全删全增，行表只能为DELETE_ADD

        Returns:
           接口返回信息（CommonResultDTO的success为true 表示成功，如false 则错误在errors集合里）


    """
        batch = self._gen_batch_payload(
            head_df=head_df, line_df=line_df,
            callback=callback, relation_field=relation_field,
            id_col=MAIN_ID,
            enable_create=enable_create,
            enable_default_value=enable_default_value,
            enable_repeat_check=enable_repeat_check,
            enable_required=enable_required,
            enable_valid_range=enable_valid_range,
            enable_all_errors=enable_all_errors,
            enable_need_one_line=enable_need_one_line,
            header_operate=header_operate,
            line_operate=line_operate,
        )
        resp = await self.async_api.journal_model_data.update(batch)

        if not resp.success:
            raise JournalModelSaveError(
                f"Failed to update journal model.\n"
                f"Detail: {resp}"
            )
        return resp

    @staticmethod
    def _maybe_raise_errors(errors):
        if errors:
            raise JournalModelSaveError("\n".join(errors))

    async def check(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
        """凭证数据校验

        Args:
            where: 校验条件 （格式 可参考 数据表（DataTableMySQL）的条件格式）

        .. admonition:: 示例

            .. code-block:: python

                journal = JournalModel(element_name="ZHY_TEST_0613_02")
                t = journal.table
                # 校验数据的条件 （格式 可参考 数据表（DataTableMySQL）的条件格式，& 表示 and，| 表示 or）
                where = (
                    ((t.year == '2023') | (t.journal_id == 'head_main_id_202306080001'))
                    &
                    (t.entity.isin(['A','B']) | t.journal_id.like('head_main_id_202306080002%'))
                )
                journal.check(where)

        Hint:
            - 如果传入的校验条件数据存在，且校验成功，则会将凭证头表上的check_status字段的值改为'true'，失败则不改


        """
        where_str = None
        if where is not None:
            where_str = self._parse_where(where)
        param = CheckStandardVO(
            elementName=self.element_info.elementName,
            folderId=self.element_info.folderId,
            whereStr=where_str
        )
        resp = await self.async_api.journal_model_data.check(param)

        if not resp.success:
            raise JournalModelCheckError(
                f"Error occurs while checking journal model.\n"
                f"Detail: {resp}"
            )
        return resp

    async def delete(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
        """凭证数据删除

        Hint:
            - ``where`` 暂只支持凭证头表上的字段作为条件

        Args:
            where: 删除条件 （格式 可参考 数据表（DataTableMySQL）的条件格式）

        .. admonition:: 示例

            .. code-block:: python

                # 创建凭证组件元素对象
                journal = JournalModel(element_name="ZHY_TEST_0613_02")
                t = journal.table
                # 删除数据的条件 （格式 可参考 数据表（DataTableMySQL）的条件格式，& 表示 and，| 表示 or）
                where = (
                    ((t.year == '2023') | (t.journal_id == 'head_main_id_202306080001'))
                    &
                    (t.entity.isin(['A','B']) | t.journal_id.like('head_main_id_202306080002%'))
                )
                # 调用删除方法
                journal.delete(where)

            将执行sql：（只需关注 where 后的条件）

            .. code-block:: sql

                DELETE h,l
                FROM
                    凭证头表 h left join 凭证行表 l on h.journal_id = l.journal_id
                WHERE
                    (h.`year`='2023' OR `h.journal_id`= 'head_main_id_202306080001')
                    AND
                    (h.`entity` IN ('A','B') OR h.`journal_id` LIKE 'head_main_id_202306080002%')

        """
        where_str = self._parse_where(where)
        model_data = ModelDataDeleteDTO(
            elementName=self.element_info.elementName,
            folderId=self.element_info.folderId,
            whereStr=where_str
        )
        res = await self.async_api.journal_model_data.delete(model_data)
        if not res.success:
            raise JournalModelSaveError(','.join([x.msg for x in res.errors]))
        return res

    async def query(
        self,
        where: Union[str, Term, EmptyCriterion] = None,
        head_column: List[str] = None,
        line_column: List[str] = None,
        sort_config: List[JournalSortConfig] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """凭证数据查询

        Args:
            where: 查询条件,条件字段名必须与凭证头、行表上字段名保持一致（格式 可参考 数据表（DataTableMySQL）的条件格式）
            head_column: 查询返回的头表字段集合  如： ["entity","year","journal_id"]
            line_column: 查询返回的行表字段集合  如： ["journal_id","line_no","account","trx_amount"]
            sort_config: 排序配置集合 如： [{"col": "journal_id","type": "asc"},{"col": "line_no","type": "asc"}]


        .. admonition:: 示例

            .. code-block:: python

                # 创建凭证组件元素对象
                journal = JournalModel(element_name="ZHY_TEST_0615_01")
                t = journal.table
                # 查询数据的条件 （格式 可参考 数据表（DataTableMySQL）的条件格式，& 表示 and，| 表示 or）
                where = (
                        ((t.journal_id == 'head_main_id_202306080001') | (t.line_no == '1'))
                        &
                        (t.entity.isin(['A','B']) | t.journal_id.like('head_main_id_202306080002%'))
                )
                head_columns = ["entity", "journal_id", "year", "period", "journal_name"]
                line_columns = ["journal_id", "line_no", "account", "trx_amount", "debit", "credit"]
                sort = [{"col": "journal_id", "type": "desc"}, {"col": "line_no", "type": "asc"}]
                # 调用查询方法，并返回 头和行的 DataFrame
                head_df, line_df = journal.query(where=where,
                                                head_column=head_columns,
                                                line_column=line_columns,
                                                sort_config=sort)

            将执行sql：（只需关注 where 后的条件）

            .. code-block:: sql

                select h.*,l.*
                FROM
                    凭证头表 h left join 凭证行表 l on h.journal_id = l.journal_id
                WHERE
                    (h.`year`='2023' OR `h.journal_id`= 'head_main_id_202306080001')
                    AND
                    (h.`entity` IN ('A','B') OR h.`journal_id` LIKE 'head_main_id_202306080002%')


        Hint:
            - ``where`` 查询条件为空时，将返回该凭证模型下的所有数据
            - ``head_column`` 字段名必须与凭证头表上字段名保持一致，为空时，将返回凭证头表上所有字段
                            (不管是否指定了返回字段，其中 journal_id 字段一定会返回)
            - ``line_column`` 字段名必须与凭证行表上字段名保持一致，为空时，将返回凭证行表上所有字段
                            (不管是否指定了返回字段，其中 journal_id 和 line_no 字段一定会返回)
            - ``sort_config`` 默认按journal_id和line_no 升序，type 为空时，默认按ASC排序

        """
        where_str = None
        if where is not None:
            where_str = self._parse_where(where)
        model_data = ModelDataQueryVO(
            elementName=self.element_info.elementName,
            folderId=self.element_info.folderId,
            whereStr=where_str,
            headQueryCols=head_column,
            lineQueryCols=line_column,
            sortConfig=sort_config
        )
        res = await self.async_api.journal_model_data.query(model_data)
        head_table_name = self.config.logicTable.dataTableInfo.name
        line_table_name = self.config.logicTable.children[0].dataTableInfo.name
        return pd.DataFrame(res[head_table_name]), pd.DataFrame(res[line_table_name])

    async def posting(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
        """凭证数据过账

        Args:
            where: 筛选条件 （格式 可参考 数据表（DataTableMySQL）的条件格式）

        .. admonition:: 示例

            .. code-block:: python

                # 创建凭证组件元素对象
                journal = JournalModel(element_name="ZHY_TEST_0613_02")
                t = journal.table
                # 筛选条件 （格式 可参考 数据表（DataTableMySQL）的条件格式，& 表示 and，| 表示 or）
                where = (
                        ((t.year == '2023') | (t.journal_id == 'head_main_id_202306080001'))
                        &
                        (t.entity.isin(['A','B']) | t.journal_id.like('head_main_id_202306080002%'))
                )
                journal.posting(where)

        Hint:

            - 如果过账成功，则会将凭证头表上的post_status字段的值改为'true'，失败则不改

        """
        where_str = None
        if where is not None:
            where_str = self._parse_where(where)
        param = JmPostParamVO(
            elementName=self.element_info.elementName,
            folderId=self.element_info.folderId,
            whereStr=where_str
        )
        resp = await self.async_api.journal_model_data.posting(param)
        if not resp.success:
            raise JournalModelPostingError(
                f"Error occurs while posting journal model.\n"
                f"Detail: {resp}"
            )
        return resp

    async def cancel_post(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
        """凭证数据取消过账

        Args:
            where: 筛选条件 （格式 可参考 数据表（DataTableMySQL）的条件格式）

        .. admonition:: 示例

            .. code-block:: python

               journal = JournalModel(element_name="ZHY_TEST_0613_02")
                t = journal.table
                # 筛选条件 （格式 可参考 数据表（DataTableMySQL）的条件格式，& 表示 and，| 表示 or）
                where = (
                        ((t.year == '2023') | (t.journal_id == 'head_main_id_202306080001'))
                        &
                        (t.entity.isin(['A','B']) | t.journal_id.like('head_main_id_202306080002%'))
                )
                journal.cancel_post(where)

        Hint:
            - 如果取消过账成功，则会将凭证头表上的post_status字段的值改为'false'，失败则不改

        """
        where_str = None
        if where is not None:
            where_str = self._parse_where(where)
        param = JmPostParamVO(
            elementName=self.element_info.elementName,
            folderId=self.element_info.folderId,
            whereStr=where_str,
        )
        resp = await self.async_api.journal_model_data.cancel_post(param)
        if not resp.success:
            raise JournalModelPostingError(
                f"Error occurs while posting journal model.\n"
                f"Detail: {resp}"
            )
        return resp


class JournalModel(AsyncJournalModel, metaclass=SyncMeta):
    synchronize = (
        "save",
        "save",
        "update",
        "delete",
        "query",
        "posting",
        "cancel_post"
    )
    if TYPE_CHECKING:  # pragma: no cover
        def save(
            self,
            head_df: pd.DataFrame,
            line_df: pd.DataFrame,
            callback: Union[Dict, CallbackInfo] = None,
            relation_field: str = 'journal_id',
            enable_create: bool = True,
            enable_default_value: bool = False,
            enable_repeat_check: bool = True,
            enable_required: bool = False,
            enable_valid_range: bool = True,
            enable_all_errors: bool = True,
            enable_need_one_line: bool = True,
            sync: bool = False
        ) -> CommonResultDTO:
            ...

        def update(
            self,
            head_df: pd.DataFrame,
            line_df: pd.DataFrame,
            callback: Union[Dict, CallbackInfo] = None,
            relation_field: str = 'journal_id',
            enable_create: bool = True,
            enable_default_value: bool = False,
            enable_repeat_check: bool = True,
            enable_required: bool = False,
            enable_valid_range: bool = True,
            enable_all_errors: bool = True,
            enable_need_one_line: bool = True,
            header_operate: Literal['EDIT', 'DELETE_ADD'] = 'EDIT',
            line_operate: Literal['EDIT', 'ADD', 'DELETE', 'DELETE_ADD'] = 'EDIT',
        ) -> CommonResultDTO:
            ...

        def check(self, where: Union[str, Term, EmptyCriterion]) -> JmPostResultVO:
            ...

        def delete(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
            ...

        def posting(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
            ...

        def cancel_post(self, where: Union[str, Term, EmptyCriterion]) -> CommonResultDTO:
            ...

        def query(
                self,
                where: Union[str, Term, EmptyCriterion] = None,
                head_column: List[str] = None,
                line_column: List[str] = None,
                sort_config: List[JournalSortConfig] = None
        ) -> Tuple[pd.DataFrame, pd.DataFrame]:
            ...
