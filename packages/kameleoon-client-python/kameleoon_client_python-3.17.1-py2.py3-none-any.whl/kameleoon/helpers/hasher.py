"""Helper hash functions"""

import hashlib
import math
from typing import Optional


class Hasher:
    """Hasher"""

    @staticmethod
    def obtain(
        visitor_code: str, container_id: int, respool_time: Optional[int] = None
    ) -> float:
        """Calculate the hash value for feature flag v2 for a given visitor_code"""
        identifier = visitor_code
        identifier += str(container_id)
        if respool_time:
            identifier += str(respool_time)
        return Hasher._calculate(identifier)

    @staticmethod
    def obtain_hash_for_me_group(visitor_code: str, me_group_name: str) -> float:
        """Calculate the hash value for a mutually exclusive group for a given visitor code"""
        return Hasher._calculate(visitor_code + me_group_name)

    @staticmethod
    def _calculate(str_to_hash: str) -> float:
        return int(hashlib.sha256(str_to_hash.encode("UTF-8")).hexdigest(), 16) / math.pow(2, 256)
