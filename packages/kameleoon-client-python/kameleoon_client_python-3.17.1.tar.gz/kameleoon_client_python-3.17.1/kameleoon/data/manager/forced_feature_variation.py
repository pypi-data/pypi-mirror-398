"""Forced Feature Variation"""

from typing import Any, Optional
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.data.data import DataType
from kameleoon.data.manager.forced_variation import ForcedVariation


class ForcedFeatureVariation(ForcedVariation):
    """Represents a forced feature variation"""

    def __init__(
        self, feature_key: str, rule: Optional[Rule], var_by_exp: Optional[VariationByExposition], simulated: bool
    ) -> None:
        super().__init__(rule, var_by_exp)
        self.__feature_key = feature_key
        self.__simulated = simulated

    @property
    def data_type(self) -> DataType:
        return DataType.FORCED_FEATURE_VARIATION

    @property
    def feature_key(self) -> str:
        """Returns the feature key"""
        return self.__feature_key

    @property
    def simulated(self) -> bool:
        """Returns the simulated flag's state"""
        return self.__simulated

    def __eq__(self, value: Any) -> bool:
        return super().__eq__(value) and isinstance(value, ForcedFeatureVariation) and \
            (self.__feature_key == value.feature_key) and (self.__simulated == value.simulated)

    def __str__(self) -> str:
        return (
            "ForcedFeatureVariation{"
            f"feature_key:'{self.__feature_key}',"
            f"rule:{self._rule},"
            f"var_by_exp:{self._var_by_exp},"
            f"simulated:{self.__simulated},"
            "}"
        )
