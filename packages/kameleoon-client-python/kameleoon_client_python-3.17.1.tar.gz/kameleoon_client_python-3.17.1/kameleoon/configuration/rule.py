"""Kameleoon Configuration"""

from typing import Any, List, Dict, Optional
from kameleoon.configuration.experiment import Experiment
from kameleoon.configuration.rule_type import RuleType, rule_type_from_literal
from kameleoon.targeting.models import Segment


class Rule:
    """
    Rule is used for saving rule of feature flags (v2) with rules
    """

    @staticmethod
    def from_array(array: List[Dict[str, Any]], segments: Dict[int, Segment]) -> List["Rule"]:
        """Create a list of Rules from the json array"""
        return [Rule(item, segments) for item in array]

    def __init__(self, dict_json: Dict[str, Any], segments: Dict[int, Segment]) -> None:
        self.id_: int = dict_json["id"]
        self.order: int = dict_json.get("order", 0)
        type_literal: str = dict_json.get("type", "")
        self.type = rule_type_from_literal(type_literal)
        self.exposition: float = dict_json.get("exposition", 0.0)
        self.experiment = Experiment.from_json(dict_json)
        self.respool_time: Optional[int] = dict_json.get("respoolTime", None)
        segment_id = dict_json.get("segmentId")
        self.segment_id: int = segment_id or -1
        self.targeting_segment: Optional[Segment] = segments.get(segment_id) if segment_id else None

    @property
    def is_experimentation(self) -> bool:
        """Return `true` if rule is `experimentation` type"""
        return self.type == RuleType.EXPERIMENTATION

    @property
    def is_targeted_delivery(self) -> bool:
        """Return `true` if rule is `targeted delivery` type"""
        return self.type == RuleType.TARGETED_DELIVERY

    def __str__(self) -> str:
        return f"Rule{{id:{self.id_}}}"
