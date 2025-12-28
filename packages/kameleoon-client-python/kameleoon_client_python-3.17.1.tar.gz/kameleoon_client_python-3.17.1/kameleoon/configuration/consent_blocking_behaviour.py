"""Kameleoon Configuration"""

from enum import Enum
from kameleoon.helpers.functions import enum_from_literal


class ConsentBlockingBehaviour(Enum):
    """Possible Consent Blocking Behaviour types"""

    PARTIALLY_BLOCKED = "PARTIALLY_BLOCK"
    COMPLETELY_BLOCKED = "FULLY_BLOCK"

    @staticmethod
    def from_str(s: str) -> "ConsentBlockingBehaviour":
        """Makes ConsentBlockingBehaviour from string"""
        return enum_from_literal(s, ConsentBlockingBehaviour, ConsentBlockingBehaviour.PARTIALLY_BLOCKED)
