"""Target experiment condition"""

from typing import cast, Any, Union, Dict
from kameleoon.data.manager.assigned_variation import AssignedVariation
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.targeting.conditions.constants import TargetingOperator
from kameleoon.targeting.conditions.targeting_condition import TargetingCondition


class TargetExperimentCondition(TargetingCondition):
    """Target experiment condition"""

    # pylint: disable=R0903
    class TargetingData:
        """Represents targeting data for TargetExperimentCondition"""

        def __init__(self, variations: Dict[int, AssignedVariation]):
            self.variations = variations

    def __init__(self, json_condition: Dict[str, Union[str, int, Any]]):
        super().__init__(json_condition)
        self.__variation_id = json_condition.get("variationId", -1)
        self.__experiment_id: int = cast(int, json_condition.get("experimentId", -1))
        self.__variation_match_type = json_condition.get("variationMatchType")

    def check(self, data: TargetingData) -> bool:
        variation = data.variations.get(self.__experiment_id)
        if self.__variation_match_type == TargetingOperator.ANY.value:
            return variation is not None
        if self.__variation_match_type == TargetingOperator.EXACT.value:
            return (variation is not None) and (variation.variation_id == self.__variation_id)
        KameleoonLogger.error(
            "Unexpected variation match type for %s condition: %s", self.type, self.__variation_match_type
        )
        return False
