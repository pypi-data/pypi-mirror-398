"""Forced Variation"""

from typing import Any, Optional
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.data.data import BaseData, DataType


class ForcedVariation(BaseData):
    """Represents a forced variation"""

    def __init__(self, rule: Optional[Rule], var_by_exp: Optional[VariationByExposition]) -> None:
        super().__init__()
        self._rule = rule
        self._var_by_exp = var_by_exp

    @property
    def data_type(self) -> DataType:
        raise NotImplementedError

    @property
    def rule(self) -> Optional[Rule]:
        """Returns the rule"""
        return self._rule

    @property
    def var_by_exp(self) -> Optional[VariationByExposition]:
        """Returns the variation by exposition"""
        return self._var_by_exp

    def __eq__(self, value: Any) -> bool:
        return isinstance(value, ForcedVariation) and \
            (self._rule == value._rule) and (self._var_by_exp == value._var_by_exp)
