import json
from typing import OrderedDict, Any

from _hydrogenlib_core.typefunc import is_function
from _hydrogenlib_core.typefunc import iter_annotations
from .field import FieldInfo, Field


class ConfigBase:
    __config_fields__: OrderedDict[str, Field]
    __config_type_registry__ = 'global'

    def __init_subclass__(cls, **kwargs):
        middle = kwargs.get('middle', False)
        if middle:
            return

        for name, anno, value in iter_annotations(cls):
            # 构造描述符
            if isinstance(value, FieldInfo):
                field_info = value
            elif is_function(value):
                field_info = FieldInfo(
                    name, anno, default_factory=value
                )
            else:
                field_info = FieldInfo(
                    name, anno, default=value
                )

            field = Field(field_info)

            setattr(cls, name, field)
            cls.__config_fields__[name] = field

    @classmethod
    def load_from_obj(cls, obj: dict | tuple[tuple[str, Any], ...], extra='allow'):
        obj = dict(obj)
        config = cls()

        for key, value in obj:
            if key not in cls.__config_fields__ and extra == 'disallow':
                raise ValueError(f'{key} is not a valid field name')

            setattr(config, key, value)

    @classmethod
    def load_from_io(cls, io, format='json'):
        if format == 'json':
            cls.load_from_obj(
                json.load(io)
            )
        else:
            raise NotImplementedError("Formats not implemented, except 'json'")

    def to_dict(self):
        return {
            name: getattr(self, name)
            for name in self.__config_fields__
        }
