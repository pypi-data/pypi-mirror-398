from collections.abc import Iterable
from typing import Any


def try_int(value: Any) -> int | None:
    ''' Convert any value to int or None (if impossible) '''
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def try_float(value: Any) -> float | None:
    ''' Convert any value to float or None (if impossible) '''
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def as_bool(value: Any) -> bool:
    ''' Return True if value like true '''
    return value in {True, '1', 'True', 'true', 't', b'1', b'True', b'true', b't'}


def to_string(val: Any) -> str:
    ''' Convert value to string '''
    if isinstance(val, bytes):
        return str(val, 'utf8', 'strict')

    if not isinstance(val, str):
        return str(val)

    return val


def to_bytes(value: bytes | str | int, encoding: str | None = None) -> bytes:
    if isinstance(value, str):
        return bytes(value, encoding or 'utf8')
    if isinstance(value, int):
        return value.to_bytes((value.bit_length() + 7) // 8, 'big')
    return value


def int_list(values: Iterable[Any]) -> list[int]:
    ''' Take list of any values and return list of integer where value is convertible '''
    return list(filter(None, map(try_int, values)))


def int_set(values: Iterable[Any]) -> set[int]:
    ''' Like int_list but return set '''
    return set(int_list(values))
