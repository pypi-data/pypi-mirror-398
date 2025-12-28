# pylint: disable=duplicate-code
"""Conversion data"""

import json
from typing import Optional, Iterable
from kameleoon.data.custom_data import CustomData
from kameleoon.data.data import Data, DataType
from kameleoon.helpers.string_utils import StringUtils
from kameleoon.network.sendable import DuplicationSafeSendableBase
from kameleoon.network.query_builder import QueryBuilder, QueryParam, QueryParams


# pylint: disable=R0801
class Conversion(Data, DuplicationSafeSendableBase):
    """Conversion is used for tracking visitors conversions"""

    EVENT_TYPE = "conversion"

    def __init__(
        self,
        goal_id: int,
        revenue: float = 0.0,
        negative: bool = False,
        metadata: Optional[Iterable[CustomData]] = None,
    ) -> None:
        """
        :param goal_id: Id of the goal associated to the conversion
        :type goal_id: int
        :param revenue: Optional field - Revenue associated to the conversion, defaults to 0.0
        :type revenue: float
        :param negative: Optional field - If the revenue is negative. By default it's positive, defaults to False
        :type negative: bool
        :param metadata: Optional field - Metadata of the conversion. `None` by default.
        :type metadata: Optional[Iterable[CustomData]]

        Example:

        .. code-block:: python3

                kameleoon_client.add_data(visitor_code, Conversion(1, 100.0))

        """
        super().__init__()
        self.__goal_id = goal_id
        self.__revenue = revenue
        self.__negative = negative
        self._metadata = metadata

    @property
    def goal_id(self) -> int:
        """Returns goal ID"""
        return self.__goal_id

    @property
    def revenue(self) -> float:
        """Returns revenue"""
        return self.__revenue

    @property
    def negative(self) -> bool:
        """Returns negative flag state"""
        return self.__negative

    @property
    def metadata(self) -> Optional[Iterable[CustomData]]:
        """Returns metadata"""
        return self._metadata

    @property
    def data_type(self) -> DataType:
        return DataType.CONVERSION

    def _add_query_params(self, query_builder: QueryBuilder) -> None:
        # remove query_builder, it's done due due pylint issue with R0801 - duplicate_code,
        # need to update pylint and return str(QueryBuilder) straightaway
        query_builder.extend(
            QueryParam(QueryParams.EVENT_TYPE, self.EVENT_TYPE),
            QueryParam(QueryParams.GOAL_ID, str(self.goal_id)),
            QueryParam(QueryParams.REVENUE, str(self.revenue)),
            QueryParam(QueryParams.NEGATIVE, "true" if self.negative else "false"),
        )
        if self.metadata:
            query_builder.append(QueryParam(QueryParams.METADATA, self.__encode_metadata()))

    def __encode_metadata(self) -> str:
        metadata = {}
        if self.metadata is not None:
            added_indices = set()
            for mcd in self.metadata:
                if isinstance(mcd, CustomData) and (mcd.id not in added_indices):
                    metadata[mcd.id] = mcd.values
                    added_indices.add(mcd.id)
        return json.dumps(metadata, separators=(",", ":"))

    def __str__(self):
        return (
            f"Conversion{{goal_id:{self.__goal_id},"
            f"revenue:{self.__revenue},"
            f"negative:{self.__negative},"
            f"metadata:{StringUtils.object_to_string(self._metadata)}}}"
        )
