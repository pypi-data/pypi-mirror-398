from deepfos.lib.utils import to_version_tuple
import pydantic

from typing import Any, Dict, TypeVar, Type
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic import parse_obj_as

Pydantic_V2 = False
if to_version_tuple(pydantic.__version__, max_split=2) > (2, 0, 0):
    from pydantic import TypeAdapter
    Pydantic_V2 = True
else:
    TypeAdapter = None

__all__ = [
    "BaseModel",
    "compat_parse_obj_as",
]

T = TypeVar('T')


class BaseModel(PydanticBaseModel):

    if Pydantic_V2:
        model_config = ConfigDict(from_attributes=True)

    @classmethod
    def construct_from(cls, *models: 'BaseModel', **extra):
        """
        基于PydanticBaseModel.contruct，删除不在_fields_set中的属性
        """
        attrs = {}
        if Pydantic_V2:
            fields_set = set(cls.model_fields.keys())
            for m in models:
                attrs.update({
                    k: getattr(m, k)
                    for k in (m.model_fields_set & fields_set)
                })
        else:
            fields_set = set(cls.__fields__.keys())
            for m in models:
                attrs.update({
                    k: getattr(m, k)
                    for k in (m.__fields_set__ & fields_set)
                })
        attrs.update({
            k: extra[k] for
            k in (fields_set & extra.keys())
        })
        if Pydantic_V2:
            return cls.model_construct(fields_set, **attrs)
        return cls.construct(fields_set, **attrs)

    @classmethod
    def update_forward_refs(cls) -> None:
        if Pydantic_V2:
            return cls.model_rebuild(force=True)
        return super().update_forward_refs()

    def dict(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        if Pydantic_V2:
            return self.model_dump(**kwargs)
        return super().dict(**kwargs)


def compat_parse_obj_as(cls: Type[T], data: Any) -> T:
    if Pydantic_V2:
        return TypeAdapter(cls).validate_python(data)
    return parse_obj_as(cls, data)
