"""Forced Experiment Variation"""

from typing import Any, cast
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.data.data import DataType
from kameleoon.data.manager.forced_variation import ForcedVariation


class ForcedExperimentVariation(ForcedVariation):
    """Represents a forced experiment variation"""

    def __init__(
        self, rule: Rule, var_by_exp: VariationByExposition, force_targeting: bool
    ) -> None:
        super().__init__(rule, var_by_exp)
        self.__force_targeting = force_targeting

    @property
    def data_type(self) -> DataType:
        return DataType.FORCED_EXPERIMENT_VARIATION

    @property
    def rule(self) -> Rule:
        """Returns the rule"""
        return self._rule or cast(Rule, self._rule)

    @property
    def var_by_exp(self) -> VariationByExposition:
        """Returns the variation by exposition"""
        return self._var_by_exp or cast(VariationByExposition, self._var_by_exp)

    @property
    def force_targeting(self) -> bool:
        """Returns the force targeting flag's state"""
        return self.__force_targeting

    def __eq__(self, value: Any) -> bool:
        return super().__eq__(value) and isinstance(value, ForcedExperimentVariation) and \
            (self.__force_targeting == value.force_targeting)

    def __str__(self) -> str:
        return (
            "ForcedExperimentVariation{"
            f"rule:{self._rule},"
            f"var_by_exp:{self._var_by_exp},"
            f"force_targeting:{self.__force_targeting},"
            "}"
        )
