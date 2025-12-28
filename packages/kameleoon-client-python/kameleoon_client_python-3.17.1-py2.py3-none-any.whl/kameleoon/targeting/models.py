"""Targeting Segment"""

from typing import Any, Dict, Optional
from kameleoon.targeting.tree_builder import create_tree, Tree


class Segment:
    """Segment with targeting data"""

    def __init__(self, id_: int, tree: Optional[Tree], audience_tracking: bool) -> None:
        self.id_ = id_
        self.tree = tree
        self.audience_tracking = audience_tracking

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "Segment":
        """Creates a Segment instance from JSON object"""
        id_ = obj.get("id", -1)
        tree = create_tree(obj.get("conditionsData"))
        audience_tracking = obj.get("audienceTracking", False)
        return Segment(id_, tree, audience_tracking)

    def check_tree(self, get_targeting_data) -> Optional[bool]:
        """Checks the targeting throught targeting tree"""
        return self.tree.check(get_targeting_data) if self.tree else True

    def __str__(self) -> str:
        return f"Segment{{id:{self.id_},audience_tracking:{self.audience_tracking}}}"
