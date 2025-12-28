"""Kameleoon Configuration"""

from typing import Any, Dict, Iterable, List, Optional, Set
from kameleoon.configuration import Variable
from kameleoon.configuration.custom_data_info import CustomDataInfo
from kameleoon.configuration.experiment import Experiment
from kameleoon.configuration.feature_flag import FeatureFlag
from kameleoon.configuration.me_group import MEGroup
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.settings import Settings
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.exceptions import FeatureNotFound, FeatureEnvironmentDisabled
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.targeting.models import Segment


class DataFile:
    """`DataFile` is a container for an actual client-configuration data"""

    @staticmethod
    def default(environment: Optional[str]) -> "DataFile":
        """Creates new instance of `DataFile` initialized with default values"""
        data_file = DataFile(environment, None, Settings(), {}, {}, CustomDataInfo(None))
        return data_file

    @staticmethod
    def from_json(
        environment: Optional[str], last_modified: Optional[str], configuration: Dict[str, Any]
    ) -> "DataFile":
        """Creates new instance of `DataFile` initialized from the specified configuration JSON"""
        settings = Settings(configuration.get("configuration"))
        segments = DataFile.__parse_segments(configuration)
        custom_data_info = CustomDataInfo(configuration.get("customData"))
        feature_flags = DataFile.__parse_feature_flags(configuration, segments, custom_data_info)
        holdout = Experiment.from_json(configuration["holdout"]) if "holdout" in configuration else None
        data_file = DataFile(environment, last_modified, settings, segments, feature_flags, custom_data_info, holdout)
        return data_file

    @staticmethod
    def __parse_segments(configuration: Dict[str, Any]) -> Dict[int, Segment]:
        return {
            (seg := Segment.from_json(jobj)).id_: seg
            for jobj in configuration.get("segments") or []
        }

    @staticmethod
    def __parse_feature_flags(
        configuration: Dict[str, Any], segments: Dict[int, Segment], cdi: CustomDataInfo
    ) -> Dict[str, FeatureFlag]:
        return {
            (ff := FeatureFlag(jobj, segments, cdi)).feature_key: ff
            for jobj in configuration.get("featureFlags") or []
        }

    # pylint: disable=R0913
    def __init__(
        self,
        environment: Optional[str],
        last_modified: Optional[str],
        settings: Settings,
        segments: Dict[int, Segment],
        feature_flags: Dict[str, FeatureFlag],
        custom_data_info: CustomDataInfo,
        holdout: Optional[Experiment] = None,
    ) -> None:
        KameleoonLogger.debug(
            "CALL: DataFile(environment: %s, last_modified: %s, settings: %s, segments, feature_flags,"
            " custom_data_info: %s, holdout: %s)",
            environment, last_modified, settings, custom_data_info, holdout
        )
        self.__environment = environment  # pylint: disable=W0238
        self.__last_modified = last_modified
        self.__settings = settings
        self.__segments = segments
        self.__audience_tracking_segments = [seg for seg in segments.values() if seg.audience_tracking]
        self.__feature_flags: Dict[str, FeatureFlag] = feature_flags
        self.__me_groups = self.__make_me_groups(feature_flags.values())
        self.__has_any_targeted_delivery_rule = any(
            rule.is_targeted_delivery
            for ff in self.__feature_flags.values()
            if ff.environment_enabled
            for rule in ff.rules
        )
        self.__variation_by_id: Dict[int, VariationByExposition] = {}
        self.__rule_info_by_exp_id: Dict[int, DataFile.RuleInfo] = {}
        self.__feature_flag_by_id: Dict[int, FeatureFlag] = {}
        self.__experiment_ids_with_js_css_variable: Set[int] = set()
        self.__collect_indices()
        self.__custom_data_info = custom_data_info
        self.__holdout = holdout
        KameleoonLogger.debug(
            "RETURN: DataFile(environment: %s, last_modified: %s, settings: %s, segments, feature_flags,"
            " custom_data_info: %s, holdout: %s)",
            environment, last_modified, settings, custom_data_info, holdout
        )

    @property
    def last_modified(self) -> Optional[str]:
        """Returns last modified string"""
        return self.__last_modified

    @property
    def settings(self) -> Settings:
        """Returns settings"""
        return self.__settings

    @property
    def segments(self) -> Dict[int, Segment]:
        """Returns segments"""
        return self.__segments

    @property
    def audience_tracking_segments(self) -> List[Segment]:
        """Returns audience tracking segments"""
        return self.__audience_tracking_segments

    @property
    def feature_flags(self) -> Dict[str, FeatureFlag]:
        """Returns dictionary of all feature flags stored by feature keys"""
        return self.__feature_flags

    @property
    def me_groups(self) -> Dict[str, MEGroup]:
        """Returns the mutually exclusive groups by their names"""
        return self.__me_groups

    @property
    def feature_flag_by_id(self) -> Dict[int, FeatureFlag]:
        """Returns dictionary of all feature flags stored by id"""
        return self.__feature_flag_by_id

    @property
    def rule_info_by_exp_id(self) -> Dict[int, "DataFile.RuleInfo"]:
        """Returns dictionary of all rule related info stored by experiment id"""
        return self.__rule_info_by_exp_id

    @property
    def variation_by_id(self) -> Dict[int, VariationByExposition]:
        """Returns dictionary of all variations stored by id"""
        return self.__variation_by_id

    @property
    def has_any_targeted_delivery_rule(self) -> bool:
        """Returns `True` if has a feature flag with a rule of the targeted delivery type, otherwise returns `False`"""
        return self.__has_any_targeted_delivery_rule

    def get_feature_flag(self, feature_key: str) -> FeatureFlag:
        """
        Returns feature flag with the specified feature key if it exists,
        otherwise raises `FeatureNotFound` exception.
        """
        feature_flag = self.__feature_flags.get(feature_key)
        if feature_flag is None:
            raise FeatureNotFound(feature_key)
        if not feature_flag.environment_enabled:
            env = "default" if self.__environment is None else f"'{self.__environment}'"
            raise FeatureEnvironmentDisabled(f"Feature '{feature_key}' is disabled for {env} environment")
        return feature_flag

    @property
    def custom_data_info(self) -> CustomDataInfo:
        """Returns custom data info for mapping device"""
        return self.__custom_data_info

    @property
    def holdout(self) -> Optional[Experiment]:
        """Returns holdout"""
        return self.__holdout

    def has_experiment_js_css_variable(self, experiment_id: int) -> bool:
        """Returns `True` if the experiment has a JS or CSS variable, otherwise returns `False`"""
        return experiment_id in self.__experiment_ids_with_js_css_variable

    def __collect_indices(self) -> None:
        for _, feature_flag in self.__feature_flags.items():
            self.__feature_flag_by_id[feature_flag.id_] = feature_flag
            if feature_flag.rules is not None:
                has_feature_flag_variable_js_css = self.__has_feature_flag_variable_js_css(feature_flag)
                for rule in feature_flag.rules:
                    self.__rule_info_by_exp_id[rule.experiment.id_] = DataFile.RuleInfo(feature_flag, rule)
                    if has_feature_flag_variable_js_css:
                        self.__experiment_ids_with_js_css_variable.add(rule.experiment.id_)
                    for variation in rule.experiment.variations_by_exposition:
                        if variation.variation_id is not None:
                            self.__variation_by_id[variation.variation_id] = variation

    @staticmethod
    def __make_me_groups(feature_flags: Iterable[FeatureFlag]) -> Dict[str, MEGroup]:
        me_group_lists: Dict[str, List[FeatureFlag]] = {}
        for feature_flag in feature_flags:
            if feature_flag.me_group_name:
                me_group_list = me_group_lists.get(feature_flag.me_group_name)
                if me_group_list:
                    me_group_list.append(feature_flag)
                else:
                    me_group_lists[feature_flag.me_group_name] = [feature_flag]
        return {me_group_name: MEGroup(me_group_list) for me_group_name, me_group_list in me_group_lists.items()}

    @staticmethod
    def __has_feature_flag_variable_js_css(feature_flag: FeatureFlag) -> bool:
        variations = feature_flag.variations
        first_variation = next(iter(variations), None)
        if first_variation:
            for variable in first_variation.variables:
                if variable.get_type() in {Variable.Type.CSS.value, Variable.Type.JS.value}:
                    return True
        return False

    def __str__(self):
        return (
            "DataFile{"
            f"environment:'{self.__environment}',"
            f"last_modified:'{self.__last_modified}',"
            f"feature_flags:{len(self.__feature_flags)},"
            f"settings:{self.__settings}"
            "}"
        )

    class RuleInfo:
        """Aggregates some information related to a specific rule"""

        def __init__(self, feature_flag: FeatureFlag, rule: Rule) -> None:
            self.__feature_flag = feature_flag
            self.__rule = rule

        @property
        def feature_flag(self) -> FeatureFlag:
            """Returns the feature flag"""
            return self.__feature_flag

        @property
        def rule(self) -> Rule:
            """Returns the rule"""
            return self.__rule
