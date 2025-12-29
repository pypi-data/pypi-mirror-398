from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Sortable(Protocol):
    def __lt__(self, other: Self) -> bool: ...


class Unique:
    def __init__(self, data: Sortable) -> None:
        self.data = data

    def __lt__(self, other: Self) -> bool:
        return self.data < other.data

    def __repr__(self) -> str:
        return repr(self.data)


class Check:
    def __init__(self) -> None:
        self._value = False

    def check(self) -> None:
        self._value = True

    def uncheck(self) -> None:
        self._value = False

    def __bool__(self) -> bool:
        return self._value


class WithClearablePropertyCache:
    def clear_property_cache(self) -> None:
        """
        Invalidate all cached properties.

        (so they will be recomputed the first time they're accessed again).
        """
        cls = self.__class__
        cache = self.__dict__
        for attr in list(cache.keys()):
            if isinstance(getattr(cls, attr, None), cached_property):
                del cache[attr]


type Modifier[T] = Callable[[T], T]


@dataclass(frozen=True)
class WithAttrModifiers(ABC):
    @property
    @abstractmethod
    def _attr_modifiers(self) -> dict[str, Modifier]: ...

    def __post_init__(self) -> None:
        """
        Convert attributes of a dataclass after __init__() is called.

        object.__setattr__() is one of the awkward options (*) we have,
        when we want to set attributes in a frozen dataclass (which will raise a
        FrozenInstanceError when its own __setattr__() or __delattr__() is invoked).

        *) Another option could be to move the attributes to a super class and
        call super().__init__() here.
        """
        for name, convert in self._attr_modifiers.items():
            object.__setattr__(self, name, convert(getattr(self, name)))


class HasAttrConverters:
    def _convert_attrs(self, *args: object) -> None:
        pass


def get_class_vars[T](cls: type, *, value_type: type[T] = None) -> dict[str, T]:
    return {
        name: value
        for name, value in cls.__dict__.items()
        if not name.startswith("_")
        and (not value_type or isinstance(value, value_type))
    }
