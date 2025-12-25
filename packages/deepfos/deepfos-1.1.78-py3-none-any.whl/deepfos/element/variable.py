from enum import Enum
from typing import List, Dict, Union, Any, Callable, TYPE_CHECKING, Optional
import pandas as pd
import datetime

from pydantic import Field

from deepfos.api.models.variable import VariableValueDTO, VariableVO, UpdateVariavlesDTO, ValueTypeMapDTO, \
    BaseElementDetail
from deepfos.api.variable import VariableAPI
from deepfos.element.base import ElementBase, SyncMeta
from deepfos.element.dimension import Dimension
from deepfos.element.smartlist import SmartList
from deepfos.exceptions import VariableUpdateError, VariableCreateError
from deepfos.lib.utils import Group, GroupDict
from deepfos.lib.constant import UNSET
from deepfos.lib.asynchronous import future_property


__all__ = [
    'Variable',
    'AsyncVariable',
    'DateType'
]


class GlobalVariable(VariableValueDTO):
    description: Optional[Dict] = {'zh-cn': None, 'en': None}
    scope: int = 1
    status: bool = True


class UserVariable(VariableValueDTO):
    description: Optional[Dict] = {'zh-cn': None, 'en': None}
    scope: int = 2
    status: bool = True


class VariableTypeId(int, Enum):
    #: TEXT - 文本
    TEXT = 1
    #: NUMBER - 数字
    NUMBER = 15
    #: SML - 值列表
    SML = 3
    #: DIM - 维度
    DIM = 8
    #: DATE - 日期时间
    DATE = 11
    #: CUSTOM_LIST - 自定义列表
    CUSTOM_LIST = 13


class DateType(str, Enum):
    #: 年
    year = "1"
    #: 年月
    year_month = "2"
    #: 年月日
    year_month_day = "3"
    #: 年月日时间
    year_month_day_time = "4"


class TextValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.TEXT
    valueKey: str = "1"
    #: 文本长度
    length: int = 255


class NumberValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.NUMBER
    #: 整数长度
    maxLen: Optional[int] = None
    #: 小数长度
    digitLen: Optional[int] = None
    #: 允许等于最小值
    minEqual: bool = True
    #: 最小值
    minimun: Optional[int] = None
    #: 允许等于最大值
    maxEqual: bool = True
    #: 最大值
    maximun: Optional[int] = None
    #: 是否显示为百分比
    percentage: bool = False


class SmartListValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.SML
    #: 元素详情(由smartlist提取后的元素信息)
    elementDetail: Optional[BaseElementDetail] = None
    #: 值列表元素名称
    valueKey: Optional[str] = None
    #: 是否选择多个值列表成员
    selectedMulti: bool = False
    #: 多选值列表的成员值列表
    valueField: List[str] = Field(default_factory=list)
    #: 多选成员数上限
    multipleChoiceLimit: Optional[int] = None


class DimensionValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.DIM
    #: 元素详情(由Dimension提取后的元素信息)
    elementDetail: Optional[BaseElementDetail] = None
    #: 维度元素名称
    dimensionName: Optional[str] = None
    #: 维度表达式
    valueKey: Optional[str] = None
    #: 是否选择多个值列表成员
    selectedMulti: bool = False
    #: 多选成员数上限
    multipleChoiceLimit: Optional[int] = None


class DateValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.DATE
    #: 对应年份格式的编号字符串
    valueKey: str = DateType.year_month_day_time


class CustomListValueMap(ValueTypeMapDTO):
    #: 变量类型代码
    valueType: int = VariableTypeId.CUSTOM_LIST
    #: 自定义列表表达式(多个值请用“,”分开。示例: 1,2,3)
    valueKey: Optional[str] = None
    #: 是否选择多个值列表成员
    selectedMulti: bool = False
    #: 多选成员数上限
    multipleChoiceLimit: Optional[int] = None


# -----------------------------------------------------------------------------
# typing
T_Number = Union[int, float]
T_Date = Union[pd.Timestamp, datetime.datetime, str]
T_Variable = Union[GlobalVariable, UserVariable]
T_VarValue = Union[T_Number, T_Date, List[str]]


