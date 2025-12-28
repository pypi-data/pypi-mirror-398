"""Kameleoon Configuration"""

from typing import Any, List, Dict, Optional

from kameleoon.configuration.custom_data_info import CustomDataInfo
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.variation import Variation
from kameleoon.helpers.string_utils import StringUtils
from kameleoon.targeting.models import Segment


class FeatureFlag:
    """
    FeatureFlag is used for operating feature flags with rules
    """

    def __init__(self, dict_json: Dict[str, Any], segments: Dict[int, Segment], cdi: CustomDataInfo) -> None:
        self.id_: int = dict_json.get("id", 0)
        self.feature_key: str = dict_json.get("featureKey", "")
        self.default_variation_key: str = dict_json.get("defaultVariationKey", "")
        self.me_group_name: Optional[str] = dict_json.get("mutuallyExclusiveGroup")
        self.variations: List[Variation] = Variation.from_array(
            dict_json.get("variations", [])
        )
        self.environment_enabled = dict_json.get("environmentEnabled", False)
        self.rules: List[Rule] = Rule.from_array(dict_json.get("rules", []), segments)
        bucketing_cd_id = dict_json.get("bucketingCustomDataId")
        self.bucketing_custom_data_index = cdi.get_custom_data_index_by_id(bucketing_cd_id) if bucketing_cd_id else None

    def get_variation(self, key: str) -> Optional[Variation]:
        """Retrun a variation for the given key"""
        return next((v for v in self.variations if v.key == key), None)

    def __str__(self):
        return (
            f"FeatureFlag{{"
            f"id:{self.id_},"
            f"feature_key:'{self.feature_key}',"
            f"environment_enabled:{self.environment_enabled},"
            f"variations:{StringUtils.object_to_string(self.variations)},"
            f"default_variation_key:'{self.default_variation_key}',"
            f"me_group_name:'{self.me_group_name}',"
            f"rules:{len(self.rules)},"
            f"bucketing_custom_data_index:{self.bucketing_custom_data_index}"
            f"}}"
        )
