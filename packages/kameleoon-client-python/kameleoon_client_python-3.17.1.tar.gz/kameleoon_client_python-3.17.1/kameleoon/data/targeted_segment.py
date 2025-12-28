"""Targeted Segment"""
from kameleoon.data.data import BaseData, DataType
from kameleoon.network.sendable import DuplicationUnsafeSendableBase
from kameleoon.network.query_builder import QueryBuilder, QueryParam, QueryParams


class TargetedSegment(BaseData, DuplicationUnsafeSendableBase):
    """Targeted Segment"""
    EVENT_TYPE = "targetingSegment"

    def __init__(self, id_: int) -> None:
        super().__init__()
        self.__id = id_

    @property
    def id(self) -> int:
        """Returns the segment ID."""
        return self.__id

    @property
    def data_type(self) -> DataType:
        """Returns the data type for the targeted segment."""
        return DataType.TARGETED_SEGMENT

    def _add_query_params(self, query_builder: QueryBuilder) -> None:
        # fmt: off
        query_builder.extend(
            QueryParam(QueryParams.EVENT_TYPE, self.EVENT_TYPE),
            QueryParam(QueryParams.SEGMENT_ID, str(self.__id)),
        )
        # fmt: on

    def __str__(self) -> str:
        return f"TargetedSegment{{id:{self.__id}}}"
