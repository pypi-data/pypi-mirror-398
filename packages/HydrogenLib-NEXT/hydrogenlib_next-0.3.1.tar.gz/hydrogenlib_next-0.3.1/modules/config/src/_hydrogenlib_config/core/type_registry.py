from typing import Callable, overload

from _hydrogenlib_core.utils import InstanceMapping

type Validator[T, R] = Callable[[T], R]


class TypeRegistry:
    def __init__(self):
        self._registry = InstanceMapping()  # type: InstanceMapping[type, InstanceMapping[type, Validator]]
        self._validators_no_from_type = InstanceMapping()

    def register(self, from_type: type | None, to_type: type, validator: Validator) -> None:
        if from_type is None:
            self._validators_no_from_type[to_type] = validator

        if from_type not in self._registry:
            self._registry[from_type] = InstanceMapping()

        if to_type is None:
            return None

        self._registry[from_type][to_type] = validator

    def exists(self, from_type: type, to_type: type) -> bool:
        return from_type in self._registry and to_type in self._registry[from_type]

    def validator(self, from_type: type, to_type: type) -> Validator:
        try:
            return self._registry[from_type][to_type]
        except KeyError:
            return self._validators_no_from_type[to_type]

    def validate(self, data: object, target: type):
        return self.validator(type(data), target)(data)

    # Decorators
    @overload
    def add_validator[FT, TT](self, *, from_: FT = None, to: TT) -> Callable[
        [Callable[[FT], TT]],
        Callable[[FT], TT]
    ]:
        ...

    @overload
    def add_validator[FT, TT](self, func: Callable[[FT], TT]) -> Callable[[FT], TT]:
        ...

    def add_validator(self, func=None, *, from_=None, to=None):
        def decorator(fnc):
            self.register(from_, to, func)
            return func

        return decorator if func is None else decorator(func)
