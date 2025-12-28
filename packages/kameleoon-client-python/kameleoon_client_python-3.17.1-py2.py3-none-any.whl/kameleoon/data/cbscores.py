"""CBScores"""

from typing import Dict, Iterable, List
from kameleoon.helpers.string_utils import StringUtils
from kameleoon.data import DataType
from kameleoon.data.data import BaseData


# pylint: disable=R0903
class ScoredVarId:
    """ScoredVarId"""
    def __init__(self, variation_id: int, score: float) -> None:
        self.variation_id = variation_id
        self.score = score


class VarGroup:
    """VarGroup"""
    def __init__(self, ids: List[int]) -> None:
        ids.sort()
        self.__ids = ids

    @property
    def ids(self) -> List[int]:
        """Returns the IDs"""
        return self.__ids

    def __str__(self) -> str:
        return f"VarGroup{{ids:{self.__ids}}}"


class CBScores(BaseData):
    """CBScores"""

    def __init__(self, cbs_map: Dict[int, Iterable[ScoredVarId]]) -> None:
        super().__init__()
        self.__values = {cbs_key: self.__extract_var_ids(cbs_value) for cbs_key, cbs_value in cbs_map.items()}

    @property
    def values(self) -> Dict[int, List[VarGroup]]:
        """
        Returns the CB variation groups stored by experiment.

        keys = experiment IDs / values = list of variation IDs ordered descending
        by score (there may be several variation ids with same score)
        """
        return self.__values

    @property
    def data_type(self) -> DataType:
        return DataType.CBS

    @staticmethod
    def __extract_var_ids(scores: Iterable[ScoredVarId]) -> List[VarGroup]:
        grouped: Dict[float, List[int]] = {}
        for score in scores:
            glist = grouped.get(score.score)
            if glist:
                glist.append(score.variation_id)
            else:
                grouped[score.score] = [score.variation_id]
        return [VarGroup(grouped[score]) for score in sorted(grouped, reverse=True)]

    def __str__(self) -> str:
        values = StringUtils.object_to_string(self.__values)
        return f"CBScores{{values:{values}}}"
