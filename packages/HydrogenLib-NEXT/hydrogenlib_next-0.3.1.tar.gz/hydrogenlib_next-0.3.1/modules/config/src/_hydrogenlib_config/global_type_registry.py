import datetime

from . import core
from _hydrogenlib_core.typefunc import builtin_types


global_type_registry = core.type_registry.TypeRegistry()


def registry_self_validating_type(typ: type | list[type]):
    if isinstance(typ, list):
        for i in typ:
            registry_self_validating_type(i)

    global_type_registry.register(None, typ, typ)
    return typ


registry_self_validating_type(
    list(builtin_types)
)

@global_type_registry.add_validator(to=datetime.datetime)
def datetime_validator(value):
    if isinstance(value, str):
        return datetime.datetime.fromisoformat(value)
    elif isinstance(value, datetime.datetime):
        return value
    elif isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value)

    raise ValueError(f"Invalid datetime type: {type(value)}")

@global_type_registry.add_validator(to=datetime.date)
def date_validator(value):
    if isinstance(value, str):
        return datetime.date.fromisoformat(value)
    elif isinstance(value, datetime.date):
        return value
    elif isinstance(value, (int, float)):
        return datetime.date.fromtimestamp(value)

    raise ValueError(f"Invalid datetype: {type(value)}")


global_type_registry.add_validator(to=object)(
    lambda x: x  # 这玩意有啥好验证的
)
