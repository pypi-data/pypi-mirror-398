"""Services"""
from typing import Any, Dict, Optional
from kameleoon.network.services.service import Service


class FetchedConfiguration:
    """Represents fetched configuration in json format and its last modification date"""

    def __init__(self, configuration: Optional[Dict[str, Any]], last_modified: Optional[str]) -> None:
        self.configuration = configuration
        self.last_modified = last_modified

    def __str__(self) -> str:
        return f"FetchedConfiguration{{configuration:{self.configuration},last_modified:'{self.last_modified}'}}"


class ConfigurationService(Service):
    """Abstract configuration service"""
    async def fetch_configuration(
        self, environment: Optional[str] = None, time_stamp: Optional[int] = None,
        if_modified_since: Optional[str] = None, timeout: Optional[float] = None
    ) -> Optional[FetchedConfiguration]:
        """Asynchronously fetches configuration data from a remote service."""
        raise NotImplementedError()
