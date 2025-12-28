"""Target personalization condition"""

from typing import Any, Union, Dict
from kameleoon.data.personalization import Personalization
from kameleoon.targeting.conditions.targeting_condition import TargetingCondition


class TargetPersonalizationCondition(TargetingCondition):
    """Target personalization condition"""

    # pylint: disable=R0903
    class TargetingData:
        """Represents targeting data for TargetPersonalizationCondition"""

        def __init__(self, personalizations: Dict[int, Personalization]):
            self.personalizations = personalizations

    def __init__(self, json_condition: Dict[str, Union[int, Any]]):
        super().__init__(json_condition)
        self.__personalization_id = json_condition.get("personalizationId", -1)

    def check(self, data: TargetingData) -> bool:
        return data.personalizations.get(self.__personalization_id) is not None
