from __future__ import annotations

import datetime
import decimal
import functools
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Union, List

import edgedb
from edgedb.introspect import introspect_object as intro
from edgedb.datatypes import datatypes


@dataclass(frozen=True)
class Context:
    frame_desc: Any = None
    query_df: bool = False


@functools.singledispatch
def serialize(o, ctx: Context = Context()):
    raise TypeError(f'无法序列化类型: {type(o)}')


@functools.singledispatch
def deserialize(o, field_info: Union[Dict, List[str], str] = None):
    raise TypeError(f'无法反序列化类型: {type(o)}')


@deserialize.register
def to_object(o: dict, field_info: Union[Dict, List[str], str] = None):
    if field_info == 'json':
        return o
    if (
        isinstance(field_info, dict)
        and len(field_info) == 1
        and field_info.get(None) == 'json'
    ):
        return o
    _id = o.pop('id', None)
    ordered_attr = o.keys()
    obj_cls = datatypes.create_object_factory(
        id='property' if _id else 'implicit',
        **{k: 'link' if isinstance(o[k], dict) else 'property' for k in ordered_attr}
    )
    actual_id = None
    if _id:
        if isinstance(_id, str):
            actual_id = uuid.UUID(_id)
        elif isinstance(_id, uuid.UUID):
            actual_id = _id
    # NB: in case of incorrect field info
    if not isinstance(field_info, dict):
        field_info = {}

    return obj_cls(
        actual_id,
        *[deserialize(o[k], field_info.get(k, {})) for k in ordered_attr]
    )


@deserialize.register
def to_set(o: list, field_info: Union[Dict, List[str], str] = None):
    if isinstance(field_info, list):
        field_info = {
            f['name']: f['type'] if f['fields'] is None else f['fields']
            for f in field_info
        }
    return [deserialize(ele, field_info) for ele in o]


@deserialize.register
def to_tuple(o: tuple, field_info: Union[Dict, List[str], str] = None):
    if isinstance(field_info, list):
        field_info = {
            f['name']: f['type'] if f['fields'] is None else f['fields']
            for f in field_info
        }
    return tuple(deserialize(ele, field_info) for ele in o)


@deserialize.register(int)
@deserialize.register(float)
@deserialize.register(str)
@deserialize.register(bytes)
@deserialize.register(bool)
@deserialize.register(type(None))
@deserialize.register(datetime.datetime)
def to_scalar(o, field_info: Union[Dict, List[str], str] = None):
    return o


@serialize.register
def _tuple(o: edgedb.Tuple, ctx: Context = Context()):
    if ctx.frame_desc is None:
        return tuple(serialize(el) for el in o)
    return tuple(
        serialize(el, Context(frame_desc=ctx.frame_desc[idx])) 
        for idx, el in enumerate(o)
    )


@serialize.register
def _namedtuple(o: edgedb.NamedTuple, ctx: Context = Context()):
    if ctx.frame_desc is None:
        return {attr: serialize(getattr(o, attr)) for attr in dir(o)}
    return {
        attr: serialize(getattr(o, attr), Context(frame_desc=ctx.frame_desc[attr]))
        for attr in ctx.frame_desc
    }


@serialize.register
def _linkset(o: edgedb.LinkSet, ctx: Context = Context()):
    return [serialize(el, ctx) for el in o]


@serialize.register
def _link(o: edgedb.Link, ctx: Context = Context()):
    ret = {}
    if ctx.frame_desc is None:
        for lprop in dir(o):
            if lprop in {'source', 'target'}:
                continue
            ret[f'@{lprop}'] = serialize(getattr(o, lprop))

        ret.update(_object(o.target))
        return ret

    lprops = list(map(lambda x: f'@{x}', (set(dir(o)) - {'source', 'target'})))
    for field in ctx.frame_desc:
        new_ctx = Context(frame_desc=ctx.frame_desc[field])
        if field in lprops:
            ret[field] = serialize(getattr(o, field[1:]), new_ctx)
        else:
            ret[field] = serialize(getattr(o.target, field), new_ctx)
    return ret


def ignore_implicited_fields(o: edgedb.Object):
    return set(dir(o)) - {desc.name for desc in intro(o).pointers if desc.implicit}


@serialize.register
def _object(o: edgedb.Object, ctx: Context = Context()):
    ret = {}

    if ctx.frame_desc is None:
        if ctx.query_df:
            attrs = dir(o)
        else:
            attrs = ignore_implicited_fields(o)
        for attr in attrs:
            try:
                ret[attr] = serialize(o[attr])
            except (KeyError, TypeError):
                ret[attr] = serialize(getattr(o, attr))
        return ret

    ensure_one_field = ctx.query_df and len(ctx.frame_desc) == 1
    for key, value in dict(ctx.frame_desc).items():
        if isinstance(key, tuple):
            # key: (field_name, not_implicit)
            maybe_drop = ctx.frame_desc.pop(key)
            if ensure_one_field or key[1]:
                ctx.frame_desc[key[0]] = maybe_drop

    for attr in ctx.frame_desc:
        try:
            ret[attr] = serialize(o[attr], Context(frame_desc=ctx.frame_desc[attr]))
        except (KeyError, TypeError):
            ret[attr] = serialize(getattr(o, attr), Context(frame_desc=ctx.frame_desc[attr]))

    return ret


@serialize.register(edgedb.Set)
@serialize.register(edgedb.Array)
def _set(o, ctx: Context = Context()):
    return [serialize(el, ctx) for el in o]


@serialize.register(int)
@serialize.register(float)
@serialize.register(str)
@serialize.register(bytes)
@serialize.register(bool)
@serialize.register(type(None))
@serialize.register(datetime.timedelta)
@serialize.register(datetime.date)
@serialize.register(datetime.datetime)
@serialize.register(datetime.time)
@serialize.register(edgedb.RelativeDuration)
@serialize.register(uuid.UUID)
@serialize.register(decimal.Decimal)
def _scalar(o, ctx: Context = Context()):
    if ctx.frame_desc == 'std::json' and isinstance(o, str):
        return json.loads(o)
    return o


@serialize.register
def _enum(o: edgedb.EnumValue, ctx: Context = Context()):
    return str(o)
