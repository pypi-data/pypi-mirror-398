"""Network"""
from urllib.parse import quote, unquote


def encode_uri(to_encode: str) -> str:
    """Encodes a given string to be safely included in a URI."""
    return quote(to_encode, safe="~()*!.'")


def decode_uri(to_decode: str) -> str:
    """Decodes a given string from URI."""
    return unquote(to_decode)
