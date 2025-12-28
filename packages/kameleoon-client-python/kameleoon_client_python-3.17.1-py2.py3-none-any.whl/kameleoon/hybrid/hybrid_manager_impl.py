"""Hybrid"""
import time
from typing import Dict, Optional
from kameleoon.data.manager.assigned_variation import AssignedVariation
from kameleoon.helpers.string_utils import StringUtils
from kameleoon.hybrid.hybrid_manager import HybridManager
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.managers.data.data_manager import DataManager


class HybridManagerImpl(HybridManager):
    """Implementation of HybridManager that generates tracking code for engine integration."""
    TC_INIT = "window.kameleoonQueue=window.kameleoonQueue||[];"
    TC_ASSIGN_VARIATION_F = "window.kameleoonQueue.push(['Experiments.assignVariation',{0},{1},true]);"
    TC_TRIGGER_F = "window.kameleoonQueue.push(['Experiments.trigger',{0},{2}]);"
    TC_ASSIGN_VARIATION_TRIGGER_F = TC_ASSIGN_VARIATION_F + TC_TRIGGER_F

    def __init__(self, expiration_period: float, data_manager: DataManager) -> None:
        KameleoonLogger.debug("CALL: HybridManagerImpl(expiration_period: %s)", expiration_period)
        super().__init__()
        self._expiration_period = expiration_period
        self._data_manager = data_manager
        KameleoonLogger.debug("RETURN: HybridManagerImpl(expiration_period: %s)", expiration_period)

    def get_engine_tracking_code(self, visitor_variations: Optional[Dict[int, AssignedVariation]]) -> str:
        KameleoonLogger.debug("CALL: HybridManagerImpl.get_engine_tracking_code(visitor_variations: %s)",
                              visitor_variations)
        lines = [self.TC_INIT]
        if visitor_variations:
            expiration_time = time.time() - self._expiration_period
            for variation in visitor_variations.values():
                if variation.assignment_time > expiration_time:
                    tracking_only = not (self._data_manager.data_file.
                                         has_experiment_js_css_variable(variation.experiment_id))
                    line = self.TC_ASSIGN_VARIATION_TRIGGER_F.format(
                        variation.experiment_id, variation.variation_id,
                        StringUtils.bool_to_string_lower_case(tracking_only))
                    lines.append(line)
        tracking_code = "".join(lines)
        KameleoonLogger.debug(
            "RETURN: HybridManagerImpl.get_engine_tracking_code(visitor_variations: %s) -> (tracking_code: %s)",
            visitor_variations, tracking_code)
        return tracking_code
