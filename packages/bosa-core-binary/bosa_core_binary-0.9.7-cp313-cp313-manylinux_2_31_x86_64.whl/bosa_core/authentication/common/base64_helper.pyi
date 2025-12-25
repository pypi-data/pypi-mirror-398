from typing import Any

def encode_base64(to_encode: Any) -> str:
    """Encode base64.

    This function will trim the '=' padding.

    Args:
        to_encode (Any): The to encode

    Returns:
        str: The encoded base64
    """
def decode_base64(to_decode: str) -> str:
    """Decode base64.

    Note that the string will be padded with '=' to make it a multiple of 4.

    Args:
        to_decode (str): The to decode

    Returns:
        str: The decoded base64
    """
