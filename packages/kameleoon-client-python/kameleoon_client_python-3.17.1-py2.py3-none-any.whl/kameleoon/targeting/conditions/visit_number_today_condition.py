"""Visit number today condition"""

import time

from typing import Any, Dict, Union, Optional
from datetime import datetime
from kameleoon.data.visitor_visits import VisitorVisits
from kameleoon.targeting.conditions.number_condition import NumberCondition


class VisitNumberTodayCondition(NumberCondition):
    """Visit number today condition uses in case if you need to target by value numeric"""

    def __init__(self, json_condition: Dict[str, Union[str, int, Any]]):
        super().__init__(json_condition, "visitCount")

    def check(self, data: Any) -> bool:
        return isinstance(data, VisitNumberTodayCondition.TargetingData) and self.__check(data)

    def __check(self, targeting_data: "TargetingData") -> bool:
        if self._condition_value is None:
            return False
        number_of_visits_today = 0
        start_of_day = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        # ... * 1000 for convert seconds to milliseconds
        for visit in targeting_data.visitor_visits.prev_visits:
            if visit.time_started < start_of_day:
                break
            number_of_visits_today += 1
        if targeting_data.current_visit_time_started >= start_of_day:
            number_of_visits_today += 1
        return self._check_targeting(number_of_visits_today)

    # pylint: disable=R0903
    class TargetingData:
        """TargetingData for VisitNumberTodayCondition"""

        def __init__(self, current_visit_time_started: Optional[int], visitor_visits: Optional[VisitorVisits]) -> None:
            self.current_visit_time_started = current_visit_time_started or int(time.time() * 1000)
            self.visitor_visits = visitor_visits or VisitorVisits([])
