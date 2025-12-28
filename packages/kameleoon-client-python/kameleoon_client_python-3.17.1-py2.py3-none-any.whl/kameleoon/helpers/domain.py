"""Helper for domain"""
import re
from typing import Optional

from kameleoon.logging.kameleoon_logger import KameleoonLogger

HTTP = "http://"
HTTPS = "https://"
REGEX_DOMAIN = (
    r"^(\.?(([a-zA-Z\d][a-zA-Z\d-]*[a-zA-Z\d])|[a-zA-Z\d]))"
    r"(\.(([a-zA-Z\d][a-zA-Z\d-]*[a-zA-Z\d])|[a-zA-Z\d])){1,126}$"
)
LOCALHOST = "localhost"


def validate_top_level_domain(top_level_domain: str) -> str:
    """
    Validate the given top-level domain.

    Args:
        top_level_domain (str): The top-level domain to validate.

    Returns:
        str: The validated top-level domain.
    """
    if top_level_domain == "":
        return top_level_domain

    top_level_domain = check_and_trim_protocol(top_level_domain.lower())

    if not re.match(REGEX_DOMAIN, top_level_domain) and top_level_domain != LOCALHOST:
        KameleoonLogger.error(
            f"The top-level domain '{top_level_domain}' is invalid. The value has been set as provided, but it does "
            f"not meet the required format for proper SDK functionality. Please check the domain for correctness.")
        return top_level_domain

    return top_level_domain


def validate_network_domain(network_domain: Optional[str]) -> Optional[str]:
    """
    Validate the given network domain.

    Args:
        network_domain: The network domain to validate.

    Returns:
        str or None: The validated network domain, or None if invalid.
    """
    if not network_domain:
        return None

    network_domain = check_and_trim_protocol(network_domain.lower())

    # Replace first and last dot
    network_domain = re.sub(r"^\.+|\.+$", "", network_domain)

    if not re.match(REGEX_DOMAIN, network_domain) and network_domain != LOCALHOST:
        KameleoonLogger.error(f"The network domain '{network_domain}' is invalid.")
        return None

    return network_domain


def check_and_trim_protocol(domain: str) -> str:
    """
    Check if the domain contains a protocol and trim it if it does.

    Args:
        domain: The domain to check and trim.

    Returns:
        str: The domain after trimming the protocol.
    """
    protocols = [HTTP, HTTPS]
    for protocol in protocols:
        if domain.startswith(protocol):
            domain = domain[len(protocol):]
            KameleoonLogger.warning(
                f"The domain contains '{protocol}'. Domain after protocol trimming: '{domain}'"
            )
            return domain
    return domain
