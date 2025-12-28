"""Visitor visits"""

from typing import Any, List, Optional, Tuple

from kameleoon.data import DataType
from kameleoon.network.sendable import DuplicationUnsafeSendableBase
from kameleoon.network.query_builder import QueryBuilder, QueryParam, QueryParams

from kameleoon.data.data import BaseData


class VisitorVisits(BaseData, DuplicationUnsafeSendableBase):
    """Visitor visits"""

    EVENT_TYPE = "staticData"

    def __init__(
        self, prev_visits: List["Visit"], visit_number=0, *, time_started=0, time_since_previous_visit=0
    ) -> None:
        super().__init__()
        self.__visit_number = max(visit_number, len(prev_visits))
        self.__prev_visits = prev_visits
        self.__time_started = time_started
        self.__time_since_previous_visit = time_since_previous_visit

    @property
    def data_type(self) -> DataType:
        return DataType.VISITOR_VISITS

    @property
    def visit_number(self) -> int:
        """Returns the visit number"""
        return self.__visit_number

    @property
    def prev_visits(self) -> List["Visit"]:
        """Returns the previous visit list"""
        return self.__prev_visits

    @property
    def time_started(self) -> int:
        """Returns the current visit's start time"""
        return self.__time_started

    @property
    def time_since_previous_visit(self) -> int:
        """Returns the time since the previous visit"""
        return self.__time_since_previous_visit

    def localize(self, time_started: int) -> "VisitorVisits":
        """
        Localizes a remote instance of `VisitorVisits` creating a new instance
        with a specific current visit's start time.
        """
        time_since_previous_visit = 0
        for visit in self.__prev_visits:
            time_delta = time_started - visit.time_last_activity
            if time_delta >= 0:
                time_since_previous_visit = time_delta
                break
        return VisitorVisits(
            self.__prev_visits, self.__visit_number,
            time_started=time_started, time_since_previous_visit=time_since_previous_visit,
        )

    def _add_query_params(self, query_builder: QueryBuilder) -> None:
        query_builder.extend(
            QueryParam(QueryParams.EVENT_TYPE, self.EVENT_TYPE),
            QueryParam(QueryParams.VISIT_NUMBER, str(self.__visit_number)),
            QueryParam(QueryParams.TIME_SINCE_PREVIOUS_VISIT, str(self.__time_since_previous_visit)),
        )

    def __eq__(self, value: Any) -> bool:
        return isinstance(value, VisitorVisits) and (self.__visit_number == value.visit_number) and \
            (self.__prev_visits == value.prev_visits) and (self.__time_started == value.time_started) and \
            (self.__time_since_previous_visit == value.time_since_previous_visit)

    def __str__(self) -> str:
        return (
            "VisitorVisits{"
            f"visit_number:{self.__visit_number},"
            f"prev_visits:{[str(v) for v in self.__prev_visits]},"
            f"time_started:{self.__time_started},"
            f"time_since_previous_visit:{self.__time_since_previous_visit}"
            "}"
        )

    @staticmethod
    def get_visitor_visits(obj: Any) -> Tuple["VisitorVisits", bool]:
        """Determines if an object is `VisitorVisits` or `None` and returns a valid instance of `VisitorVisits`."""
        if isinstance(obj, VisitorVisits):
            return obj, True
        return VisitorVisits([]), obj is None

    class Visit:
        """Visit"""

        def __init__(self, time_started: int, time_last_activity: Optional[int] = None) -> None:
            self.__time_started = time_started
            self.__time_last_activity = time_last_activity or time_started

        @property
        def time_started(self) -> int:
            """Returns the start time"""
            return self.__time_started

        @property
        def time_last_activity(self) -> int:
            """Returns the last activity time"""
            return self.__time_last_activity

        def __eq__(self, value: Any) -> bool:
            return isinstance(value, VisitorVisits.Visit) and (self.__time_started == value.time_started) and \
                (self.__time_last_activity == value.time_last_activity)

        def __str__(self) -> str:
            return f"Visit{{time_started:{self.__time_started},time_last_activity:{self.__time_last_activity}}}"
