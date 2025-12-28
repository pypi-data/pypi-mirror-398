"""Evaluated Experiment"""

from typing import Optional
from kameleoon.configuration.experiment import Experiment
from kameleoon.configuration.rule import Rule
from kameleoon.configuration.rule_type import RuleType
from kameleoon.configuration.variation_by_exposition import VariationByExposition
from kameleoon.data.manager.forced_variation import ForcedVariation
from kameleoon.data.manager.forced_experiment_variation import ForcedExperimentVariation


class EvaluatedExperiment:
    """Represents an evaluated experiment"""

    def __init__(self, var_by_exp: VariationByExposition, experiment: Experiment, rule_type: RuleType) -> None:
        self.__var_by_exp = var_by_exp
        self.__experiment = experiment
        self.__rule_type = rule_type

    @staticmethod
    def from_var_by_exp_rule(var_by_exp: VariationByExposition, rule: Rule) -> "EvaluatedExperiment":
        """Make an `EvaluatedExperiment` instance from a variation by exposition and a rule"""
        return EvaluatedExperiment(var_by_exp, rule.experiment, rule.type)

    @staticmethod
    def from_forced_variation(forced_variation: ForcedVariation) -> Optional["EvaluatedExperiment"]:
        """Make an `EvaluatedExperiment` instance from a forced variation"""
        if forced_variation.var_by_exp and forced_variation.rule:
            return EvaluatedExperiment.from_var_by_exp_rule(forced_variation.var_by_exp, forced_variation.rule)
        return None

    @staticmethod
    def from_forced_experiment_variation(forced_variation: ForcedExperimentVariation) -> "EvaluatedExperiment":
        """Make an `EvaluatedExperiment` instance from a forced experiment variation"""
        return EvaluatedExperiment.from_var_by_exp_rule(forced_variation.var_by_exp, forced_variation.rule)

    @property
    def var_by_exp(self) -> VariationByExposition:
        """Returns the variation by exposition"""
        return self.__var_by_exp

    @property
    def experiment(self) -> Experiment:
        """Returns the experiment"""
        return self.__experiment

    @property
    def rule_type(self) -> RuleType:
        """Returns the rule type"""
        return self.__rule_type
