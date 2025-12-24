import core


from .global_type_registry import global_type_registry


class ConfigBase(core.base.ConfigBase, middle=True):
    __config_type_registry__ = 'global'

    def __init_subclass__(cls, **kwargs):
        if kwargs.get("middle", False): return

        if cls.__config_type_registry__ == 'global':
            cls.__config_type_registry__ = global_type_registry

        super().__init_subclass__()



