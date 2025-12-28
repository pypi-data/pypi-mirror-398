"""Helper class for work with string values"""

import collections.abc
from typing import Any, Optional


class StringUtils:
    """Utility class for string manipulation and object formatting."""

    @staticmethod
    def secret(secret: Optional[str]) -> str:
        """Hide part of the string, keeping only a few initial characters visible."""
        hid_ch = '*'
        vis_count = 4

        if secret is None:
            return "None"

        length = len(secret)

        if length <= vis_count:
            return hid_ch * length

        hidden_length = max(length - vis_count, vis_count)
        return secret[:length - hidden_length] + hid_ch * hidden_length

    @staticmethod
    def bool_to_string_lower_case(data: bool) -> str:
        """Convert a boolean value to a lowercase string."""
        return "true" if data else "false"

    @staticmethod
    def object_to_string(data: Any) -> str:
        """Convert various data types into their string representation."""
        if data is None:
            return "None"
        if isinstance(data, str):
            return f"'{data}'"
        result = StringUtils._collection_to_string(data)
        if result is not None:
            return result
        if isinstance(data, bool):
            return StringUtils.bool_to_string_lower_case(data)
        if hasattr(data, '__str__'):
            return str(data)
        return repr(data)

    @staticmethod
    def _collection_to_string(data: Any) -> Optional[str]:
        if isinstance(data, dict):
            return "{" + ",".join(
                f"{StringUtils.object_to_string(key)}: {StringUtils.object_to_string(value)}"
                for key, value in data.items()
            ) + "}"
        if isinstance(data, collections.abc.Iterable):
            return "[" + ",".join(StringUtils.object_to_string(item) for item in data) + "]"
        return None
