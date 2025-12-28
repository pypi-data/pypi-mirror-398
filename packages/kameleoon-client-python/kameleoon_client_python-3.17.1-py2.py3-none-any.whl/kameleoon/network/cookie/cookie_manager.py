"""Cookie"""

import datetime
import json
from http.cookies import SimpleCookie, Morsel
from typing import Dict, List, Optional, Union
from kameleoon.configuration.data_file import DataFile
from kameleoon.data.manager.forced_feature_variation import ForcedFeatureVariation
from kameleoon.data.manager.visitor_manager import VisitorManager
from kameleoon.helpers.visitor_code import generate_visitor_code, validate_visitor_code
from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.managers.data.data_manager import DataManager
from kameleoon.network.uri_helper import decode_uri


VISITOR_CODE_COOKIE = "kameleoonVisitorCode"
KAMELEOON_SIMULATION_FF_DATA = "kameleoonSimulationFFData"
EXPERIMENT_ID_KEY = "expId"
VARIATION_ID_KEY = "varId"
COOKIE_TTL = datetime.timedelta(days=380)
MAX_AGE = str(int(COOKIE_TTL.total_seconds()))


class CookieManager:
    """Cookie manager"""

    _ENCODER: SimpleCookie[str] = SimpleCookie()

    def __init__(self, data_manager: DataManager, visitor_manager: VisitorManager, top_level_domain: str) -> None:
        KameleoonLogger.debug(
            "CALL: CookieManager(data_manager, visitor_manager, top_level_domain: %s)", top_level_domain
        )
        self._data_manager = data_manager
        self._visitor_manager = visitor_manager
        self._top_level_domain = top_level_domain
        KameleoonLogger.debug(
            "RETURN: CookieManager(data_manager, visitor_manager, top_level_domain: %s)", top_level_domain
        )

    # fmt is disabled due issue in pylint, disabling R0801 doesn’t work
    # fmt: off
    def get_or_add(
        self, cookies_readonly: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, Morsel[str]]] = None,
        default_visitor_code: Optional[str] = None,
    ) -> str:
        # fmt: on
        """
        Retrieves and returns a visitor code from the provided cookies if it exists. In other case uses
        the `default_visitor_code` as a new visitor code if provided, otherwise generates a new visitor code.
        Then the new visitor code is added to the cookies unless the cookies are passed as `cookies_readonly`
        and not as `cookies`. Then returns the new visitor code.
        """
        KameleoonLogger.debug(
            "CALL: CookieManager.get_or_add(cookies_readonly: %s, cookies: %s, default_visitor_code: %s)",
            cookies_readonly, cookies, default_visitor_code)
        visitor_code = self._get_or_add_visitor_code(cookies_readonly, cookies, default_visitor_code)
        self._process_simulated_variations(cookies_readonly, cookies, visitor_code)
        KameleoonLogger.debug(
            "RETURN: CookieManager.get_or_add(cookies_readonly: %s, cookies: %s, default_visitor_code: %s)"
            " -> (visitor_code: %s)", cookies_readonly, cookies, default_visitor_code, visitor_code)
        return visitor_code

    def _get_or_add_visitor_code(
        self, cookies_readonly: Optional[Dict[str, str]],
        cookies: Optional[Dict[str, Morsel[str]]],
        default_visitor_code: Optional[str],
    ) -> str:
        visitor_code = self._get_value_from_cookies(cookies_readonly or cookies or {}, VISITOR_CODE_COOKIE)
        if visitor_code is not None:
            validate_visitor_code(visitor_code)
            KameleoonLogger.debug("Read visitor code %s from cookies %s", visitor_code, cookies)
            return visitor_code
        if default_visitor_code is None:
            visitor_code = generate_visitor_code()
            KameleoonLogger.debug("Generated new visitor code %s", visitor_code)
            if not self._data_manager.is_visitor_code_managed and (cookies is not None):
                self._add(visitor_code, cookies)
            return visitor_code
        validate_visitor_code(default_visitor_code)
        visitor_code = default_visitor_code
        KameleoonLogger.debug("Used default visitor code '%s'", default_visitor_code)
        if not self._data_manager.is_visitor_code_managed and (cookies is not None):
            self._add(visitor_code, cookies)
        return visitor_code

    def update(self, visitor_code: str, consent: bool, cookies: Dict[str, Morsel[str]]) -> None:
        """Updates cookies based on the visitor's consent."""
        KameleoonLogger.debug("CALL: CookieManager.update(visitor_code: %s, consent: %s, cookies: %s)",
                              visitor_code, consent, cookies)
        if consent:
            self._add(visitor_code, cookies)
        KameleoonLogger.debug("RETURN: CookieManager.update(visitor_code: %s, consent: %s, cookies: %s)",
                              visitor_code, consent, cookies)

    def _add(self, visitor_code: str, cookies: Dict[str, Morsel[str]]) -> None:
        KameleoonLogger.debug("CALL: CookieManager._add(visitor_code: %s, cookies: %s)", visitor_code, cookies)
        morsel: Morsel[str] = Morsel()
        morsel.set(VISITOR_CODE_COOKIE, *self._ENCODER.value_encode(visitor_code))
        morsel["domain"] = self._top_level_domain
        morsel["path"] = "/"
        expires = datetime.datetime.now(datetime.timezone.utc) + COOKIE_TTL
        morsel["expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        morsel["max-age"] = MAX_AGE
        cookies[VISITOR_CODE_COOKIE] = morsel
        KameleoonLogger.debug("RETURN: CookieManager._add(visitor_code: %s, cookies: %s)", visitor_code, cookies)

    def _process_simulated_variations(
        self, cookies_readonly: Optional[Dict[str, str]], cookies: Optional[Dict[str, Morsel[str]]], visitor_code: str
    ) -> None:
        raw = self._get_value_from_cookies(cookies_readonly or cookies or {}, KAMELEOON_SIMULATION_FF_DATA)
        if not raw:
            return
        raw = decode_uri(raw)
        try:
            variations = self._parse_simulated_variations(raw)
            visitor = self._visitor_manager.get_or_create_visitor(visitor_code)
            visitor.update_simulated_variations(variations)
        except Exception as ex:  # pylint: disable=W0703
            KameleoonLogger.error("Failed to process simulated variations cookie: %s", ex)

    def _parse_simulated_variations(self, raw: str) -> List[ForcedFeatureVariation]:
        variations: List[ForcedFeatureVariation] = []
        data_file = self._data_manager.data_file
        jobj = json.loads(raw)
        if not isinstance(jobj, dict):
            self._log_malformed_simulated_variations_cookie(raw, "object expected")
            return variations
        for feature_key, value in jobj.items():
            if not isinstance(feature_key, str):
                self._log_malformed_simulated_variations_cookie(raw, "key must be string")
                continue
            if not isinstance(value, dict):
                self._log_malformed_simulated_variations_cookie(raw, "value must be object")
                continue
            experiment_id = value.get(EXPERIMENT_ID_KEY)
            if not isinstance(experiment_id, int) or (experiment_id < 0):
                self._log_malformed_simulated_variations_cookie(raw, "'expId' must be non-negative integer")
                continue
            if experiment_id != 0:
                variation_id = value.get(VARIATION_ID_KEY)
                if not isinstance(variation_id, int) or (variation_id < 0):
                    self._log_malformed_simulated_variations_cookie(raw, "'varId' must be non-negative integer")
                    continue
            else:
                variation_id = 0
            simulated_variation = self._simulated_variation_from_data_file(
                data_file, feature_key, experiment_id, variation_id
            )
            if simulated_variation:
                variations.append(simulated_variation)
        return variations

    @staticmethod
    def _log_malformed_simulated_variations_cookie(raw: str, info: str) -> None:
        KameleoonLogger.error("Malformed simulated variations cookie %s: %s", raw, info)

    @staticmethod
    def _simulated_variation_from_data_file(
        data_file: DataFile, feature_key: str, experiment_id: int, variation_id: int
    ) -> Optional[ForcedFeatureVariation]:
        feature_flag = data_file.feature_flags.get(feature_key)
        if feature_flag is None:
            KameleoonLogger.error("Simulated feature flag %s is not found", feature_key)
            return None
        if experiment_id == 0:
            return ForcedFeatureVariation(feature_key, None, None, True)
        rule = next(filter(lambda r: r.experiment.id_ == experiment_id, feature_flag.rules), None)
        if rule is None:
            KameleoonLogger.error("Simulated experiment %s is not found", experiment_id)
            return None
        var_by_exp = next(
            filter(lambda v: v.variation_id == variation_id, rule.experiment.variations_by_exposition), None
        )
        if var_by_exp is None:
            KameleoonLogger.error("Simulated variation %s is not found", variation_id)
            return None
        return ForcedFeatureVariation(feature_key, rule, var_by_exp, True)

    @staticmethod
    def _get_value_from_cookies(cookies: Union[Dict[str, str], Dict[str, Morsel[str]]], key: str) -> Optional[str]:
        value = None
        value_cookie = cookies.get(key)
        if value_cookie:
            # SimpleCookie or request.COOKIES could be passed to the method, we should determine what exactly
            value = value_cookie if isinstance(value_cookie, str) else value_cookie.value
            if not value:
                value = None
        return value
