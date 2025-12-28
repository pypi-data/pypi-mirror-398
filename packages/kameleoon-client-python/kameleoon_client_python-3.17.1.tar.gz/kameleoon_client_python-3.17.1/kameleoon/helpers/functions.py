"""Helper functions"""
import json
import sys
from enum import Enum
from typing import Dict, Any, Optional, Type, TypeVar


def load_params_from_json(json_path) -> Dict[Any, Any]:
    """Load json for a file"""
    with open(json_path, encoding="utf-8") as file:
        return json.load(file)


def get_size(obj) -> float:
    """Get size of memory used by given obj"""
    return sum([sys.getsizeof(v) + sys.getsizeof(k) for k, v in obj.items()])


E = TypeVar('E', bound=Enum)


def enum_from_literal(literal: str, enum_type: Type[E], default_value: E) -> E:
    """
    Converts enum literal to enum value.
    Returns default enum value if literal does not correspond any enum value.
    """
    try:
        return enum_type(literal)
    except ValueError:
        return default_value


def enum_from_name_literal(literal: str, enum_type: Type[E], default_value: Optional[E]) -> Optional[E]:
    """
    Converts enum name literal to enum value.
    Returns default enum value if literal does not correspond any enum name.
    """
    try:
        return enum_type[literal]
    except ValueError:
        return default_value


def compare_str_ignore_case(value_1: Optional[str], value_2: Optional[str]) -> bool:
    """Comparing two strings ignoring case."""
    return (value_1 == value_2 or
            ((value_1 is not None and value_2 is not None) and value_1.lower() == value_2.lower()))
