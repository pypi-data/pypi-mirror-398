"""Personalization"""

from kameleoon.data import DataType
from kameleoon.data.data import BaseData


class Personalization(BaseData):
    """Personalization"""

    def __init__(self, id_: int, variation_id: int) -> None:
        super().__init__()
        self.__id = id_
        self.__variation_id = variation_id

    @property
    def id(self) -> int:
        """Returns personalization ID"""
        return self.__id

    @property
    def variation_id(self) -> int:
        """Returns variation ID"""
        return self.__variation_id

    @property
    def data_type(self) -> DataType:
        return DataType.PERSONALIZATION

    def __str__(self):
        return f"Personalization{{id:{self.__id},variation_id:{self.__variation_id}}}"
