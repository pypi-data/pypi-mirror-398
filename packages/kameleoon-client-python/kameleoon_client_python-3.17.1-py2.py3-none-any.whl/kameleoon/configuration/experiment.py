"""Kameleoon Configuration"""

from typing import Any, List, Dict, Optional
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.exceptions import FeatureVariationNotFound


class Experiment:
    """Experiment"""

    def __init__(self, id_: int, variations_by_exposition: List[VariationByExposition]) -> None:
        self.id_ = id_
        self.variations_by_exposition = variations_by_exposition
        self.first_variation = variations_by_exposition[0] if len(variations_by_exposition) > 0 else None

    @staticmethod
    def from_json(dict_json: Dict[str, Any]) -> "Experiment":
        """Creates a new instance of `Experiment` from a json object"""
        id_ = dict_json.get("experimentId", 0)
        variations_by_exposition: List[VariationByExposition] = VariationByExposition.from_array(
            dict_json.get("variationByExposition", [])
        )
        return Experiment(id_, variations_by_exposition)

    def get_variation(self, hash_double: float) -> Optional[VariationByExposition]:
        """Calculates the variation key for the given hash of visitor"""

        total = 0.0
        for var_by_exp in self.variations_by_exposition:
            total += var_by_exp.exposition
            if total >= hash_double:
                return var_by_exp
        return None

    def get_variation_by_key(self, variation_key: str) -> VariationByExposition:
        """
        Finds variation with a passed variation key.
        Raises the `FeatureVariationNotFound` exception if such variation does not exist.
        """
        for var_by_exp in self.variations_by_exposition:
            if var_by_exp.variation_key == variation_key:
                return var_by_exp
        raise FeatureVariationNotFound("'#{variation_key}'")

    def __str__(self) -> str:
        return f"Experiment{{id:{self.id_}}}"
