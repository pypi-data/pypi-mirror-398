"""Services"""
from typing import Optional

from kameleoon.logging.kameleoon_logger import KameleoonLogger
from kameleoon.network.services.service_impl import ServiceImpl
from kameleoon.network.services.configuration_service import ConfigurationService, FetchedConfiguration
from kameleoon.network.net_provider import ResponseContentType, Request, HttpMethod
from kameleoon.sdk_version import SdkVersion


class ConfigurationServiceImpl(ConfigurationService, ServiceImpl):
    """Configuration service implementation"""
    _SDK_TYPE_HEADER = "X-Kameleoon-SDK-Type"
    _SDK_VERSION_HEADER = "X-Kameleoon-SDK-Version"
    _HEADER_IF_MODIFIED_SINCE = "If-Modified-Since"
    _HEADER_LAST_MODIFIED = "Last-Modified"

    def __init__(self, network_manager) -> None:
        KameleoonLogger.debug("CALL: ConfigurationServiceImpl(network_manager)")
        ConfigurationService.__init__(self)
        ServiceImpl.__init__(self, network_manager)
        KameleoonLogger.debug("RETURN: ConfigurationServiceImpl(network_manager)")

    async def fetch_configuration(
        self, environment: Optional[str] = None, time_stamp: Optional[int] = None,
        if_modified_since: Optional[str] = None, timeout: Optional[float] = None
    ) -> Optional[FetchedConfiguration]:
        KameleoonLogger.debug(
            "CALL: ConfigurationServiceImpl.fetch_configuration("
            "environment: %s, time_stamp: %s, if_modified_since: %s, timeout: %s)",
            environment, time_stamp, if_modified_since, timeout
        )
        if timeout is None:
            timeout = self.network_manager.call_timeout
        url: str = self.network_manager.url_provider.make_configuration_url(environment, time_stamp)
        headers = {
            self._SDK_TYPE_HEADER: SdkVersion.NAME,
            self._SDK_VERSION_HEADER: SdkVersion.VERSION,
        }
        if if_modified_since:
            headers[self._HEADER_IF_MODIFIED_SINCE] = if_modified_since
        request = Request(
            HttpMethod.GET, url, timeout, headers=headers,
            response_content_type=ResponseContentType.JSON,
        )
        response = await self._make_call(request, False, self.NUMBER_OF_RECONNECTION_ON_FAILURE_CRITICAL)
        fetched_configuration = None
        if response.success:
            fetched_configuration = (
                FetchedConfiguration(None, None)
                if response.code == 304 else
                FetchedConfiguration(response.content, response.headers.get(self._HEADER_LAST_MODIFIED))
            )
        KameleoonLogger.debug(
            "RETURN: ConfigurationServiceImpl.fetch_configuration("
            "environment: %s, time_stamp: %s, timeout: %s) -> (response_coroutine)",
            environment, time_stamp, if_modified_since, timeout
        )
        return fetched_configuration
