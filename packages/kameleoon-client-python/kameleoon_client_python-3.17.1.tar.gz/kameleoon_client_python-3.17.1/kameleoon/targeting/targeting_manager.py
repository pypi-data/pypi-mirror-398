"""Targeting Segment"""

from typing import Optional
from kameleoon.data.manager.visitor import Visitor
from kameleoon.data.manager.visitor_manager import VisitorManager
from kameleoon.helpers.functions import enum_from_literal
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.managers.data.data_manager import DataManager
from kameleoon.sdk_version import SdkVersion
from kameleoon.targeting.conditions.exclusive_experiment_condition import ExclusiveExperimentCondition
from kameleoon.targeting.conditions.sdk_language_condition import SdkLanguageCondition
from kameleoon.targeting.conditions.segment_condition import SegmentCondition
from kameleoon.targeting.conditions.target_feature_flag_condition import TargetFeatureFlagCondition
from kameleoon.targeting.conditions.target_experiment_condition import TargetExperimentCondition
from kameleoon.targeting.conditions.target_personalization_condition import TargetPersonalizationCondition
from kameleoon.targeting.conditions.targeting_condition import TargetingConditionType
from kameleoon.targeting.conditions.visit_number_today_condition import VisitNumberTodayCondition
from kameleoon.targeting.models import Segment


class TargetingManager:
    """Manager for check visitor is targeted for rule"""

    def __init__(self, data_manager: DataManager, visitor_manager: VisitorManager) -> None:
        self.__data_manager = data_manager
        self.__visitor_manager = visitor_manager

    # pylint: disable=W0238
    def check_targeting(self, visitor_code: str, campaign_id: Optional[int], segment: Optional[Segment]):
        """Check if visitor is targeted for rule"""
        KameleoonLogger.debug(
            "CALL: TargetingManager.check_targeting(visitor_code: %s, campaign_id: %s, segment: %s)",
            visitor_code, campaign_id, segment
        )
        if segment is None:
            targeting: Optional[bool] = True
        else:
            visitor = self.__visitor_manager.get_visitor(visitor_code)
            targeting = segment.check_tree(
                lambda type: self.__get_condition_data(type, visitor, visitor_code, campaign_id)
            )
        KameleoonLogger.debug(
            "RETURN: TargetingManager.check_targeting(visitor_code: %s, campaign_id: %s, "
            "segment: %s) -> (targeting: %s)", visitor_code, campaign_id, segment, targeting
        )
        return targeting

    # pylint: disable=R0911
    def __get_condition_data(
        self,
        condition_type_literal: str,
        visitor: Optional[Visitor],
        visitor_code: str,
        campaign_id: Optional[int],
    ):
        # pylint: disable=E1101
        KameleoonLogger.debug(
            "CALL: TargetingManager.__get_condition_data(condition_type_literal: %s, visitor, visitor_code: %s, "
            "campaign_id: %s)", condition_type_literal, visitor_code, campaign_id
        )
        condition_type = enum_from_literal(
            condition_type_literal,
            TargetingConditionType,
            TargetingConditionType.UNKNOWN,
        )
        condition_data = None
        if visitor:
            condition_data = self.__get_condition_data_by_type(visitor, condition_type)
        if condition_data is None:
            if condition_type == TargetingConditionType.SEGMENT:
                condition_data = SegmentCondition.SegmentInfo(
                    self.__data_manager.data_file,
                    lambda type: self.__get_condition_data(type, visitor, visitor_code, campaign_id),
                )
            elif condition_type == TargetingConditionType.EXCLUSIVE_EXPERIMENT:
                if campaign_id is not None:
                    condition_data = ExclusiveExperimentCondition.TargetingData(
                        campaign_id, visitor.variations if visitor else {}, visitor.personalizations if visitor else {}
                    )
            elif condition_type == TargetingConditionType.VISITOR_CODE:
                condition_data = visitor_code
            elif condition_type == TargetingConditionType.SDK_LANGUAGE:
                condition_data = SdkLanguageCondition.SdkInfo(SdkVersion.NAME, SdkVersion.VERSION)
            elif condition_type == TargetingConditionType.TARGET_EXPERIMENT:
                condition_data = TargetExperimentCondition.TargetingData(visitor.variations if visitor else {})
            elif condition_type == TargetingConditionType.TARGET_PERSONALIZATION:
                condition_data = TargetPersonalizationCondition.TargetingData(
                    visitor.personalizations if visitor else {}
                )
            elif condition_type == TargetingConditionType.SAME_DAY_VISITS:
                condition_data = VisitNumberTodayCondition.TargetingData(None, None)
        KameleoonLogger.debug(
            "RETURN: TargetingManager.__get_condition_data(condition_type_literal: %s, visitor, visitor_code: %s,"
            " campaign_id: %s) -> (condition_data: %s)",
            condition_type_literal, visitor_code, campaign_id, condition_data
        )
        return condition_data

    def __get_condition_data_by_type(self, visitor: Visitor, condition_type: TargetingConditionType):  # noqa: C901
        if condition_type == TargetingConditionType.BROWSER:
            return visitor.browser
        if condition_type == TargetingConditionType.DEVICE_TYPE:
            return visitor.device
        if condition_type == TargetingConditionType.COOKIE:
            return visitor.cookie
        if condition_type == TargetingConditionType.GEOLOCATION:
            return visitor.geolocation
        if condition_type == TargetingConditionType.OPERATING_SYSTEM:
            return visitor.operating_system
        if condition_type == TargetingConditionType.CUSTOM_DATUM:
            return visitor.custom_data
        if condition_type == TargetingConditionType.CONVERSIONS:
            return visitor.conversions
        if condition_type in (
            TargetingConditionType.PAGE_URL,
            TargetingConditionType.PAGE_TITLE,
            TargetingConditionType.PAGE_VIEWS,
            TargetingConditionType.PREVIOUS_PAGE,
        ):
            return visitor.page_view_visits
        if condition_type == TargetingConditionType.TARGET_FEATURE_FLAG:
            return TargetFeatureFlagCondition.TargetFeatureFlagInfo(self.__data_manager.data_file, visitor.variations)
        if condition_type in (
            TargetingConditionType.FIRST_VISIT,
            TargetingConditionType.LAST_VISIT,
            TargetingConditionType.VISITS,
            TargetingConditionType.NEW_VISITORS,
        ):
            return visitor.visitor_visits
        if condition_type == TargetingConditionType.SAME_DAY_VISITS:
            return VisitNumberTodayCondition.TargetingData(visitor.time_started, visitor.visitor_visits)
        if condition_type == TargetingConditionType.HEAT_SLICE:
            return visitor.kcs_heat
        return None
