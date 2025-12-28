"""Legal Consent"""

from enum import Enum


class LegalConsent(Enum):
    """Possible Legal Consent states"""

    UNKNOWN = 0
    GIVEN = 1
    NOT_GIVEN = 2
