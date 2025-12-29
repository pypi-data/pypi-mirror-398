from typing import Any, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta


class FieldType:
    UNKNOWN = 0
    STRING = 1
    INT = 2
    BOOL = 3
    FLOAT = 4
    TIME = 5
    DURATION = 6
    ERROR = 7


@dataclass
class Field:
    name: str
    value: Any
    field_type: int

    @classmethod
    def String(cls, key: str, val: str) -> "Field":
        return cls(key, val, FieldType.STRING)

    @classmethod
    def Int(cls, key: str, val: int) -> "Field":
        return cls(key, val, FieldType.INT)

    @classmethod
    def Bool(cls, key: str, val: bool) -> "Field":
        return cls(key, val, FieldType.BOOL)

    @classmethod
    def Float(cls, key: str, val: float) -> "Field":
        return cls(key, val, FieldType.FLOAT)

    @classmethod
    def Time(cls, key: str, val: datetime) -> "Field":
        return cls(key, val, FieldType.TIME)

    @classmethod
    def Duration(cls, key: str, val: timedelta) -> "Field":
        return cls(key, val, FieldType.DURATION)

    @classmethod
    def Error(cls, val: Exception) -> "Field":
        return cls("error", val, FieldType.ERROR)

    @classmethod
    def Any(cls, key: str, val: Any) -> "Field":
        return cls(key, val, FieldType.UNKNOWN)


def expand_fields(fields: tuple) -> Dict[str, Any]:
    """
    Expands a tuple of Field objects into a dictionary for logging.
    """
    result = {}
    for f in fields:
        if isinstance(f, Field):
            result[f.name] = f.value
    return result
