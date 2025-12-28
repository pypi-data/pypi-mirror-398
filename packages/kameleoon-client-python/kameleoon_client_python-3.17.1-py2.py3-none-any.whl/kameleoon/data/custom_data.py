"""Custom data"""

import json
from typing import Optional, Tuple, Union
from kameleoon.data.data import Data, DataType
from kameleoon.network.sendable import DuplicationUnsafeSendableBase
from kameleoon.network.query_builder import QueryBuilder, QueryParam, QueryParams


class CustomData(Data, DuplicationUnsafeSendableBase):
    """Custom data"""

    EVENT_TYPE = "customData"
    UNDEFINED_INDEX = -1

    def __init__(self, index_or_name: Union[int, str], *args: str, overwrite=True) -> None:
        """
        :param index_or_name: Index or Name of the custom data. This field is mandatory.
        :type index_or_name: Union[int, str]
        :param args: Values of the custom data to be stored. This field is mandatory.
        :type args: *str
        :param overwrite: Flag to explicitly control how the values are stored and how they appear in reports.
        This field is optional, `True` by default.
        :type overwrite: bool
        """
        # pylint: disable=invalid-name,redefined-builtin
        super().__init__()
        # pylint: disable=W0511
        if isinstance(index_or_name, int):
            self.__index = index_or_name
            self._name = None
        else:
            self.__index = self.UNDEFINED_INDEX
            self._name = index_or_name
        self.__values = args
        self.__overwrite = overwrite

    def _named_to_indexed(self, index: int) -> "CustomData":
        """Makes an indexed Custom Data instance based on the current instance"""
        custom_data = CustomData(index, *self.__values, overwrite=self.__overwrite)
        custom_data._name = self._name
        return custom_data

    @property
    def id(self) -> int:
        """
        Deprecated. Please use `index` instead.

        Returns index
        """
        return self.__index

    @property
    def index(self) -> int:
        """Returns index"""
        return self.__index

    @property
    def name(self) -> Optional[str]:
        """Returns name"""
        return self._name

    @property
    def values(self) -> Tuple[str, ...]:
        """Returns values"""
        return self.__values

    @property
    def overwrite(self) -> bool:
        """Returns overwrite"""
        return self.__overwrite

    @property
    def data_type(self) -> DataType:
        return DataType.CUSTOM_DATA

    def _add_query_params(self, query_builder: QueryBuilder) -> None:
        str_values = json.dumps({v: 1 for v in self.__values}, separators=(",", ":"))
        query_builder.extend(
            QueryParam(QueryParams.EVENT_TYPE, self.EVENT_TYPE, False),
            QueryParam(QueryParams.INDEX, str(self.id), False),
            QueryParam(QueryParams.VALUES_COUNT_MAP, str_values),
            QueryParam(QueryParams.OVERWRITE, "true" if self.__overwrite else "false", False),
        )

    def __str__(self):
        return (
            "CustomData{"
            f"index:{self.__index},name:'{self._name}',values:{self.__values},overwrite:{self.__overwrite}"
            "}"
        )
