"""Time elapsed since visit condition"""

import time
from typing import Any, Dict, Union
from kameleoon.data.visitor_visits import VisitorVisits
from kameleoon.targeting.conditions.targeting_condition import TargetingConditionType
from kameleoon.targeting.conditions.number_condition import NumberCondition


class TimeElapsedSinceVisitCondition(NumberCondition):
    """Time elapsed since visit condition"""

    def __init__(self, json_condition: Dict[str, Union[str, int, Any]]):
        super().__init__(json_condition, "countInMillis")
        self.__is_first_visit = self.type == TargetingConditionType.FIRST_VISIT.name

    def check(self, data: Any) -> bool:
        visitor_visits, ok = VisitorVisits.get_visitor_visits(data)
        return ok and (self._condition_value is not None) and self.__check(visitor_visits)

    def __check(self, visitor_visits: VisitorVisits) -> bool:
        if len(visitor_visits.prev_visits) == 0:
            return False
        now = int(time.time() * 1000)  # Convert seconds to milliseconds
        visit = visitor_visits.prev_visits[-1 if self.__is_first_visit else 0]
        return self._check_targeting(now - visit.time_started)
