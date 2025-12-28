""" condition"""

from typing import Any, Union, Dict
from kameleoon.data.manager.page_view_visit import PageViewVisit
from kameleoon.targeting.conditions.string_value_condition import StringValueCondition


class PageUrlCondition(StringValueCondition):
    """Page url condition uses when you need to compare url of page"""

    def __init__(self, json_condition: Dict[str, Union[str, Any]]):
        super().__init__(json_condition, json_condition.get("url"))

    def check(self, data: Any) -> bool:
        return isinstance(data, dict) and self.__check(data)

    def __check(self, page_view_visits: Dict[str, PageViewVisit]) -> bool:
        latest = max(page_view_visits.values(), key=lambda visit: visit.last_timestamp, default=None)
        return latest is not None and self._check(latest.page_view.url)