def value_adaptor(var_type: int) -> Callable[[Any], str]:
    if var_type == VariableTypeId.DATE:
        def handle(value: T_Date):
            if not isinstance(value, str):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            return value
    elif var_type == VariableTypeId.NUMBER:
        def handle(value: T_Number):
            return str(value)
    else:
        def handle(value: Union[str, List[str]]):
            if isinstance(value, list):
                value = ','.join(map(str, value))
            return value

    def guard_none_handle(value):
        if value is None:
            return value
        else:
            return handle(value)

    return guard_none_handle


# -----------------------------------------------------------------------------
# core
class AsyncVariable(ElementBase[VariableAPI]):
    """变量

    为了防止将变量元素本身与变量元素保存的变量值混淆。在本节文档中，
    将变量元素称为 **“变量”** ，各变量值称为 **“变量成员”** 或简称为 **“成员”**。
    """
    def __init__(
        self,
        element_name: str,
        folder_id: str = None,
        path: str = None,
        server_name: str = None,
    ):
        self.__group = Group()
        self.__description = None
        self.__gv_memo = None
        self.__uv_memo = None
        super().__init__(element_name=element_name, folder_id=folder_id, path=path, server_name=server_name)

    @property
    def _group(self) -> Group:
        if self.__gv_memo is None:
            _ = self._gv_memo
        if self.__uv_memo is None:
            _ = self._uv_memo
        return self.__group

    @property
    def _gv_memo(self) -> GroupDict[str, GlobalVariable]:
        if self.__gv_memo is None:
            self.__gv_memo = GroupDict(self.__group)
            for gv in self.meta.globalVariables:
                self.__gv_memo[gv.name] = gv

        return self.__gv_memo

    @property
    def _uv_memo(self) -> GroupDict[str, UserVariable]:
        if self.__uv_memo is None:
            self.__uv_memo = GroupDict(self.__group)
            for uv in self.meta.userVariables:
                self.__uv_memo[uv.name] = uv

        return self.__uv_memo

    @property
    def _description(self) -> Dict[str, str]:
        if not self.__description:
            self.__description = self.meta.description

        return self.__description

    @future_property
    async def meta(self) -> VariableVO:
        """系统中的变量列表的元数据信息"""
        api = await self.wait_for('async_api')
        ele_info = await self.wait_for('element_info')
        return await api.variable.query(
            folderId=ele_info.folderId,
            elementName=ele_info.elementName,
        )

    def __getitem__(self, name: str) -> T_VarValue:
        """
        根据变量成员名获取成员值

        当为用户变量时，返回自定义变量

        Args:
            name: 变量成员名

        Returns:
            变量的值

        See Also:
            - :meth:`get`
            - :meth:`get_value`

        """
        return self.get_value(name, is_customize_value=True)

    def get(self, name: str, default: str = None) -> T_VarValue:
        """
        根据变量成员名获取成员值

        当为用户变量时，返回自定义变量

        Args:
            name: 变量成员名
            default: 变量名不存在时的默认值

        Returns:
            变量的值

        See Also:
            :meth:`get_value`

        """
        return self.get_value(name, is_customize_value=True, default=default)

    @staticmethod
    def _maybe_list(value, cast: Callable[[str], Any] = None):
        if not value:
            return value
        if cast is None:
            cast = lambda x: x
        if len(val_list := value.split(',')) == 1:
            return cast(val_list[0])
        return [cast(val) for val in val_list]

    def get_value(
        self,
        name: str,
        is_customize_value: bool = True,
        default: Any = UNSET,
        auto_cast: bool = True,
        obj_hook: Callable[[str], Any] = None
    ) -> T_VarValue:
        """
        根据变量成员名获取成员值

        Args:
            name: 变量成员名
            is_customize_value: 是否为用户变量时配置的自定义值，在获取用户变量时会查看该值
            default: 变量不存在时的默认值
            auto_cast: 是否对变量值做自动转换
            obj_hook: 自定义的变量转换函数


        .. admonition:: 示例

            例如变量成员 ``ctm_list`` 为自定义列表，存的值为1，2，3。
            在使用默认参数的情况下，此方法将返回 ['1', '2', '3']。

            如果希望返回整数列表[1, 2, 3]，可以传入 ``obj_hook`` 使用自定义逻辑

            .. code-block:: python

                var = Variable('test_var')

                def hook(value):
                    return [int(v) for v in value.split(',')]

                var.get_value('ctm_list', obj_hook=hook)

        Returns:
            变量的值
        """
        if name in self._gv_memo:
            var = self._gv_memo[name]
            is_customize_value = False
        elif name in self._uv_memo:
            var = self._uv_memo[name]
        elif default is UNSET:
            raise KeyError(f"Variable : {name} not exist.")
        else:
            return default

        value = var.userValue if is_customize_value else var.value

        if obj_hook is not None:
            return obj_hook(value)

        # 启用维度表达式的维度变量应直接取原值
        if var.valueType == VariableTypeId.DIM and not var.valueTypeMap.selectedMulti:
            return value

        if not auto_cast:
            cast = None
        elif var.valueType == VariableTypeId.NUMBER:
            cast = float
        elif var.valueType == VariableTypeId.DATE:
            cast = pd.to_datetime
        else:
            cast = None

        return self._maybe_list(value, cast)

    def __setitem__(self, key: str, value: T_VarValue):
        """更新变量成员的值

        根据变量名称与变量值，更新变量的值。全局变量时即为变量的值，

        """
        self.update_value(key, value, is_customize_value=True)

    def update_value(
        self,
        name: str,
        update_value: T_VarValue,
        is_customize_value: bool = True
    ):
        """更新变量成员的值

        根据变量名称与变量值，更新变量的值。全局变量时即为变量的值，
        用户变量时即为自定义值，为用户变量默认值时，需置 ``is_customize_value`` 为
        ``False``

        Args:
            name: 变量成员名称
            update_value: 需更新的值
            is_customize_value: 是否更新自定义值（仅对用户变量生效）
        """
        variable = self.get_variable(name)
        value = value_adaptor(variable.valueType)(update_value)

        if is_customize_value and name in self._uv_memo:
            variable.userValue = value
        else:
            variable.value = value

    async def save(self):
        """
        保存变量

        将当前元素内变量信息保存至系统
        """
        payload = UpdateVariavlesDTO.construct_from(
            self.meta, description=self._description,
            globalVariables=list(self._gv_memo.values()),
            userVariables=list(self._uv_memo.values()),
            moduleId=self.api.module_id
        )
        return await self._update_impl(payload=payload)

    async def _update_impl(self, payload: UpdateVariavlesDTO):
        await self.async_api.variable.update(payload)
        # 使memo的缓存失效
        self.__gv_memo = None
        self.__uv_memo = None
        self.__description = None
        self.__group.clear()
        # 使meta重置
        self.__class__.meta.reset(self)

    @property
    def variables(self) -> Dict[str, T_Variable]:
        """
        所有变量成员

        Returns:
            以name为键名，Variable为内容的字典
        """
        all_variable = {}
        if self._gv_memo:
            all_variable.update(self._gv_memo)
        if self._uv_memo:
            all_variable.update(self._uv_memo)
        return all_variable

    def get_variable(self, name: str) -> T_Variable:
        """
        根据变量成员名获取成员

        Args:
            name: 变量成员名

        Returns:
            GlobalVariable或UserVariable类型的对象
        """
        if name in self._gv_memo:
            return self._gv_memo[name]
        elif name in self._uv_memo:
            return self._uv_memo[name]
        else:
            raise KeyError(f"Variable : {name} not exist.")

    def _add_variable(
        self,
        name: str,
        value_map: Union[
            TextValueMap, NumberValueMap, SmartListValueMap,
            DimensionValueMap, DateValueMap, CustomListValueMap
        ],
        value: Union[str, List[str]],
        description: Dict[str, str],
        is_global: bool,
        is_customize_value: bool
    ):
        """新增单个变量

        Args:
            name: 变量成员名
            value_map: 变量类型
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
        """
        if name in self._group.keys():
            raise VariableCreateError(f"Variable: {name} already exist. "
                                      "Please use update instead.")
        if is_global:
            self._gv_memo[name] = variable = \
                GlobalVariable(
                    name=name,
                    valueType=value_map.valueType,
                    valueTypeMap=value_map
                )
        else:
            self._uv_memo[name] = variable = \
                UserVariable(
                    name=name,
                    valueType=value_map.valueType,
                    valueTypeMap=value_map
                )

        if description:
            variable.description = description

        if value:
            self.update_value(name, value, is_customize_value)

    def add_text(
        self,
        name: str,
        value: Union[str, List[str]] = None,
        description: Dict[str, str] = None,
        is_global: bool = False,
        is_customize_value: bool = True,
        length: int = 255
    ):
        """新增单个文本变量成员

        Args:
            name: 变量成员名
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
            length: 文本长度

        """
        value = value_adaptor(VariableTypeId.TEXT)(value)
        value_map = TextValueMap(length=length)
        self._add_variable(name=name, value_map=value_map, value=value,
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def add_number(
        self,
        name: str,
        value: T_Number = None,
        description: Dict[str, str] = None,
        is_global: bool = False,
        is_customize_value: bool = True,
        int_length: int = 13,
        digit_length: int = 6,
        min_equal: bool = True,
        minimun: int = None,
        max_equal: bool = True,
        maximun: int = None,
        percentage: bool = False
    ):
        """新增单个数字变量成员

        Args:
            name: 变量成员名
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
            int_length: 整数长度
            digit_length: 小数长度
            min_equal: 允许等于最小值
            minimun: 最小值
            max_equal: 允许等于最大值
            maximun: 最大值
            percentage: 是否显示为百分比

        """
        value = value_adaptor(VariableTypeId.NUMBER)(value)
        value_map = NumberValueMap(maxLen=int_length, digitLen=digit_length, minEqual=min_equal, minimun=minimun,
                                   maxEqual=max_equal, maximun=maximun, percentage=percentage)
        self._add_variable(name=name, value_map=value_map, value=str(value),
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def add_smartlist(
        self,
        name: str,
        smart_list: SmartList,
        value: Union[str, List[str]] = None,
        description: Dict[str, str] = None,
        is_global: bool = False,
        is_customize_value: bool = True,
        selected_multi: bool = False,
        multi_member_list: List[str] = None,
        multiple_choice_limit: int = None
    ):
        """新增单个值列表变量成员

        Args:
            name: 变量成员名
            smart_list: 值列表对象（必填）
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
            selected_multi: 是否选择多个值列表成员
            multi_member_list: 多选值列表的成员值列表
            multiple_choice_limit: 多选成员数上限
        """
        if multi_member_list is None:
            multi_member_list = []

        value = value_adaptor(VariableTypeId.SML)(value)

        element_detail = BaseElementDetail.construct_from(smart_list.element_info, elementType="SML")
        value_map = SmartListValueMap(elementDetail=element_detail,
                                      valueKey=smart_list.element_info.elementName,
                                      selectedMulti=selected_multi,
                                      valueField=multi_member_list,
                                      multipleChoiceLimit=multiple_choice_limit)

        self._add_variable(name=name, value_map=value_map, value=value,
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def add_dimension(
        self,
        name: str,
        dim: Dimension,
        dim_expression: str,
        value: Union[str, List[str]] = None,
        description: Dict[str, str] = None,
        is_global: bool = False,
        is_customize_value: bool = True,
        selected_multi: bool = False,
        multiple_choice_limit: int = None
    ):
        """新增单个维度变量成员

        Args:
            name: 变量成员名
            dim: 维度对象（必填）
            dim_expression: 维度表达式（必填）
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
            selected_multi: 是否选择多个值列表成员
            multiple_choice_limit: 多选成员数上限
        """

        value = value_adaptor(VariableTypeId.DIM)(value)
        element_detail = BaseElementDetail.construct_from(dim.element_info, elementType="DIM")
        value_map = DimensionValueMap(elementDetail=element_detail,
                                      dimensionName=dim.element_info.elementName,
                                      valueKey=dim_expression,
                                      selectedMulti=selected_multi,
                                      multipleChoiceLimit=multiple_choice_limit)

        self._add_variable(name=name, value_map=value_map, value=value,
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def add_date(
        self,
        name: str,
        date_format: str = DateType.year_month_day_time,
        value: T_Date = None,
        description: Dict[str, str] = None,
        is_global: bool = False,
        is_customize_value: bool = True
    ):
        """新增单个日期变量成员

        Args:
            name: 变量成员名
            value: 变量值
            date_format: 对应年份格式的编号（必填，建议使用枚举类DateType的值）
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值

        """
        value = value_adaptor(VariableTypeId.DATE)(value)
        value_map = DateValueMap(valueKey=date_format)
        self._add_variable(name=name, value_map=value_map, value=value,
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def add_custom_list(
        self,
        name: str,
        custom_list: List[Union[int, float]],
        value: Union[str, List[str]] = None,
        description: Dict[str, str] = None,
        is_global: bool = False, 
        is_customize_value: bool = True,
        selected_multi: bool = False,
        multiple_choice_limit: int = None
    ):
        """新增单个自定义列表变量成员

        Args:
            name: 变量成员名
            custom_list: 自定义列表
            value: 变量值
            description: 变量描述
            is_global: 是否为全局变量
            is_customize_value: 值是否为用户变量时配置的自定义值
            selected_multi: 是否选择多个值列表成员
            multiple_choice_limit: 多选成员数上限

        """
        value = value_adaptor(VariableTypeId.CUSTOM_LIST)(value)
        list_expr = ','.join(map(str, custom_list))
        value_map = CustomListValueMap(valueKey=list_expr,
                                       selectedMulti=selected_multi,
                                       multipleChoiceLimit=multiple_choice_limit)
        self._add_variable(name=name, value_map=value_map, value=value,
                           description=description,
                           is_customize_value=is_customize_value,
                           is_global=is_global)

    def _update_valuetype(
        self,
        name,
        value_map: Union[
            TextValueMap, NumberValueMap, SmartListValueMap,
            DimensionValueMap, DateValueMap, CustomListValueMap]
    ):
        """根据变量名称与变量值，更新变量的变量类型(逻辑属性)

        Args:
            name: 变量成员名
            value_map: 变量类型(逻辑属性)
        """
        variable = self.get_variable(name)
        variable.valueType = value_map.valueType
        variable.valueTypeMap = value_map

    def update_description(
        self,
        name: str,
        en_description: str = None,
        zh_cn_description: str = None
    ):
        """根据变量成员名称，更新变量成员的描述

        Args:
            name: 变量成员名
            en_description: 变量英文描述
            zh_cn_description: 变量中文描述
        """
        description = {'zh-cn': zh_cn_description, 'en': en_description}
        variable = self.get_variable(name)
        variable.description = description

    def delete_variables(self, *name: str, silent: bool = True):
        """删除变量成员

        根据变量成员名列表删除多个变量

        Args:
            *name: 变量成员名
            silent: 当变量不存在时，是报错还是静默处理。默认True, 即静默处理。
        """
        not_exist = []
        for n in name:
            if n in self._gv_memo:
                del self._gv_memo[n]
            elif n in self._uv_memo:
                del self._uv_memo[n]
            else:
                not_exist.append(n)
        if not_exist and not silent:
            raise VariableUpdateError(f"Variable: {not_exist} not exist.")

    def __contains__(self, item):
        return item in self._group.keys()

    def __len__(self):
        return len(self._group.keys())


class Variable(AsyncVariable, metaclass=SyncMeta):
    synchronize = ('save', )

    if TYPE_CHECKING:  # pragma: no cover
        def save(self):
            ...
