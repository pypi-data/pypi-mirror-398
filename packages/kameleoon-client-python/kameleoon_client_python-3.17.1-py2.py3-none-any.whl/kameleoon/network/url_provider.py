"""Network"""

from typing import Any, Optional
from kameleoon.sdk_version import SdkVersion
from kameleoon.network.query_builder import QueryBuilder, QueryParam, QueryParams
from kameleoon.types.remote_visitor_data_filter import RemoteVisitorDataFilter


class UrlProvider:
    """URL provider"""

    _TRACKING_PATH = "/visit/events"
    _VISITOR_DATA_PATH = "/visit/visitor"
    _EXPERIMENTS_CONFIGURATIONS_PATH = "/visit/experimentsConfigurations"
    _GET_DATA_PATH = "/map/map"
    _POST_DATA_PATH = "/map/maps"
    _CONFIGURATION_API_URL_FORMAT = "https://{0}/v3/{1}"
    _RT_CONFIGURATION_URL_FORMAT = "https://{0}:8110/sse?{1}"
    _ACCESS_TOKEN_URL_FORMAT = "https://{0}/oauth/token"
    _DATA_API_URL_FORMAT = "https://{0}{1}?{2}"

    TEST_DATA_API_DOMAIN = "data.kameleoon.net"
    TEST_AUTOMATION_API_DOMAIN = "api.kameleoon.net"
    DEFAULT_DATA_API_DOMAIN = "data.kameleoon.io"
    DEFAULT_EVENTS_DOMAIN = "events.kameleoon.eu"
    DEFAULT_CONFIGURATION_DOMAIN = "sdk-config.kameleoon.eu"
    DEFAULT_ACCESS_TOKEN_DOMAIN = "api.kameleoon.com"

    def __init__(
        self,
        site_code: str,
        network_domain: Optional[str] = None,
    ) -> None:
        self.site_code = site_code
        self._data_api_domain = self.DEFAULT_DATA_API_DOMAIN  # if remove W0201 error (pylint)
        self.__setup_domains(network_domain)
        self.__post_query_base = self.__make_post_query_base()

    def __make_post_query_base(self) -> str:
        # fmt: off
        query_builder = QueryBuilder(
            QueryParam(QueryParams.SDK_NAME, SdkVersion.NAME),
            QueryParam(QueryParams.SDK_VERSION, SdkVersion.VERSION),
            QueryParam(QueryParams.SITE_CODE, self.site_code),
            QueryParam(QueryParams.BODY_UA, "true"),
        )
        # fmt: on
        return str(query_builder)

    def __setup_domains(self, network_domain: Optional[str]) -> None:
        """Updates the domains based on the provided network domain."""
        if not network_domain:
            self._data_api_domain = self.DEFAULT_DATA_API_DOMAIN
            self._events_domain = self.DEFAULT_EVENTS_DOMAIN
            self._configuration_domain = self.DEFAULT_CONFIGURATION_DOMAIN
            self._access_token_domain = self.DEFAULT_ACCESS_TOKEN_DOMAIN
            self.__is_custom_domain = False
        else:
            self._events_domain = f"events.{network_domain}"
            self._configuration_domain = f"sdk-config.{network_domain}"
            self._data_api_domain = f"data.{network_domain}"
            self._access_token_domain = f"api.{network_domain}"
            self.__is_custom_domain = True

    def apply_data_api_domain(self, data_api_domain: Any) -> None:
        """Sets the domain for the data API."""
        if data_api_domain:
            if self.__is_custom_domain:
                sub_domain = data_api_domain.split(".")[0]
                self._data_api_domain = self._data_api_domain.replace(self._data_api_domain.split(".")[0], sub_domain)
            else:
                self._data_api_domain = data_api_domain

    def make_tracking_url(self) -> str:
        """Constructs the URL for tracking events."""
        return self._DATA_API_URL_FORMAT.format(self._data_api_domain, self._TRACKING_PATH, self.__post_query_base)

    def make_visitor_data_get_url(
        self, visitor_code: str, data_filter: RemoteVisitorDataFilter, is_unique_identifier: bool = False
    ) -> str:
        """Constructs the URL for fetching visitor data with specified filters."""
        # fmt: off
        query_builder = QueryBuilder(
            QueryParam(QueryParams.SITE_CODE, self.site_code, encoding_required=False),
            QueryParam(QueryParams.MAPPING_VALUE if is_unique_identifier else QueryParams.VISITOR_CODE, visitor_code),
            QueryParam(QueryParams.MAX_NUMBER_PREVIOUS_VISITS, str(data_filter.previous_visit_amount)),
            QueryParam(QueryParams.VERSION, "0", encoding_required=False),
            QueryParam(QueryParams.STATIC_DATA, "true", encoding_required=False),
        )
        # fmt: on
        self.__add_flag_param_if_required(query_builder, QueryParams.KCS, data_filter.kcs)
        self.__add_flag_param_if_required(query_builder, QueryParams.CURRENT_VISIT, data_filter.current_visit)
        self.__add_flag_param_if_required(query_builder, QueryParams.CUSTOM_DATA, data_filter.custom_data)
        self.__add_flag_param_if_required(query_builder, QueryParams.CONVERSION, data_filter.conversions)
        self.__add_flag_param_if_required(query_builder, QueryParams.GEOLOCATION, data_filter.geolocation)
        self.__add_flag_param_if_required(query_builder, QueryParams.EXPERIMENT, data_filter.experiments)
        self.__add_flag_param_if_required(query_builder, QueryParams.PAGE, data_filter.page_views)
        self.__add_flag_param_if_required(query_builder, QueryParams.PERSONALIZATION, data_filter.personalization)
        self.__add_flag_param_if_required(query_builder, QueryParams.CBS, data_filter.cbs)
        return self._DATA_API_URL_FORMAT.format(self._data_api_domain, self._VISITOR_DATA_PATH, str(query_builder))

    @staticmethod
    def __add_flag_param_if_required(query_builder: QueryBuilder, param_name: QueryParams, state: bool) -> None:
        if state:
            query_builder.append(QueryParam(param_name, "true"))

    def make_api_data_get_request_url(self, key: str) -> str:
        """Constructs the URL for fetching remote data from the Data API."""
        # fmt: off
        query_builder = QueryBuilder(
            QueryParam(QueryParams.SITE_CODE, self.site_code),
            QueryParam(QueryParams.KEY, key),
        )
        # fmt: on
        return self._DATA_API_URL_FORMAT.format(self._data_api_domain, self._GET_DATA_PATH, str(query_builder))

    def make_configuration_url(self, environment: Optional[str] = None, time_stamp: Optional[int] = None) -> str:
        """Constructs the URL for fetching configuration data with optional query parameters."""
        query_builder = QueryBuilder()
        if environment:
            query_builder.append(QueryParam(QueryParams.ENVIRONMENT, environment))
        if time_stamp is not None:
            query_builder.append(QueryParam(QueryParams.TS, str(time_stamp)))
        url = self._CONFIGURATION_API_URL_FORMAT.format(self._configuration_domain, self.site_code)
        query = str(query_builder)
        if len(query) > 0:
            url = f"{url}?{query}"
        return url

    def make_real_time_url(self) -> str:
        """Constructs the URL for real-time configuration data."""
        query_builder = QueryParam(QueryParams.SITE_CODE, self.site_code)
        return self._RT_CONFIGURATION_URL_FORMAT.format(self._events_domain, query_builder)

    def make_access_token_url(self) -> str:
        """Constructs the URL for fetching access tokens."""
        return self._ACCESS_TOKEN_URL_FORMAT.format(self._access_token_domain)
