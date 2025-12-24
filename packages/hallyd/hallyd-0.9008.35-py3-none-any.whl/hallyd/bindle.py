#  SPDX-FileCopyrightText: © 2021 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
"""
Serialization and deserialization.

It provides support for primitive data types, dicts, lists, enums and some classes.

Any class could either be serializable as it is (basically if it provides a property for each constructor parameter),
or could be adapted by adding :code:`__to_json_dict__()` and (static) :code:`__from_json_dict__(d)` methods to it.
"""
import base64
import datetime
import enum
import functools
import importlib
import inspect
import json
import pathlib
import typing as t


def loads(sj: t.AnyStr, *, type_whitelist: t.Iterable[str] | None = None) -> t.Any:
    """
    Deserialize an object from a string. See also dumps() and load().
    """
    type_whitelist = None if type_whitelist is None else set(type_whitelist)
    return json.loads(sj, object_hook=functools.partial(_deserialize_object_json_loads_object_hook, type_whitelist))


def dumps(obj: t.Any) -> str:
    """
    Serialize an object to a string. See also loads().
    """
    return json.dumps(obj, default=_serialize_object_json_dumps_default, sort_keys=True, indent=1)


def load(fp: t.IO, *, type_whitelist: t.Iterable[str] | None = None) -> t.Any:
    """
    Deserialize an object from a file object. See also dump() and loads().
    """
    type_whitelist = None if type_whitelist is None else set(type_whitelist)
    return json.load(fp, object_hook=functools.partial(_deserialize_object_json_loads_object_hook, type_whitelist))


def dump(obj: t.Any, fp: t.IO) -> None:
    """
    Serialize an object to a file object. See also load().
    """
    return json.dump(obj, fp, default=_serialize_object_json_dumps_default, sort_keys=True, indent=1)


def _serialize_object_json_dumps_default(obj):
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        pass

    if obj is None:
        return None
    if isinstance(obj, pathlib.Path):
        return {_TYPE_KEY: ["hallyd.fs", "Path"], "s": str(obj)}
    if isinstance(obj, datetime.datetime):
        return {_TYPE_KEY: [__name__, _new_datetime_datetime.__qualname__], "timestamp": obj.timestamp()}
    if isinstance(obj, datetime.timedelta):
        return {_TYPE_KEY: [__name__, _new_datetime_timedelta.__qualname__], "seconds": obj.total_seconds()}
    if isinstance(obj, bytes):
        return {_TYPE_KEY: [__name__, _new_bytes.__qualname__], "b64str": base64.b64encode(obj).decode()}
    if isinstance(obj, enum.Enum):
        return {
            _TYPE_KEY: [__name__, _enum.__qualname__],
            "enum_type": (type(obj).__module__, type(obj).__qualname__),
            "name": obj.name,
        }
    if isinstance(obj, set):
        return {_TYPE_KEY: [__name__, _new_set.__qualname__], "items": list(obj)}
    if isinstance(obj, functools.partial):
        return {
            _TYPE_KEY: [__name__, _new_functools_partial.__qualname__],
            "func": obj.func,
            "args": obj.args,
            "kwargs": obj.keywords,
        }
    if hasattr(obj, "__qualname__"):
        return {
            _TYPE_KEY: [__name__, _by_qualname.__qualname__],
            "module": obj.__module__,
            "qualname": obj.__qualname__,
        }
    to_json_dict_func = getattr(obj, "__to_json_dict__", None)
    if to_json_dict_func:
        obj_dict = to_json_dict_func()
    else:
        obj_dict = {}
        non_existent = object()
        for obj_init_param in inspect.signature(type(obj)).parameters.values():
            if obj_init_param.kind == inspect.Parameter.VAR_KEYWORD:
                raise SerializingError("objects whose __init__() has 'kwargs' cannot be serialized")
            value = getattr(obj, obj_init_param.name, non_existent)
            if value is not non_existent:
                obj_dict[obj_init_param.name] = value
        obj_dict = _filter_unneeded_dict_entries(type(obj), obj_dict)
    return {_TYPE_KEY: [type(obj).__module__, type(obj).__qualname__], **obj_dict}


def _deserialize_object_json_loads_object_hook(type_whitelist, dict_):
    type_module_name, type_qualified_name = dict_.pop(_TYPE_KEY, (None, None))
    if type_qualified_name:
        type_full_name = f"{type_module_name}.{type_qualified_name}"
        if type_whitelist is not None and type_full_name not in type_whitelist:
            raise RuntimeError(f"type not whitelisted: {type_full_name}")

        kwargs = dict_
        obj_type = importlib.import_module(type_module_name)
        for name_piece in type_qualified_name.split("."):
            obj_type = getattr(obj_type, name_piece, None)
            if not obj_type:
                raise SerializingError(f"unable to find type: {type_full_name}")
        from_json_dict_func = getattr(obj_type, "__from_json_dict__", None)
        if from_json_dict_func:
            return from_json_dict_func(kwargs)
        args = []
        for obj_init_param in inspect.signature(obj_type).parameters.values():
            if obj_init_param.kind in [inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY]:
                args.append(kwargs.pop(obj_init_param.name))
            if obj_init_param.kind == inspect.Parameter.VAR_POSITIONAL:
                args += kwargs.pop(obj_init_param.name)
        # noinspection PyCallingNonCallable
        return obj_type(*args, **kwargs)
    return dict_


def _new_datetime_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


def _new_datetime_timedelta(seconds):
    return datetime.timedelta(seconds=seconds)


def _new_bytes(b64str):
    return base64.b64decode(b64str)


def _new_set(items):
    return set(items)


def _new_functools_partial(func, args, kwargs):
    return functools.partial(func, *args, **kwargs)


def _by_qualname(module, qualname):
    obj_type = importlib.import_module(module)
    for name_piece in qualname.split("."):
        obj_type = getattr(obj_type, name_piece, None)
        if not obj_type:
            raise SerializingError(f"unable to find type '{module}.{qualname}'")
    return obj_type


def _enum(enum_type, name):
    obj_type = importlib.import_module(enum_type[0])
    for name_piece in enum_type[1].split("."):
        obj_type = getattr(obj_type, name_piece, None)
        if not obj_type:
            raise SerializingError(f"unable to find type '{enum_type[0]}.{enum_type[1]}'")

    return getattr(obj_type, name)


def _filter_unneeded_dict_entries(obj_type, obj_dict: dict) -> dict:
    init_param_names = [obj_init_param.name for obj_init_param in inspect.signature(obj_type).parameters.values()]
    return {key: value for key, value in obj_dict.items() if key in init_param_names}


_TYPE_KEY = "$_hallyd_type"


class SerializingError(ValueError):
    pass
