"""Kameleoon Configuration"""

from typing import List
from kameleoon.configuration.feature_flag import FeatureFlag


class MEGroup:
    """Represents a mutually exclusive group"""

    def __init__(self, feature_flags: List[FeatureFlag]) -> None:
        feature_flags.sort(key=lambda ff: ff.id_)
        self.__feature_flags = feature_flags

    @property
    def feature_flags(self) -> List[FeatureFlag]:
        """Returns the feature flags"""
        return self.__feature_flags

    def get_feature_flag_by_hash(self, hash_double: float) -> FeatureFlag:
        """Finds a feature flag by the given hash"""
        idx = int(hash_double * len(self.__feature_flags))
        if idx >= len(self.__feature_flags):
            idx = len(self.__feature_flags) - 1
        return self.__feature_flags[idx]
