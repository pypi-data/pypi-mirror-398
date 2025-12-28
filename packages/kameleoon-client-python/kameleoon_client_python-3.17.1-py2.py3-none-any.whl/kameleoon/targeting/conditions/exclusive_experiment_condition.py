"""Exclusive experiment condition"""

from typing import Any, Union, Dict
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.data.personalization import Personalization
from kameleoon.data.manager.assigned_variation import AssignedVariation
from kameleoon.targeting.conditions.targeting_condition import TargetingCondition


class ExclusiveExperimentCondition(TargetingCondition):
    """Exclusive experiment condition"""

    # pylint: disable=R0903
    class TargetingData:
        """Represents targeting data for ExclusiveExperimentCondition"""

        def __init__(
            self,
            current_experiment_id: int,
            variations: Dict[int, AssignedVariation],
            personalizations: Dict[int, Personalization],
        ) -> None:
            self.current_experiment_id = current_experiment_id
            self.variations = variations
            self.personalizations = personalizations

    # pylint: disable=R0903
    class CampaignType:
        """Aggregates campaign types"""
        EXPERIMENT = "EXPERIMENT"
        PERSONALIZATION = "PERSONALIZATION"
        ANY = "ANY"

    def __init__(self, json_condition: Dict[str, Union[str, int, Any]]) -> None:
        super().__init__(json_condition)
        self.__campaign_type = json_condition.get("campaignType")

    def check(self, data: Any) -> bool:
        if not isinstance(data, self.TargetingData):
            return False
        if self.__campaign_type == self.CampaignType.EXPERIMENT:
            return self.__check_experiment(data)
        if self.__campaign_type == self.CampaignType.PERSONALIZATION:
            return self.__check_personalization(data)
        if self.__campaign_type == self.CampaignType.ANY:
            return self.__check_personalization(data) and self.__check_experiment(data)
        KameleoonLogger.error("Unexpected campaign type for %s condition: %s", self.type, self.__campaign_type)
        return False

    @staticmethod
    def __check_experiment(data: TargetingData) -> bool:
        size = len(data.variations)
        return (size == 0) or ((size == 1) and data.variations.get(data.current_experiment_id) is not None)

    @staticmethod
    def __check_personalization(data: TargetingData) -> bool:
        return len(data.personalizations) == 0
