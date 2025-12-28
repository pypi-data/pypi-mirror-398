import base64
import re
from urllib.parse import unquote


# Function to check if the string is base64-encoded
def is_base64_encoded(string: str) -> bool:
    base64_regex: str = r"^[A-Za-z0-9+/=]*$"
    return len(string) % 4 == 0 and re.match(base64_regex, string) is not None


# Function to decode base64-encoded strings
def decode_base64_string(encoded_string: str) -> str:
    if not encoded_string or not is_base64_encoded(encoded_string):
        return encoded_string

    try:
        decoded_bytes: bytes = base64.b64decode(encoded_string)
        decoded_str: str = decoded_bytes.decode("utf-8")
        return decode_if_korean(decoded_str)
    except Exception as e:
        return f"Error decoding base64: {e!s}"


# Decode if the result contains Korean characters
def decode_if_korean(encoded_str: str) -> str:
    try:
        decoded: str = unquote(encoded_str)
        if re.search(r"[\uac00-\ud7a3]", decoded):  # Korean Hangul Unicode range
            return decoded
        return encoded_str
    except Exception:
        return encoded_str

# Helper function to get header with fallback options
def get_header_with_fallback(headers: dict, header_options: list[str]) -> str:
    for header_name in header_options:
        value = headers.get(header_name)
        if value:
            return value
    return None
