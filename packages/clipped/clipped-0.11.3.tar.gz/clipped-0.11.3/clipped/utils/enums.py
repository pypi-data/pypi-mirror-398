from enum import Enum
from typing import Iterable, List, Set, Tuple, Type, Union


def get_enum_value(e: Union[str, Enum]) -> str:
    if isinstance(e, Enum):
        return e.value
    return e


def enum_to_choices(enumeration: Type[Enum]) -> Iterable[Tuple[str, str]]:
    return tuple((e.value, e.name.lower()) for e in enumeration)


def enum_to_list(enumeration: Type[Enum]) -> List[str]:
    return [e.value for e in enumeration]


def enum_to_set(enumeration: Type[Enum]) -> Set[str]:
    return set(e.value for e in enumeration)


def values_to_choices(enumeration: Union[List, Set]) -> Iterable[Tuple[str, str]]:
    return tuple((e, e) for e in sorted(enumeration))


class EnumMixin:
    @classmethod
    def to_choices(cls) -> Iterable[Tuple[str, str]]:
        return enum_to_choices(cls)

    @classmethod
    def to_set(cls) -> Set[str]:
        return enum_to_set(cls)

    @classmethod
    def to_list(cls) -> List[str]:
        return enum_to_list(cls)

    @classmethod
    def members(cls) -> List[str]:
        return cls._member_names_


class PEnum(EnumMixin, Enum):
    pass
